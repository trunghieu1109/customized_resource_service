import requests
import json
from config import API_KEY

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


def get_instances():
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()["instances"]


def get_instance(id):
    response = requests.request("GET", url, headers=headers, data=payload)
    found_instance = None
    for obj in response.json()["instances"]:
        if obj["id"] == int(id):
            found_instance = obj
            break
    return found_instance


def essential_instance_info(old_instance, attributes):
    return {attr: old_instance[attr] for attr in attributes}


def get_instance_info(id):
    return essential_instance_info(get_instance(id), instance_attr)


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
