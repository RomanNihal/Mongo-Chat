import jwt
from datetime import datetime, timedelta, timezone
from src.config import AppConfig

class AuthHandler:
    @staticmethod
    def create_access_token(data: dict):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=AppConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, AppConfig.JWT_SECRET_KEY, algorithm=AppConfig.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token):
        try:
            payload = jwt.decode(token, AppConfig.JWT_SECRET_KEY, algorithms=[AppConfig.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None