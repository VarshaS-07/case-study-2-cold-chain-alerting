
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv

load_dotenv()

PASSWORD_ITERATIONS = 600_000
OTP_ITERATIONS = 100_000
SESSION_HOURS = 8


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, PASSWORD_ITERATIONS
    )
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    try:
        algorithm, rounds, salt_hex, digest_hex = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False

        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            bytes.fromhex(salt_hex),
            int(rounds),
        )
        return hmac.compare_digest(digest, bytes.fromhex(digest_hex))
    except (ValueError, TypeError):
        return False


def generate_otp():
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(otp):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", otp.encode(), salt, OTP_ITERATIONS
    )
    return f"{salt.hex()}${digest.hex()}"


def verify_otp(otp, stored):
    try:
        salt_hex, digest_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256", otp.encode(), bytes.fromhex(salt_hex),
            OTP_ITERATIONS
        )
        return hmac.compare_digest(digest, bytes.fromhex(digest_hex))
    except (ValueError, TypeError):
        return False


def auth_secret():
    secret = os.getenv("AUTH_SECRET")
    if not secret or len(secret) < 32:
        raise RuntimeError("AUTH_SECRET must contain at least 32 characters")
    return secret


def create_session(user_id):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(hours=SESSION_HOURS),
            "jti": secrets.token_hex(16),
        },
        auth_secret(),
        algorithm="HS256",
    )


def decode_session(token):
    return jwt.decode(
        token,
        auth_secret(),
        algorithms=["HS256"],
        options={"require": ["sub", "iat", "exp", "jti"]},
    )
