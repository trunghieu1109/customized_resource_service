# config.py
import configparser

# Tạo đối tượng configparser
config = configparser.ConfigParser()

# Đọc tệp environment.ini
config.read("environment.ini")

# Lưu trữ các biến môi trường
API_KEY = config["vastai"]["api_key"]

# Email server config
SENDER_EMAIL = config["email"]["sender_email"]
SENDER_PWD = config["email"]["sender_pwd"]
SERVER_HOST = config["email"]["server_host"]
SERVER_PORT = config["email"]["server_port"]
SENDER_NAME = config["email"]["sender_name"]

# Redis connection config
REDIS_HOST = config["redis"]["redis_host"]
REDIS_PORT = config["redis"]["redis_port"]
POOL_SIZE = config["redis"]["pool_size"]