from typing import Union
from fastapi import FastAPI
from vastai import VastAI
from app import creater
from pydantic import BaseModel
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
    return vast_sdk.show_instances()

@app.get("/instances/{instance_id}")
async def get_instances(instance_id):
    return vast_sdk.show_instance(id=instance_id)

@app.get("/instances/ssh_infos/{instance_id}")
async def get_ssh(instance_id):
    return creater.get_ssh_info(instance_id)

@app.post("/instances")
async def create_instance():
    return creater.launch_instance()

@app.post("/instances/attach_ssh_key")
async def attach_ssh_key(ssh_attach: Ssh_attach):
    return vast_sdk.attach_ssh(instance_id=ssh_attach.instance_id, ssh_key=ssh_attach.ssh_public_key)

@app.delete("/instances/{instance_id}")
async def delete_instance(instance_id):
    vast_sdk.destroy_instance(id=instance_id)