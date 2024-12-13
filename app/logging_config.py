import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

handler = logging.StreamHandler(sys.stdout)

handler.setLevel(logging.INFO)

handler.flush = sys.stdout.flush

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: [%(name)s][%(asctime)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[handler],
    force=True
)

def get_logger():
    return logging.getLogger("resource_service")

# Test logger
logger = get_logger()
logger.info("This is an info message")
