from vastai import VastAI
import sys
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import app.sdk_service as sdk_service
import api_service
from constants import GPU_USAGE_THRESHOLD, CPU_USAGE_THRESHOLD, FULL_DISK_USAGE_THRESHOLD, IDLE_DISK_USAGE_THRESHOLD 
from config import API_KEY
from pydantic import BaseModel
import mail_service

jobstores = {
    'default': RedisJobStore(host="localhost", port=6379, db=0)
}

executors = {
    'default': ThreadPoolExecutor(5)
}

scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors)
scheduler.start()

hash_name = "apscheduler.jobs"

class TrackingJob(BaseModel):
    instance_id: int | str
    test_script: str
    backup_script: str
    option: str
    client_email: str

vast_sdk = VastAI(api_key=API_KEY)

def check_instance_status(instance_id: str, test_script: str = ""):
    
    instance = api_service.get_instance(instance_id)

    if instance:
        gpu_util = instance['gpu_util']
        cpu_util = instance['cpu_util']
        disk_util = instance['disk_util']
        disk_space = instance['disk_space']
        
        if disk_util / disk_space * 100 > FULL_DISK_USAGE_THRESHOLD:
            return {
                "status": "error",
                "message": f"No space left in instance {instance_id}"
            }
        
        if gpu_util > GPU_USAGE_THRESHOLD or cpu_util > CPU_USAGE_THRESHOLD:
            return {
                "status": "processing",
                "message": f"Instance {instance_id} is processing, gpu and cpu are used"
            }
        else:
            if disk_util / disk_space * 100 < IDLE_DISK_USAGE_THRESHOLD:
                return {
                    "status": "ready",
                    "message": f"Instance {instance_id} is ready"
                }
            else:
                
                if test_script != "":
                    # TODO: Not tested yet
                    result = vast_sdk.execute(ID=instance_id, COMMAND=test_script)
                    
                    if result == "True":
                        return {
                            "status": "finished",
                            "message": f"Process in instance {instance_id} was finished"
                        }
                    else:
                        return {
                            "status": "ready",
                            "message": f"Instance {instance_id} is ready"
                        }   
                else:
                    return {
                        "status": "finished",
                        "message": f"Process in instance {instance_id} was finished"
                    }       
    else:      
        return {
            "status": "not existed",
            "message": f"Can't found instance matching id: {instance_id}"
        }

def tracking_job(job: TrackingJob):
    instance_status = check_instance_status(job.instance_id, job.test_script)
    
    print(instance_status)
    
    if instance_status['status'] == 'finished':
        
        instance = api_service.get_instance(job.instance_id)
        
        if instance:
            
            msg = None
            
            if job.backup_script != "":
                vast_sdk.execute(ID=job.instance_id, COMMAND=job.backup_script)
            
            if job.option == "stop":
                vast_sdk.stop_instance(ID=job.instance_id)
                job_id = "job_" + job.instance_id
        
                scheduler.remove_job(job_id=job_id)
            
            elif job.option in ["destroy", "delete"]:
                vast_sdk.destroy_instance(id=job.instance_id)
                job_id = "job_" + job.instance_id
        
                scheduler.remove_job(job_id=job_id)
                
            else:
                subject = sdk_service.compose_subject_finished_instance(job.instance_id)
                body = sdk_service.compose_body_finished_instance(job.client_email, instance)
                
                msg = mail_service.send_email(job.client_email, subject, body)
            
                return msg
                    
    elif instance_status['status'] == 'error':
        instance = api_service.get_instance(job.instance_id)
        
        if instance:
        
            subject = sdk_service.compose_subject_error_instance(job.instance_id)
            body = sdk_service.compose_body_error_instance(job.client_email, instance, instance_status['message'])
            
            msg = mail_service.send_email(job.client_email, subject, body)
            
            return msg
        
    return {
        "instance_status": instance_status['status'],
        "message": f"Tracking instance {job.instance_id} successfully! Log: {instance_status['message']}."
    }

async def create_tracking_job(instance_id: str, time_interval: int = "300", test_script: str = "", 
                              backup_script: str = "", option: str = "", client_email: str = ""):
    
    instance = api_service.get_instance(instance_id)
    
    if instance and instance['cur_state'] != 'stopped':  
        job_id = "job_" + instance_id
        
        if scheduler.get_job(job_id):
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
        
        scheduler.add_job(tracking_job, "interval", seconds = time_interval, args = [job], id = job_id)
        
        return {
            "status": "success",
            "message": f"Create tracking job for instance {instance_id} successfully!"
        }
    else:
        return {
            "status": "error",
            "message": f"Instance {instance_id} is not existed or stopped! Please check instance_id."
        }
        
def remove_tracking_job(instance_id: str):
    
    instance = api_service.get_instance(instance_id)
    if instance and instance['cur_state'] != "stopped":
        job_id = "job_" + instance_id
        
        job = scheduler.get_job(job_id)
        
        if job:
            scheduler.remove_job(job_id=job_id)
            return {
                "status": "success",
                "messasge": f"Remove tracking job of instance {instance_id} successfully!"
            }
        else:
            return {
                "status": "error",
                "message": f"Tracking job for instance {instance_id} is not existed! Please check instance_id?"
            }
    else:
        return {
            "status": "error",
            "message": f"Instance {instance_id} was not tracked or stopped! Please check instance_id."
        }