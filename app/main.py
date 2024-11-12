from fastapi import FastAPI
from vastai import VastAI
import sys
import os

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
async def get_instances(instance_id):
    return api_service.get_instance_info(instance_id)


# return {"ssh_addr": str, "ssh_port": int}
@app.get("/instances/ssh_info/{instance_id}")
async def get_ssh(instance_id):
    return api_service.get_ssh_info(instance_id)


# return {"public_ip": str, "hostports": str[]}
@app.get("/instances/ip_and_hostports/{instance_id}")
async def get_ip_and_hostports(instance_id):
    return api_service.get_ip_and_hostports(instance_id)


# return {"id": int}
@app.post("/instances")
async def create_instance():
    return creater.launch_instance()


@app.post("/instances/attach_ssh_key")
async def attach_ssh_key(ssh_attach: Ssh_attach):
    return vast_sdk.attach_ssh(
        instance_id=ssh_attach.instance_id, ssh_key=ssh_attach.ssh_public_key
    )


@app.delete("/instances/{instance_id}")
async def delete_instance(instance_id):
    return vast_sdk.destroy_instance(id=instance_id)
