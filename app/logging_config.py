import logging
import sys
import os
import time
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

directory_path = "logs" 

Path("logs").mkdir(parents=True, exist_ok=True)

timestamp = str(int(time.time()))
filepath = f"logs/resource_service_{timestamp}.log"
filepath_ = Path(filepath)

if not filepath_.exists():
    print("Create ", filepath)
    filepath_.touch()  
    
handler = logging.FileHandler(filepath, mode='a')

handler.setLevel(logging.INFO)
handler.flush = handler.stream.flush

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(
    logging.Formatter(
        "%(levelname)s: [%(name)s]: %(message)s"
    )
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: [%(name)s][%(asctime)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[handler, console_handler],
    force=True
)

def get_logger(log_src: str):
    return logging.getLogger(log_src)

if __name__ == "__main__":
    app_logger = get_logger("MyTestApp")
    app_logger.debug("Đây là một thông điệp debug, sẽ không hiện nếu LOG_LEVEL=INFO.")
    app_logger.info("Ứng dụng đang khởi chạy...")
    app_logger.warning("Cảnh báo: Cấu hình API key chưa được thiết lập.")
    app_logger.error("Không thể kết nối tới cơ sở dữ liệu.")
