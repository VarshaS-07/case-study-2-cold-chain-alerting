
from datetime import timedelta
import re
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
import jwt

from backend.database import get_db
from backend.models import User, LoginOTP
from backend.auth.security import (
    utc_now,
    verify_password,
    generate_otp,
    hash_otp,
    verify_otp,
    create_session,
    decode_session,
)
from backend.notifications.email_sender import send_alert_email


router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer = HTTPBearer(auto_error=False)

# Simple per-IP throttling for the single-process demo.
requests_by_ip = {}


def check_rate_limit(request: Request, action: str, limit: int):
    ip = request.client.host if request.client else "unknown"
    key = (ip, action)
    now = time.monotonic()

    recent = [
        t for t in requests_by_ip.get(key, [])
        if now - t < 300
    ]

    if len(recent) >= limit:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Try again later.",
        )

    recent.append(now)
    requests_by_ip[key] = recent


class LoginRequest(BaseModel):
    username: str
    password: str


class OTPRequest(BaseModel):
    username: str
    otp: str


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Login required")

    try:
        payload = decode_session(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session",
        )

    user = db.get(User, user_id)

    if user is None or user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    return user


@router.post("/login")
def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    check_rate_limit(request, "login", 10)

    user = db.scalar(
        select(User).where(User.username == data.username)
    )

    if user is None or not verify_password(
        data.password, user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    # Invalidate previous unused OTPs.
    previous = db.scalars(
        select(LoginOTP).where(
            LoginOTP.user_id == user.id,
            LoginOTP.used_at.is_(None),
        )
    ).all()

    now = utc_now()

    for record in previous:
        record.used_at = now

    otp = generate_otp()

    record = LoginOTP(
        user_id=user.id,
        otp_hash=hash_otp(otp),
        expires_at=now + timedelta(minutes=5),
        attempts=0,
    )

    db.add(record)
    db.commit()

    try:
        send_alert_email(
            user.email,
            "Nimbus Freight - Admin Login OTP",
            (
                f"Your Nimbus Freight login code is: {otp}\n\n"
                "This code expires in 5 minutes.\n"
                "Do not share this code."
            ),
        )
    except Exception:
        record.used_at = utc_now()
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="Unable to send OTP email. Please try later.",
        )

    return {"message": "OTP sent to the registered admin email"}


@router.post("/verify-otp")
def verify_login_otp(
    data: OTPRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    check_rate_limit(request, "otp", 15)

    user = db.scalar(
        select(User).where(User.username == data.username)
    )

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid OTP")

    record = db.scalar(
        select(LoginOTP)
        .where(
            LoginOTP.user_id == user.id,
            LoginOTP.used_at.is_(None),
        )
        .order_by(LoginOTP.id.desc())
        .limit(1)
    )

    now = utc_now()

    if record is None or record.expires_at <= now:
        raise HTTPException(
            status_code=401,
            detail="OTP expired or unavailable",
        )

    if record.attempts >= 3:
        raise HTTPException(
            status_code=429,
            detail="OTP attempt limit reached",
        )

    if not re.fullmatch(r"\d{6}", data.otp) or not verify_otp(
        data.otp, record.otp_hash
    ):
        record.attempts += 1

        if record.attempts >= 3:
            record.used_at = now

        db.commit()

        raise HTTPException(status_code=401, detail="Invalid OTP")

    record.used_at = now
    db.commit()

    return {
        "access_token": create_session(user.id),
        "token_type": "bearer",
        "expires_in": 8 * 60 * 60,
    }


@router.get("/me")
def get_me(user: User = Depends(get_current_admin)):
    return {
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }
