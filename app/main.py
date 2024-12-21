from fastapi import FastAPI, Depends, Header, HTTPException, status
from vastai import VastAI
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sdk_service
import schedule_service
import api_service
import auth_service
from config import API_KEY
from pydantic import BaseModel
import logging

class Ssh_attach(BaseModel):
    instance_id: int | str
    ssh_public_key: str
    

class InstanceRequest(BaseModel):
    task: str
    training_time: int
    presets: str
    
class JobRequest(BaseModel):
    instance_id: int | str
    time_interval: int
    test_script: str
    backup_script: str
    option: str
    client_email: str
    
class PostProcessRequest(BaseModel):
    instance_id: int | str
    option: str
    client_email: str
    
class SignUpRequest(BaseModel):
    username: str
    password: str
    
class LogInRequest(BaseModel):
    username: str
    password: str
    
vast_sdk = VastAI(api_key=API_KEY)
app = FastAPI(
    title="Resource Service",
    description="This is resource service.",
    version="1.0.0",
    docs_url="/docs"
)

logger = logging.getLogger("resource_service")

async def check_access_token(access_token : str = Header(None)):
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is missing or invalid",
        )

    message = await auth_service.verify_token(access_token)
    
    if message['status'] == 'error':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message['message'],
        )

    return message['user_info']

def get_username_from_data(user_info: dict):
    username = user_info["username".encode("utf-8")].decode("utf-8")
    return username

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/instances")
async def get_instances(user_info : dict = Depends(check_access_token)):
    """
    Get list of all instances
    """
    
    username = get_username_from_data(user_info)
    logger.info(f"{username} gets all instances's information.")
    
    return api_service.get_instances()

@app.get("/instances/{instance_id}")
async def get_instance_info(instance_id: int, user_info : dict = Depends(check_access_token)):
    """
    Get instance's information
    """
    
    username = get_username_from_data(user_info)
    logger.info(f"{username} gets information of instance {instance_id}.")
    
    info = api_service.get_instance_info(instance_id)
    if info:
        return info
    return {"status": "failed"}

@app.get("/instances/ssh_info/{instance_id}")
async def get_ssh(instance_id, user_info : dict = Depends(check_access_token)):
    """
    Get instance's ssh information
    """
    
    username = get_username_from_data(user_info)
    logger.info(f"{username} gets ssh info of instance {instance_id}.")
    
    return api_service.get_ssh_info(instance_id)

@app.get("/instances/ip_and_hostport/{instance_id}")
async def get_ip_and_hostport(instance_id, user_info : dict = Depends(check_access_token)):
    """
    Get instance's ip and hostport
    """
    
    username = get_username_from_data(user_info)
    logger.info(f"{username} gets ip pand hostport of instance {instance_id}")
    
    return api_service.get_ip_and_hostport(instance_id)


@app.post("/instances")
async def create_instance(req: InstanceRequest, user_info : dict = Depends(check_access_token)):
    """
    Create an instance
    """
    
    username = get_username_from_data(user_info)
    
    # TODO: Implement the logic to create an instance based on 3 parameters
    new_istance = await sdk_service.launch_instance(req.task, req.training_time, req.presets)
    
    logger.info(f"{username} creates new instance {new_istance['id']}.")
    
    return new_istance


@app.post("/select_instance")
async def select_instance(req: InstanceRequest, user_info : dict = Depends(check_access_token)):
    """
    Select appropriate instance for current task, presets and training time
    """
    
    username = get_username_from_data(user_info)
    logger.info(f"{username} selects appropriate instance for current task, presets and training time.")
    
    # TODO: If some appropriate instances already running, select it and return the instance_id
    # TODO: If no instances are running, create a new instance
    instance = await api_service.select_available_instance(req.task, req.training_time, req.presets)
    if instance:
        return instance
    return await create_instance(req)


@app.get("/instances/start/{instance_id}")
async def start_instance(instance_id: int, user_info : dict = Depends(check_access_token)):
    """
    Start an instance
    """
    
    username = get_username_from_data(user_info)
    logger.info(f"{username} starts instance {instance_id}")
    
    return vast_sdk.start_instance(id=instance_id)


# TODO: add shutdown instance method
@app.get("/instances/stop/{instance_id}")
async def stop_instance(instance_id: int, user_info : dict = Depends(check_access_token)):
    """
    Stop an instance
    """
    
    username = get_username_from_data(user_info)
    logger.info(f"{username} stops instance {instance_id}")
    
    return vast_sdk.stop_instance(id=instance_id)


