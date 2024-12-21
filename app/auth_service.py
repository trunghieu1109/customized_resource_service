import sys
import os
import bcrypt
import jwt
import redis
import datetime
from config import REDIS_HOST, REDIS_PORT, SECRET_KEY, JWT_ALGORITHM
from constants import TOKEN_EXPIRED_TIME_HOURS, TOKEN_EXPIRED_TIME_DAYS, TOKEN_EXPIRED_TIME_MINUTES
import logging 

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)

logger = logging.getLogger("auth_service")

def encode_password(password: str):
    hashed_pwd = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    
    return hashed_pwd

def check_pwd(password: str, hashed_pwd: str):
    return bcrypt.checkpw(password.encode("utf-8"), hashed_pwd)

def create_access_token(username: str):
    payload = {
        'username': username,
        'exp': datetime.datetime.now() + datetime.timedelta(days=TOKEN_EXPIRED_TIME_DAYS, hours=TOKEN_EXPIRED_TIME_HOURS, minutes=TOKEN_EXPIRED_TIME_MINUTES)
    }
    
    access_token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return access_token

async def verify_token(access_token : str):
    
    logger.info("Checking access token")
    
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=JWT_ALGORITHM)
        
        if payload:
            
            username = payload["username"]
            
            user_data = redis_client.hgetall(f"users:{username}")
            
            if user_data:
                
                active = user_data["active".encode("utf-8")].decode("utf-8")
                stored_token = user_data["token".encode("utf-8")].decode("utf-8")
                expired_time = user_data["expired_time".encode("utf-8")].decode("utf-8")
                curr_time = str(datetime.datetime.now())
                
                if curr_time > expired_time:
                    return {
                        "status": "error",
                        "message": "Access token was expired. Please check your access token or try to login again."
                    }
                
                if str(active) == "0":
                    return {
                        "status": "error",
                        "message": "Account is not active. Please login before sending new request."
                    }
                else:
                    if stored_token != access_token:
                        return {
                            "status": "error",
                            "message": "Access token is not matched to the latest token. This could be expired or can be used. Please login again to get new access token."
                        }
                    else:
                        return {
                            "status": "success",
                            "message": "Access token is valid.",
                            "user_info": user_data
                        }
            else:
                return {
                    "status": "error",
                    "message": "Access token is not matched to existing user! Please check your access token."
                }
            
        else:
            return {
                "status": "error",
                "message": "Empty payload."
            }    
    
    except jwt.ExpiredSignatureError:
        return {
            "status": "error",
            "message": "Access token is expired."
        }
    except jwt.PyJWTError:
        return {
            "status": "error",
            "message": "Access token is invalid."
        }
        
async def logout(user_info: dict):
   
    username = user_info["username".encode("utf-8")].decode("utf-8")
    num_access = user_info['num_access'.encode("utf-8")].decode("utf-8")    
    
    num_access = max(int(num_access) - 1, 0)
    print(num_access)
    if int(num_access) == 0:
        active = 0
        redis_client.hset(f"users:{username}", "active", active)
    
    redis_client.hset(f"users:{username}", "num_access", num_access)
    
    return {
        "status": "success",
        "message": "Log out successfully."
    }

async def authenticate(username: str, password: str):
    
    global redis_client
    
    logger.info(f"Authenticate for account {username}")
    
    if username == "" or password == "":
        return {
            "status": "error",
            "message": "Username or password is required. Please fill all the required fields."
        }
    else:
        user_data = redis_client.hgetall(f"users:{username}")
        
        if not user_data:
            return {
                "status": "error",
                "message": "Username does not exist in the database. Please sign up a new account before logging in."
            }
            
        else:
            hashed_pwd = user_data["password".encode("utf-8")]
            
            is_matched = check_pwd(password, hashed_pwd)
            
            if is_matched:
                
                active = user_data["active".encode("utf-8")].decode("utf-8")
                num_access = user_data["num_access".encode("utf-8")].decode("utf-8")
                access_token = user_data["token".encode("utf-8")].decode("utf-8")
                
                if int(active) == 1:
                    redis_client.hset(f"users:{username}", "num_access", int(num_access) + 1)
                    
                    check_result = await verify_token(access_token)
                    if (check_result['status'] == 'error'):
                        access_token = create_access_token(username)
                        redis_client.hset(f"users:{username}", "token", access_token)
                        redis_client.hset(
                            f"users:{username}", 
                            "expired_time", 
                            str(datetime.datetime.now() + datetime.timedelta(days=TOKEN_EXPIRED_TIME_DAYS, hours=TOKEN_EXPIRED_TIME_HOURS, minutes=TOKEN_EXPIRED_TIME_MINUTES))
                        )
                    
                else:
                    access_token = create_access_token(username)
                    
                    redis_client.hset(f"users:{username}", "token", access_token)
                    redis_client.hset(f"users:{username}", "active", 1)
                    redis_client.hset(f"users:{username}", "num_access", 1)
                    redis_client.hset(f"users:{username}", "created_time", str(datetime.datetime.now()))
                    redis_client.hset(
                        f"users:{username}", 
                        "expired_time", 
                        str(datetime.datetime.now() + datetime.timedelta(days=TOKEN_EXPIRED_TIME_DAYS, hours=TOKEN_EXPIRED_TIME_HOURS, minutes=TOKEN_EXPIRED_TIME_MINUTES))
                    )
    
                return {
                    "status": "success",
                    "message": "Authenticate successfully.",
                    "access-token": access_token
                }
                
            else:
                return {
                    "status": "error",
                    "message": "Password is incorrect. Please check your password.",
                }
                

async def create_account(username: str, password: str):
    
    global redis_client
    
    logger.info(f"Create new account, username: {username}, password: {password}")
    
    if username == "" or password == "":
        return {
            "status": "error",
            "message": "Username or password is required. Please fill all the required fields."
        }
    else:
        user = redis_client.hget(f"users:{username}", "username")
        
        if user:
            return {
                "status": "error",
                "message": "Username existed in the database. Please try other username."
            }
        else:
            hashed_pwd = encode_password(password)
            
            account_info = {
                "username": username,
                "password": hashed_pwd,
                "active": 0,
                "token": "",
                "num_access": 0,
                "created_time": "",
                "expired_time": ""
            }
            
            redis_client.hset(f"users:{username}", mapping=account_info)
            
            return {
                "status": "success",
                "message": "Create account successfully."
            }
    
    