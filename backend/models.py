
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, DateTime,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship

from backend.database import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(30), default="admin", nullable=False)


class LoginOTP(Base):
    __tablename__ = "login_otps"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    otp_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    attempts = Column(Integer, default=0, nullable=False)

    user = relationship("User")


class Truck(Base):
    __tablename__ = "trucks"

    truck_id = Column(String(30), primary_key=True)
    threshold_c = Column(Float, default=8.0, nullable=False)

    readings = relationship(
        "SensorReading", back_populates="truck"
    )
    incidents = relationship(
        "Incident", back_populates="truck"
    )


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True)
    truck_id = Column(
        String(30),
        ForeignKey("trucks.truck_id"),
        nullable=False
    )
    timestamp = Column(DateTime, nullable=False)
    temperature_c = Column(Float, nullable=False)
    humidity_pct = Column(Float, nullable=True)

    truck = relationship(
        "Truck", back_populates="readings"
    )

    __table_args__ = (
        UniqueConstraint(
            "truck_id", "timestamp",
            name="uq_truck_timestamp"
        ),
        Index(
            "idx_readings_truck_time",
            "truck_id", "timestamp"
        ),
    )


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True)
    incident_key = Column(
        String(150), unique=True, nullable=False
    )
    truck_id = Column(
        String(30),
        ForeignKey("trucks.truck_id"),
        nullable=False
    )
    type = Column(String(30), nullable=False)
    start_time = Column(DateTime, nullable=False)
    detected_at = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(30), nullable=False)
    reason = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=utc_now)

    truck = relationship(
        "Truck", back_populates="incidents"
    )
    notifications = relationship(
        "Notification", back_populates="incident"
    )


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    incident_id = Column(
        Integer,
        ForeignKey("incidents.id"),
        nullable=False
    )
    channel = Column(String(20), nullable=False)
    recipient = Column(String(255), nullable=False)
    status = Column(
        String(30), default="PENDING", nullable=False
    )
    attempt_count = Column(
        Integer, default=0, nullable=False
    )
    sent_at = Column(DateTime, nullable=True)
    provider_reference = Column(String(255), nullable=True)
    last_error = Column(String(500), nullable=True)

    incident = relationship(
        "Incident", back_populates="notifications"
    )

    __table_args__ = (
        UniqueConstraint(
            "incident_id", "channel", "recipient",
            name="uq_incident_notification"
        ),
    )
