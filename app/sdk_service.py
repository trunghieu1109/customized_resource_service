import asyncio
from vastai import VastAI
import json
import re
from config import API_KEY

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import api_service
import mail_service

vast_sdk = VastAI(api_key=API_KEY)


def convert_str_to_dict(str):
    json_part = re.search(r"\{.*\}", str).group(0)
    json_part = json_part.replace("'", '"').replace("True", "true")
    data_object = json.loads(json_part)
    return data_object


def get_instance_id(str):
    obj = convert_str_to_dict(str)
    return obj["new_contract"]


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
async def launch_instance(task: str, training_time: int, presets: str):
    instance = vast_sdk.launch_instance(
        num_gpus="1",
        gpu_name="RTX_3060",
        region="[VN]",
        disk=20,
        image="pytorch/pytorch:2.1.2-cuda12.1-cudnn8-runtime",
        env="-p 8081:8081 -p 8680:8680",
        jupyter_dir="/",
        jupyter_lab=True,
        ssh=True,
        direct=True,
        onstart_cmd="sudo apt-get install screen unzip nano zsh htop lsof default-jre zip -yenv | grep _ >> /etc/environment; echo 'starting up'",
    )
    print("----------")
    if instance:
        try:
            print(instance)
            instance_id = get_instance_id(instance)
        except:
            instance = vast_sdk.launch_instance(
                num_gpus="1",
                gpu_name="RTX_3060",
                disk=20,
                image="pytorch/pytorch:2.1.2-cuda12.1-cudnn8-runtime",
                env="-p 8081:8081 -p 8680:8680",
                jupyter_dir="/",
                jupyter_lab=True,
                ssh=True,
                direct=True,
                onstart_cmd="sudo apt-get install screen unzip nano zsh htop lsof default-jre zip -yenv | grep _ >> /etc/environment; echo 'starting up'",
            )
            print("Failed to create instance!")
            print("Recreating instance...")
            print(instance)
            instance_id = get_instance_id(instance)

        print(instance_id)

        threshold = 30  # 150s, = 2.5 minutes
        count = 0

        while count < threshold:
            try:
                instance_info = api_service.get_instance_info(instance_id)
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
                print("Waiting for launching instance, iteration:", count)
                count = count + 1
                await asyncio.sleep(5)

    print("Instance takes too long to launch successfully!")
    print("Recreating instance...")
    launch_instance(task, training_time, presets)
    return None

def compose_body_error_instance(client_email, instance, message):
    return f"""
                Dear {client_email},

                We are pleased to inform you that the processing of your instance on Vast AI has been error.

                Instance ID: {instance['id']}
                Image: {instance['image_uuid']}
                Error Message: {message}
                
                You now have the option to either:

                1. Delete the instance (This will permanently remove it from the system).
                2. Stop the instance (This will halt its current execution, but it can be resumed later).
                
                If you have any questions or need further assistance, feel free to reach out to our support team.

                Best regards,
                iSE Laboratory
            """

def compose_subject_error_instance(instance_id):
    return f"Notification about the process of the instance {instance_id} on Vast AI has been error."

def compose_body_finished_instance(client_email, instance):
    return f"""
                Dear {client_email},

                We are pleased to inform you that the processing of your instance on Vast AI has been completed.

                Instance ID: {instance['id']}
                Image: {instance['image_uuid']}
                
                You now have the option to either:

                1. Delete the instance (This will permanently remove it from the system).
                2. Stop the instance (This will halt its current execution, but it can be resumed later).
                
                If you have any questions or need further assistance, feel free to reach out to our support team.

                Best regards,
                iSE Laboratory
            """

def compose_subject_finished_instance(instance_id):
    return f"Notification about the process of the instance {instance_id} on Vast AI has been completed."

async def post_process(instance_id: str, option: str, client_email: str = ""):
    
    instance = api_service.get_instance(instance_id)
    
    if instance and instance['cur_state'] != "stopped":
        if option == "stop":
            vast_sdk.stop_instance(ID=instance_id)
        elif option in ["destroy", "delete"]:
            vast_sdk.destroy_instance(id=instance_id)
        elif option == "send email":
            
            subject = compose_subject_finished_instance(instance_id)
            body = compose_body_finished_instance(client_email, instance)
            
            result = mail_service.send_email(client_email, subject, body)
            
            return result
            
        else:
            return {
                "status": "error",
                "message": "Process option is invalid! You shoud pass one of the following options: stop, destroy or send email."
            }
        
        return {
            "status": "success",
            "message": f"Post process instance {instance_id}, option: {option} successfully!"
        }
    else:
        return {
            "status": "error",
            "message": f"Instance {instance_id} was not existed or stopped! Please check instace_id."
        }


def test():
    instance_info = launch_instance()
    print(instance_info)
    print(instance_info["id"])
    print(instance_info["ssh_addr"], instance_info["ssh_port"])
