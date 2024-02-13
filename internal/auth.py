"""
認証関連の処理を行うモジュール

参考: https://fastapi.tiangolo.com/ja/tutorial/security/oauth2-jwt/
"""

from hashlib import sha256
import secrets

SALT = "9881bfb57714f87b671c"


def encrypt_password(password: str) -> str:
    return sha256((password + SALT).encode()).hexdigest()


def generate_token() -> str:
    return secrets.token_urlsafe(32)
