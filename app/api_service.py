import requests
import json
import time
from config import API_KEY
from vastai import VastAI
import asyncio

vast_sdk = VastAI(api_key=API_KEY)
url = f"https://console.vast.ai/api/v0/instances?api_key={API_KEY}"

payload = {}
headers = {"Accept": "application/json", "Content-Type": "application/json"}
response = requests.request("GET", url, headers=headers, data=payload)


instance_attr = [
    "id",
    "geolocation",
    "ssh_host",
    "ssh_port",
    "direct_port_start",
    "direct_port_end",
    "public_ipaddr",
    "ports",
    "machine_id",
    "host_id",
    "num_gpus",
    "gpu_name",
    "cpu_name",
    "image_uuid",
    "image_runtype",
    "extra_env",
    "onstart",
    "machine_dir_ssh_port",
]

appropriate_attr = {
    "image_uuid": "pytorch/pytorch:2.1.2-cuda12.1-cudnn8-runtime",
    "gpu_name": "RTX 3060",
}


def get_instances():
    response = requests.request("GET", url, headers=headers, data=payload)
    
    if response:
        return response.json()["instances"]
    else:
        time.sleep(0.2)
        
        response = requests.request("GET", url, headers=headers, data=payload)
        return response.json()["instances"]

def get_instance(id):
    instances = get_instances()
    found_instance = None
    for obj in instances:
        if obj["id"] == int(id):
            found_instance = obj
            break
    return found_instance


# def essential_instance_info(old_instance, attributes):
#     return {attr: old_instance[attr] for attr in attributes}


# def get_instance_info(id):
#     return essential_instance_info(get_instance(id), instance_attr)


def get_instance_info(id):
    instance = get_instance(id)
    if instance:
        ssh_addr = instance["ssh_host"]
        ssh_port = instance["ssh_port"]
        public_ip = instance["public_ipaddr"]
        
        host_ports_22_tcp = ""
        
        if "22/tcp" in instance["ports"]:
            host_ports_22_tcp = instance["ports"]["22/tcp"][0]["HostPort"]
        # host_ports_8680_tcp = instance["ports"]["8680/tcp"][0]["HostPort"]
        return {
            "id": id,
            "ssh_port": host_ports_22_tcp,
            "public_ip": public_ip,
            "deploy_port": "",
        }
    return None


def get_ssh_info(id):
    instance = get_instance(id)
    if instance:
        ssh_addr = instance["ssh_host"]
        ssh_port = instance["ssh_port"]
        return {"ssh_addr": ssh_addr, "ssh_port": ssh_port}


def get_ip_and_hostport(id):
    instance = get_instance(id)
    if instance:
        public_ip = instance["public_ipaddr"]
        host_ports_8680_tcp = instance["ports"]["8680/tcp"][0]["HostPort"]
        return {"public_ip": public_ip, "hostports": host_ports_8680_tcp}


def get_appropriate_instance(task: str, training_time: int, presets: str):
    instances = get_instances()
    appropriate_instance = None
    match = True
    for instance in instances:
        if instance["cur_state"] == "stopped":
            match = True
            for key, value in appropriate_attr.items():
                print(key, ": ", instance[key])
                if instance[key] != value:
                    match = False
                    break
            if match == True:
                appropriate_instance = instance
                break
    return appropriate_instance


async def select_available_instance(task: str, training_time: int, presets: str):
    appropriate_instance = get_appropriate_instance(task, training_time, presets)

    if appropriate_instance:
        instance_id = appropriate_instance["id"]
        vast_sdk.start_instance(id=instance_id)

        threshold = 20
        count = 0

        while count < threshold:
            try:
                instance_info = get_instance_info(instance_id)
                print(instance_info)
                print(
                    "Successfully get instance info, iter:",
                    count,
                    ", time: ",
                    count * 5,
                    "s",
                )
                count = threshold
                return instance_info
            except:
                print("Waiting for starting instance, iteration:", count)
                count = count + 1
                await asyncio.sleep(5)

    return None