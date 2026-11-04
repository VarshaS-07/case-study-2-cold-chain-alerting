
import os

from sqlalchemy import select
from dotenv import load_dotenv

from backend.database import SessionLocal, init_db
from backend.models import User
from backend.auth.security import hash_password

load_dotenv()


def main():
    username = os.getenv("ADMIN_USERNAME")
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")

    if not all([username, email, password]):
        raise ValueError("Admin credentials missing from .env")

    if len(password) < 12:
        raise ValueError("ADMIN_PASSWORD must have at least 12 characters")

    init_db()

    with SessionLocal() as db:
        existing = db.scalar(select(User).limit(1))

        if existing:
            print("Admin already exists. No new user created.")
            return

        db.add(User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role="admin",
        ))
        db.commit()

    print("Admin account created successfully.")


if __name__ == "__main__":
    main()
