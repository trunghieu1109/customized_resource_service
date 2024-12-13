from vastai import VastAI
import sys
import os
import logging_config
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sdk_service
import api_service
from constants import GPU_USAGE_THRESHOLD, CPU_USAGE_THRESHOLD, FULL_DISK_USAGE_THRESHOLD, IDLE_DISK_USAGE_THRESHOLD 
from config import API_KEY, REDIS_HOST, REDIS_PORT, POOL_SIZE
from pydantic import BaseModel
import mail_service

def check_scheduler_state(scheduler):
    state = scheduler.state
    if state == 0:  # STATE_STOPPED
        print("Scheduler has not started.")
    elif state == 1:  # STATE_RUNNING
        print("Scheduler is running.")
    elif state == 2:  # STATE_PAUSED
        print("Scheduler is paused.")

jobstores = {
    'default': RedisJobStore(host=REDIS_HOST, port=REDIS_PORT, db=0)
}

executors = {
    'default': ThreadPoolExecutor(POOL_SIZE)
}

scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors)
scheduler.start()

check_scheduler_state(scheduler)

hash_name = "apscheduler.jobs"

logger = logging_config.get_logger()

class TrackingJob(BaseModel):
    instance_id: int | str
    test_script: str
    backup_script: str
    option: str
    client_email: str

vast_sdk = VastAI(api_key=API_KEY)

def check_instance_status(instance_id: str, test_script: str = ""):
    
    logger.info(f"Checking instance {instance_id}'s status")
    
    instance = api_service.get_instance(instance_id)

    if instance:
        gpu_util = instance['gpu_util']
        cpu_util = instance['cpu_util']
        disk_util = instance['disk_util']
        disk_space = instance['disk_space']
        
        if disk_util / disk_space * 100 > FULL_DISK_USAGE_THRESHOLD:
            return {
                "status": "error",
                "message": f"No space left in instance {instance_id}."
            }
        
        if gpu_util > GPU_USAGE_THRESHOLD or cpu_util > CPU_USAGE_THRESHOLD:
            return {
                "status": "in process",
                "message": f"Instance {instance_id} is in process, gpu and cpu are used."
            }
        else:
            if disk_util / disk_space * 100 < IDLE_DISK_USAGE_THRESHOLD:
                return {
                    "status": "ready",
                    "message": f"Instance {instance_id} is ready."
                }
            else:
                
                if test_script != "":
                    # TODO: Not tested yet
                    result = vast_sdk.execute(id=instance_id, command=test_script)
                    
                    if result == "True":
                        return {
                            "status": "finished",
                            "message": f"Process in instance {instance_id} was finished."
                        }
                    else:
                        return {
                            "status": "ready",
                            "message": f"Instance {instance_id} is ready."
                        }   
                else:
                    return {
                        "status": "finished",
                        "message": f"Process in instance {instance_id} was finished."
                    }       
    else:      
        return {
            "status": "not existed",
            "message": f"Can't found instance matching id: {instance_id}. Please check instance_id."
        }

def tracking_job(job: TrackingJob):
    
    logger.info(f"Executing tracking job of instance {job.instance_id}.")
    
    instance_status = check_instance_status(job.instance_id, job.test_script)
    
    logger.info(instance_status)
    
    if instance_status['status'] == 'finished':
        
        instance = api_service.get_instance(job.instance_id)
        
        if instance:
            
            msg = None
            
            # TODO: Not tested yet
            if job.backup_script != "":
                logger.info(f"Backing up data from instance ${job.instance_id}.")
                
                vast_sdk.execute(id=job.instance_id, command=job.backup_script)
            
            if job.option == "stop":
                logger.info(f"Stopping instance ${job.instance_id}.")
                
                vast_sdk.stop_instance(id=job.instance_id)
                job_id = "job_" + str(job.instance_id)
        
                scheduler.remove_job(job_id=job_id)
            
            elif job.option in ["destroy", "delete"]:
                logger.info(f"Destroying instance ${job.instance_id}.")
                
                vast_sdk.destroy_instance(id=job.instance_id)
                job_id = "job_" + str(job.instance_id)
        
                scheduler.remove_job(job_id=job_id)
                
            else:
                logger.info(f"Sending notification to {job.client_email} about instance ${job.instance_id}.")
                
                subject = mail_service.compose_subject_finished_instance(job.instance_id)
                body = mail_service.compose_body_finished_instance(job.client_email, instance)
                
                msg = mail_service.send_email(job.client_email, subject, body)
                    
    elif instance_status['status'] == 'error':
        instance = api_service.get_instance(job.instance_id)
        
        if instance:
            logger.info(f"Sending warning to {job.client_email} about instance ${job.instance_id}.")
        
            subject = mail_service.compose_subject_error_instance(job.instance_id)
            body = mail_service.compose_body_error_instance(job.client_email, instance, instance_status['message'])
            
            msg = mail_service.send_email(job.client_email, subject, body)
        
    return {
        "instance_status": instance_status['status'],
        "message": f"Tracking instance {job.instance_id} successfully! Log: {instance_status['message']}."
    }

async def create_tracking_job(instance_id: str, time_interval: int = "300", test_script: str = "", 
                              backup_script: str = "", option: str = "", client_email: str = ""):
    
    logger.info(f"Creating new tracking job for instance {instance_id}.")
    
    instance = api_service.get_instance(instance_id)
    
    if instance and instance['cur_state'] == 'running':  
        job_id = "job_" + str(instance_id)
        
        if scheduler.get_job(job_id):
            
            logger.error(f"Instance {instance_id} has been tracked. Please check instance_id")
            
            return {
                "status": "error",
                "message": f"Tracking job for instance {instance_id} was existed! Please check instance_id."
            }
        
        job = TrackingJob(
            instance_id = instance_id, 
            test_script = test_script, 
            backup_script = backup_script, 
            option = option,
            client_email = client_email
        )
        
        job = scheduler.add_job(tracking_job, "interval", seconds = time_interval, args = [job], id = job_id)
        
        if job:
            return {
                "status": "success",
                "message": f"Create tracking job for instance {instance_id} successfully!"
            }
        
        else:
            
            logger.error(f"Error while creating tracking job for instance {instance_id}")
            
            return {
                "status": "error",
                "message": f"Error while creating tracking job for instance {instance_id}! Please check tracking job configuration."
            }    
        
    else:
        logger.error(f"Instance {instance_id} is not exist or not ready. Please check instance_id")
        
        return {
            "status": "error",
            "message": f"Instance {instance_id} is not existed or not ready! Please check instance_id."
        }
        
def remove_tracking_job(instance_id: str):
    
    instance = api_service.get_instance(instance_id)
    
    if instance and instance['cur_state'] == "running":
        job_id = "job_" + str(instance_id)
        
        job = scheduler.get_job(job_id)
        
        if job:
            logger.info(f"Removing tracking job of instance {instance_id}.")
            
            scheduler.remove_job(job_id=job_id)
            return {
                "status": "success",
                "messasge": f"Remove tracking job of instance {instance_id} successfully!"
            }
        else:
            logger.error(f"Tracking job for instance {instance_id} is not existed! Please check instance_id?")
            
            return {
                "status": "error",
                "message": f"Tracking job for instance {instance_id} is not existed! Please check instance_id?"
            }
    else:
        logger.error(f"Instance {instance_id} was not tracked or not ready! Please check instance_id.")
        
        return {
            "status": "error",
            "message": f"Instance {instance_id} was not tracked or not ready! Please check instance_id."
        }