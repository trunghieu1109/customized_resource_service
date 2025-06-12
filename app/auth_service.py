import sys
import os
import bcrypt
import jwt
import redis
from datetime import datetime, timedelta
from typing import Dict, Any
from config import REDIS_HOST, REDIS_PORT, SECRET_KEY, JWT_ALGORITHM
from constants import TOKEN_EXPIRED_TIME_HOURS, TOKEN_EXPIRED_TIME_DAYS, TOKEN_EXPIRED_TIME_MINUTES
import logging 

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

logger = logging.getLogger("auth_service")

def encode_password(password: str) -> str:
    hashed_pwd = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_pwd.decode('utf-8')

def check_pwd(password: str, hashed_pwd: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_pwd.encode('utf-8'))

def create_access_token(username: str) -> str:
    """Tạo JWT access token."""
    expire = datetime.utcnow() + timedelta(days=TOKEN_EXPIRED_TIME_DAYS, hours=TOKEN_EXPIRED_TIME_HOURS, minutes=TOKEN_EXPIRED_TIME_MINUTES)
    payload = {
        "username": username,
        "exp": expire
    }
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def verify_token(access_token: str) -> Dict[str, Any]:
    """
    Xác minh tính hợp lệ của access token.
    1. Giải mã JWT và kiểm tra hết hạn.
    2. Lấy thông tin người dùng từ Redis.
    3. Kiểm tra người dùng có đang 'active' không.
    4. So sánh token được cung cấp với token lưu trong Redis để đảm bảo là token mới nhất.
    """
    
    logger.info("Checking access token")
    
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        print(payload)
        username: str = payload.get("username")
        if username is None:
            return {"status": "error", "message": "Invalid token payload."}
    except jwt.ExpiredSignatureError:
        return {"status": "error", "message": "Token has expired."}
    except jwt.PyJWTError:
        return {"status": "error", "message": "Invalid token."}

    user_key = f"users:{username}"
    user_data = redis_client.hgetall(user_key)

    if not user_data:
        return {"status": "error", "message": "User not found."}

    if user_data.get("active") != "1":
        return {"status": "error", "message": "User is not active. Please log in."}
    
    if user_data.get("token") != access_token:
        return {"status": "error", "message": "Token is invalid or has been revoked."}

    return {"status": "success", "message": "Token is valid.", "user_info": user_data}
       
async def logout(user_info: dict) -> Dict[str, Any]:
    logger.info("Logging out .....")

    username = user_info["username"]
    user_key = f"users:{username}"
    if redis_client.exists(user_key):
        update_data = {
            "active": "0",
            "token": "" # Xóa token cũ
        }
        redis_client.hset(user_key, mapping=update_data)

    return {"status": "success", "message": "Logged out successfully."}

async def authenticate(username: str, password: str) -> Dict[str, Any]:

    logger.info(f"Authenticate for account {username}")
    
    if username == "" or password == "":
        return {
            "status": "error",
            "message": "Username or password is required. Please fill all the required fields."
        }
    
    user_key = f"users:{username}"
    user_data = redis_client.hgetall(user_key)

    if not user_data:
        return {"status": "error", "message": "Invalid username or password."}
    
    print(user_data)

    if not check_pwd(password, user_data.get("password", "")):
        return {"status": "error", "message": "Invalid username or password."}

    access_token = create_access_token(username)

    update_data = {
        "active": "1",
        "token": access_token,
        "created_time": str(datetime.now()),
        "expired_time": str(datetime.now() + timedelta(days=TOKEN_EXPIRED_TIME_DAYS, hours=TOKEN_EXPIRED_TIME_HOURS, minutes=TOKEN_EXPIRED_TIME_MINUTES))
    }
    
    redis_client.hset(user_key, mapping=update_data)

    return {
        "status": "success",
        "message": "Authentication successful.",
        "access_token": access_token
    }

async def create_account(username: str, password: str) -> Dict[str, Any]:
    
    logger.info(f"Create new account, username: {username}, password: {password}")
    
    if username == "" or password == "":
        return {
            "status": "error",
            "message": "Username or password is required. Please fill all the required fields."
        }
    
    user_key = f"users:{username}"
    if redis_client.exists(user_key):
        return {"status": "error", "message": f"Username '{username}' already exists. Please try other username."}

    hashed_password = encode_password(password)
    user_data = {
        "username": username,
        "password": hashed_password,
        "active": "0",  # 0: inactive/logged-out, 1: active/logged-in
        "token": "",    # Token hiện tại đang được sử dụng
        "created_time": "",
        "expired_time": ""
    }

    redis_client.hset(user_key, mapping=user_data)
    return {"status": "success", "message": "Account created successfully."}  