@app.post("/instances/attach_ssh_key")
async def attach_ssh_key(ssh_attach: Ssh_attach, user_info : dict = Depends(check_access_token)):
    """
    Attach ssh key to an instance
    """
    
    username = get_username_from_data(user_info)
    logger.info(f"{username} attachs ssh key to instance {ssh_attach.instance_id}")
    
    return vast_sdk.attach_ssh(
        instance_id=ssh_attach.instance_id, ssh_key=ssh_attach.ssh_public_key
    )


@app.delete("/instances/{instance_id}")
async def delete_instance(instance_id, user_info : dict = Depends(check_access_token)):
    """
    Delete an instance
    """
    
    username = get_username_from_data(user_info)
    logger.info(f"{username} deletes instance {instance_id}")
    
    return vast_sdk.destroy_instance(id=instance_id)


# register new tracking job
@app.get("/instances/get_running_status/{instance_id}")
async def get_running_status(instance_id : str, user_info : dict = Depends(check_access_token)):
    """
    Get running status of an instance
    """
    
    username = get_username_from_data(user_info)
    logger.info(f"{username} gets running status of instance {instance_id}")
    
    msg = schedule_service.check_instance_status(instance_id)
    
    return msg
    
@app.post("/instances/create_tracking_job")
async def create_tracking_job(req: JobRequest, user_info : dict = Depends(check_access_token)):
    """
    Creating a new tracking job for an instance
    
    "instance_id" is id of an instance.
    
    "time_interval" is tracking time, calculated in seconds.
    
    "test_script", "backup_script" and "option" is optional. If you want to control and post process automatically, please provide fill these params. In the other case, set them to "".
    
    "option" is "stop", "destroy" or "send email".
    
    "client_email" is email that the system will send notification to.
    
    """
    username = get_username_from_data(user_info)
    logger.info(f"{username} creates a new tracking job for instance {req.instance_id}")
    
    msg = await schedule_service.create_tracking_job(req.instance_id, req.time_interval, req.test_script, 
                                                     req.backup_script, req.option, req.client_email)
    return msg

@app.post("/instances/post_process")
async def post_process(req: PostProcessRequest, user_info : dict = Depends(check_access_token)):
    """
    Post process an instance after it has finished or stopped
    
    "instance_id" is id of an instance.
    
    "option" is "stop", "destroy" or "send email".
    
    "client_email" is email that the system will send notification to.
    
    """
    
    username = get_username_from_data(user_info)
    logger.info(f"{username} post process instance {req.instance_id}")
    
    schedule_msg = schedule_service.remove_tracking_job(req.instance_id)
    
    if schedule_msg['status'] == "success":
    
        sdk_msg = await sdk_service.post_process(req.instance_id, req.option, req.client_email)
        
        if sdk_msg['status'] == 'success':
    
            return {
                "status": "success",
                "message": f"Schedule message: {schedule_msg}, SDK messsage: {sdk_msg}."
            }
            
        else:
            return sdk_msg
    
    else:
        return schedule_msg
    
@app.post("/instances/remove_error_job")
async def remove_error_job(instance_id: str, user_info : dict = Depends(check_access_token)):
    """
    Remove error job (forgetting to be removed)
    
    "instance_id" is id of an instance.
    
    """
    
    username = get_username_from_data(user_info)
    logger.info(f"{username} removes error tracking job of instance {instance_id}")
    
    msg = schedule_service.remove_error_job(instance_id)
    
    return msg

@app.post("/instances/get_all_tracking_jobs")
async def get_all_tracking_jobs(user_info : dict = Depends(check_access_token)):
    """
    Get all tracking jobs
    
    """
    
    username = get_username_from_data(user_info)
    logger.info(f"{username} gets all tracking jobs")
    
    msg = await schedule_service.get_all_tracking_jobs()
    
    return msg
        
@app.post("/instances/signup")
async def signup(req: SignUpRequest):
    """
    Sign up a new account
    
    "username"
    "password"
    
    """
    
    logger.info(f"{req.username} signs up.")
    
    msg = await auth_service.create_account(req.username, req.password)
    
    return msg
        
@app.post("/instances/login")
async def login(req: LogInRequest):
    """
    Login the system
    
    "username"
    "password"
    
    """
    
    logger.info(f"{req.username} logs in.")
    
    msg = await auth_service.authenticate(req.username, req.password)
    
    return msg
        
@app.post("/instances/logout")
async def logout(user_info : dict = Depends(check_access_token)):
    """
    Logout from system
    
    "access_token"
    
    """
    
    username = get_username_from_data(user_info)
    logger.info(f"{username} logs out.")
    
    msg = await auth_service.logout(user_info)
    
    return msg
        
 