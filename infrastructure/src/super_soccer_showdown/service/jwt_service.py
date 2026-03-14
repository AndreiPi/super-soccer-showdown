import json
import os
from datetime import datetime, timedelta, timezone

import jwt
import logging

logger = logging.getLogger("super_soccer_showdown.jwt")


class JWTConfig:
    SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "test-secret-key-with-at-least-32-bytes")
    ALGORITHM = "HS256"
    EXPIRATION_MINUTES = int(os.environ.get("JWT_EXPIRATION_MINUTES", "60"))

def get_jwt_payload(event: dict) -> dict:
    headers = event.get("headers", {})
    auth_header = headers.get("Authorization") or headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise ValueError("Missing or invalid Authorization header")
    token = auth_header.split(" ", 1)[1]
    return decode_token(token)


def generate_token(user_id: int, username: str) -> str:
    """Generate JWT token for authenticated user."""
    payload = {
        "user_id": user_id,
        "username": username,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWTConfig.EXPIRATION_MINUTES),
    }
    token = jwt.encode(payload, JWTConfig.SECRET_KEY, algorithm=JWTConfig.ALGORITHM)
    logger.info(f"Generating JWT for user_id={user_id}, username={username}")
    return token


def decode_token(token: str) -> dict:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, JWTConfig.SECRET_KEY, algorithms=[JWTConfig.ALGORITHM])
        logger.info(f"Decoded JWT payload: {payload}")
        return payload
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        raise ValueError(f"Invalid token: {str(e)}")
