import logging
import sys
import os
import time
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

directory_path = "logs" 

if not os.path.exists(directory_path):
    os.makedirs(directory_path)

timestamp = str(int(time.time()))
filepath = f"logs/resource_service_{timestamp}.log"
filepath_ = Path(filepath)

if not filepath_.exists():
    print("Create ", filepath)
    filepath_.touch()  
    
handler = logging.FileHandler(filepath, mode='a')

handler.setLevel(logging.INFO)
handler.flush = handler.stream.flush

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: [%(name)s][%(asctime)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[handler],
    force=True
)

def get_logger(log_src: str):
    return logging.getLogger(log_src)
