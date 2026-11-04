
import os
from datetime import datetime, timezone

from sqlalchemy import select

from backend.database import SessionLocal
from backend.models import Incident, Notification
from backend.notifications.email_sender import send_alert_email


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def prepare_notifications():
    recipient = os.getenv("ALERT_EMAIL")

    if not recipient:
        raise ValueError("ALERT_EMAIL is not configured")

    created = 0

    with SessionLocal() as db:
        incidents = db.scalars(select(Incident)).all()

        for incident in incidents:
            existing = db.scalar(
                select(Notification).where(
                    Notification.incident_id == incident.id,
                    Notification.channel == "EMAIL",
                    Notification.recipient == recipient,
                )
            )

            if existing:
                continue

            db.add(
                Notification(
                    incident_id=incident.id,
                    channel="EMAIL",
                    recipient=recipient,
                    status="PENDING",
                    attempt_count=0,
                )
            )
            created += 1

        db.commit()

    return created


def process_notifications(send=False):
    results = []

    with SessionLocal() as db:
        notifications = db.scalars(
            select(Notification).where(
                Notification.channel == "EMAIL",
                Notification.status.in_(["PENDING", "FAILED"]),
                Notification.attempt_count < 3,
            ).order_by(Notification.id)
        ).all()

        for notification in notifications:
            incident = db.get(Incident, notification.incident_id)

            subject = (
                f"[Nimbus Freight] {incident.type} - "
                f"{incident.truck_id}"
            )

            body = (
                f"Cold-Chain Alert\n\n"
                f"Truck: {incident.truck_id}\n"
                f"Type: {incident.type}\n"
                f"Started: {incident.start_time}\n"
                f"Detected: {incident.detected_at}\n"
                f"Reason: {incident.reason}\n\n"
                f"Please review the shipment."
            )

            if not send:
                results.append({
                    "truck_id": incident.truck_id,
                    "status": "DRY_RUN",
                    "recipient": notification.recipient,
                    "subject": subject,
                    "body": body,
                })
                continue

            # Commit the attempt before contacting SMTP.
            notification.status = "SENDING"
            notification.attempt_count += 1
            db.commit()

            try:
                send_alert_email(
                    notification.recipient,
                    subject,
                    body,
                )
                notification.status = "SENT"
                notification.sent_at = utc_now()
                notification.last_error = None

            except Exception as exc:
                notification.status = "FAILED"
                notification.last_error = str(exc)[:500]

            db.commit()

            results.append({
                "truck_id": incident.truck_id,
                "status": notification.status,
                "recipient": notification.recipient,
            })

    return results
