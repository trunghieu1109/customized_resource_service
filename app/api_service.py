import requests
import json
from config import API_KEY

url = f"https://console.vast.ai/api/v0/instances?api_key={API_KEY}"

payload = {}
headers = {
   'Accept': 'application/json',
   'Content-Type': 'application/json'
}

def create_new_object(old_obj, attributes):
    return {attr: old_obj[attr] for attr in attributes}

old_object = {
    "id": 1,
    "name": "Old Object",
    "description": "This is the old object",
    "value": 100
}

def create_new_object(old_obj, attributes):
    return {attr: old_obj[attr] for attr in attributes}

old_object = {
    "id": 1,
    "name": "Old Object",
    "description": "This is the old object",
    "value": 100
}

id_to_find = 13612535
found_object = None
response = requests.request("GET", url, headers=headers, data=payload)
# print(response.json())
# print(type(response.json()))
for obj in response.json()["instances"]:
  if(obj["id"] == id_to_find):
    found_object = obj
    break

def create_new_object(old_obj, attributes):
    return {attr: old_obj[attr] for attr in attributes}

#print(found_object)
attr = ["machine_id", 'geolocation', 'host_id', 'id', 'num_gpus', 'gpu_name', 'gpu_ram',
        'gpu_totalram', 'cpu_name', 'cpu_ram', 'cpu_cores', 'ssh_host', 'ssh_port', 'image_uuid', 'image_runtype', 'extra_env', 'onstart', 'direct_port_end', 'direct_port_start', 'ports']
attributes_to_copy = ["id", "name"]

new_object = create_new_object(old_object, attributes_to_copy)

#print(new_object)



