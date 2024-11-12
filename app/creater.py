from vastai import VastAI
import json
import re
from config import API_KEY

vast_sdk = VastAI(api_key=API_KEY)


def convert_str_to_dict(str):
    json_part = re.search(r"\{.*\}", str).group(0)
    json_part = json_part.replace("'", '"').replace("True", "true")
    data_object = json.loads(json_part)
    return data_object


def get_instance_id(str):
    return convert_str_to_dict(str)["new_contract"]


# Get SSH Addr and SSH Port
def get_ssh_info(instance_id):
    instance_info = vast_sdk.show_instance(id=instance_id)
    # Use Regular Expression to retrieve SSH Addr, SSH Port
    ssh_match = re.search(r"(\bssh[0-9]+\.vast\.ai)\s+(\d{5})\b", instance_info)
    # Return SSH Addr and SSH Port
    if ssh_match:
        ssh_addr = ssh_match.group(1)
        ssh_port = ssh_match.group(2)
        return {"ssh_addr": ssh_addr, "ssh_port": ssh_port}
    else:
        print("Not found ssh info!")
        return None, None


# Main function
# Create new instance and return (instance id, ssh_addr, ssh_port)
def launch_instance():
    instance = vast_sdk.launch_instance(
        num_gpus="1",
        gpu_name="RTX_3060",
        region="[VN]",
        image="pytorch/pytorch:2.1.2-cuda12.1-cudnn8-runtime",
        env="-p 8081:8081 -p 8680:8680",
    )
    if instance:
        instance_id = get_instance_id(instance)
        return {"id": instance_id}
    return None


def test():
    instance_info = launch_instance()
    print(instance_info)
    print(instance_info["id"])
    print(instance_info["ssh_addr"], instance_info["ssh_port"])
