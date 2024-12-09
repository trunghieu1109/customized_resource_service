from fastapi import FastAPI
from vastai import VastAI
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import app.sdk_service as sdk_service
import app.schedule_service as schedule_service
import api_service
from config import API_KEY
from pydantic import BaseModel

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
    
vast_sdk = VastAI(api_key=API_KEY)
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/instances")
async def get_instances():
    return api_service.get_instances()


# @app.get("/instances/{instance_id}")
# async def get_instance_info(instance_id: int):
#     url = f"https://console.vast.ai/api/v0/instances?api_key={API_KEY}"

#     payload = {}
#     headers = {"Accept": "application/json", "Content-Type": "application/json"}
#     response = requests.request("GET", url, headers=headers, data=payload).json()

#     instances = response["instances"]

#     for instance in instances:
#         if instance["id"] == instance_id:
#             ssh_addr = instance["ssh_host"]
#             ssh_port = instance["ssh_port"]
#             public_ip = instance["public_ipaddr"]
#             host_ports_22_tcp = instance["ports"]["22/tcp"][0]["HostPort"]
#             host_ports_8680_tcp = instance["ports"]["8680/tcp"][0]["HostPort"]
#             return {
#                 "id": instance_id,
#                 "ssh_port": host_ports_22_tcp,
#                 "public_ip": public_ip,
#                 "deploy_port": host_ports_8680_tcp,
#             }
#     return {"status": "failed"}


@app.get("/instances/{instance_id}")
async def get_instance_info(instance_id: int):
    info = api_service.get_instance_info(instance_id)
    if info:
        return info
    return {"status": "failed"}


# return {"ssh_addr": str, "ssh_port": int}
@app.get("/instances/ssh_info/{instance_id}")
async def get_ssh(instance_id):
    return api_service.get_ssh_info(instance_id)


# return {"public_ip": str, "hostport": str}
@app.get("/instances/ip_and_hostport/{instance_id}")
async def get_ip_and_hostport(instance_id):
    return api_service.get_ip_and_hostport(instance_id)


@app.post("/instances")
async def create_instance(req: InstanceRequest):
    # TODO: Implement the logic to create an instance based on 3 parameters
    new_istance = await sdk_service.launch_instance(req.task, req.training_time, req.presets)
    return new_istance


@app.post("/select_instance")
async def select_instance(req: InstanceRequest):
    # TODO: If some appropriate instances already running, select it and return the instance_id
    # TODO: If no instances are running, create a new instance
    instance = await api_service.select_available_instance(req.task, req.training_time, req.presets)
    if instance:
        return instance
    return await create_instance(req)


@app.get("/instances/start/{instance_id}")
async def start_instance(instance_id: int):
    return vast_sdk.start_instance(ID=instance_id)


# TODO: add shutdown instance method
@app.get("/instances/stop/{instance_id}")
async def stop_instance(instance_id: int):
    return vast_sdk.stop_instance(ID=instance_id)


@app.post("/instances/attach_ssh_key")
async def attach_ssh_key(ssh_attach: Ssh_attach):
    return vast_sdk.attach_ssh(
        instance_id=ssh_attach.instance_id, ssh_key=ssh_attach.ssh_public_key
    )


@app.delete("/instances/{instance_id}")
async def delete_instance(instance_id):
    return vast_sdk.destroy_instance(id=instance_id)


# register new tracking job
@app.post("/instances/create_tracking_job")
async def create_tracking_job(req: JobRequest):
    msg = await schedule_service.create_tracking_job(req.instance_id, req.time_interval, req.test_script, 
                                                     req.backup_script, req.option, req.client_email)
    return msg

@app.post("/instances/post_process")
async def post_process(req: PostProcessRequest):
    
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