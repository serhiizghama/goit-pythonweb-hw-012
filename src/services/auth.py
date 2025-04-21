import json
from datetime import datetime, timedelta, UTC
from typing import Optional

from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
import redis.asyncio as redis

from src.database.db import get_db
from src.conf.config import config as app_config
from src.services.users import UserService


class Hash:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        return self.pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

redis_client = redis.Redis.from_url(app_config.REDIS_URL, decode_responses=True)


async def create_access_token(data: dict, expires_delta: Optional[int] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + timedelta(seconds=expires_delta)
    else:
        expire = datetime.now(UTC) + timedelta(
            seconds=int(app_config.JWT_EXPIRATION_TIME)
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, app_config.JWT_SECRET, algorithm=app_config.JWT_ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, app_config.JWT_SECRET, algorithms=[app_config.JWT_ALGORITHM]
        )
        username = payload["sub"]
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    cached_user = await redis_client.get(f"user:{username}")
    if cached_user:
        return json.loads(cached_user)

    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)

    if user is None:
        raise credentials_exception

    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar": user.avatar
    }
    await redis_client.set(f"user:{username}", json.dumps(user_dict), ex=3600)

    return user


def create_email_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=1)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    token = jwt.encode(
        to_encode, app_config.JWT_SECRET, algorithm=app_config.JWT_ALGORITHM
    )
    return token


async def get_email_from_token(token: str):
    try:
        payload = jwt.decode(
            token, app_config.JWT_SECRET, algorithms=[app_config.JWT_ALGORITHM]
        )
        email = payload["sub"]
        return email
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid token",
        )