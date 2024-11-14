from fastapi import FastAPI
from vastai import VastAI
import sys
import os
import json
import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import creater
from pydantic import BaseModel
import api_service
from config import API_KEY


class Ssh_attach(BaseModel):
    instance_id: int | str
    ssh_public_key: str


vast_sdk = VastAI(api_key=API_KEY)
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/instances")
async def get_instances():
    return api_service.get_instances()


@app.get("/instances/{instance_id}")
async def get_instance_info(instance_id : int):
    url = f"https://console.vast.ai/api/v0/instances?api_key={API_KEY}"

    payload = {}
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    response = requests.request("GET", url, headers=headers, data=payload).json()
    
    instances = response["instances"]
    

    for instance in instances:
        if instance["id"] == instance_id:
            ssh_addr = instance["ssh_host"]
            ssh_port = instance["ssh_port"]
            public_ip = instance["public_ipaddr"]
            host_ports_22_tcp = instance["ports"]["22/tcp"][0]["HostPort"]
            host_ports_8680_tcp = instance["ports"]["8680/tcp"][0]["HostPort"]
            return {"id": instance_id, "ssh_port": host_ports_22_tcp, "public_ip": public_ip, "deploy_port": host_ports_8680_tcp, }
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
async def create_instance(task: str, training_time: int, presets: str):
    # TODO: Implement the logic to create an instance based on 3 parameters
    
    return creater.launch_instance()

@app.post("/select_instance")
async def select_instance(task: str, training_time: int, presets: str):
    # TODO: If some appropriate instances already running, select it and return the instance_id
    # TODO: If no instances are running, create a new instance
    pass

# TODO: add shutdown instance method


@app.post("/instances/attach_ssh_key")
async def attach_ssh_key(ssh_attach: Ssh_attach):
    return vast_sdk.attach_ssh(
        instance_id=ssh_attach.instance_id, ssh_key=ssh_attach.ssh_public_key
    )


@app.delete("/instances/{instance_id}")
async def delete_instance(instance_id):
    return vast_sdk.destroy_instance(id=instance_id)

