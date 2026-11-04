
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from backend.auth.routes import get_current_admin
from backend.database import get_db
from backend.models import Truck, SensorReading, Incident,Notification
from backend.engine.preprocessing import find_data_gaps
from backend.engine.preprocessing import preprocess_readings
from backend.engine.detection import detect_all_incidents

# router = APIRouter(prefix="/api", tags=["Cold Chain"])

router = APIRouter(
    prefix="/api",
    tags=["Cold Chain"],
    dependencies=[Depends(get_current_admin)],
)
@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    total_trucks = db.scalar(
        select(func.count()).select_from(Truck)
    )

    total_readings = db.scalar(
        select(func.count()).select_from(SensorReading)
    )

    incidents = db.scalars(select(Incident)).all()

    confirmed = sum(
        i.type == "CONFIRMED_VIOLATION"
        for i in incidents
    )

    warnings = sum(
        i.type == "PREDICTIVE_WARNING"
        for i in incidents
    )

    return {
        "total_trucks": total_trucks,
        "total_readings": total_readings,
        "total_incidents": len(incidents),
        "confirmed_violations": confirmed,
        "predictive_warnings": warnings,
    }


@router.get("/trucks")
def get_trucks(db: Session = Depends(get_db)):
    trucks = db.scalars(
        select(Truck).order_by(Truck.truck_id)
    ).all()

    result = []

    for truck in trucks:
        latest = db.scalar(
            select(SensorReading)
            .where(SensorReading.truck_id == truck.truck_id)
            .order_by(SensorReading.timestamp.desc())
            .limit(1)
        )

        if latest is None:
            status = "NO_DATA"
        elif latest.temperature_c > truck.threshold_c:
            status = "ABOVE_THRESHOLD"
        else:
            status = "NORMAL"

        result.append({
            "truck_id": truck.truck_id,
            "threshold_c": truck.threshold_c,
            "latest_temperature_c": (
                latest.temperature_c if latest else None
            ),
            "latest_humidity_pct": (
                latest.humidity_pct if latest else None
            ),
            "last_reading_at": (
                latest.timestamp.isoformat() if latest else None
            ),
            "status": status,
        })

    return result


@router.get("/trucks/{truck_id}/readings")
def get_truck_readings(
    truck_id: str,
    db: Session = Depends(get_db)
):
    truck = db.get(Truck, truck_id)

    if truck is None:
        raise HTTPException(
            status_code=404,
            detail="Truck not found"
        )

    readings = db.scalars(
        select(SensorReading)
        .where(SensorReading.truck_id == truck_id)
        .order_by(SensorReading.timestamp)
    ).all()

    return {
        "truck_id": truck_id,
        "threshold_c": truck.threshold_c,
        "readings": [
            {
                "timestamp": r.timestamp.isoformat(),
                "temperature_c": r.temperature_c,
                "humidity_pct": r.humidity_pct,
            }
            for r in readings
        ],
    }


@router.get("/incidents")
def get_incidents(db: Session = Depends(get_db)):
    incidents = db.scalars(
        select(Incident).order_by(
            Incident.detected_at.desc(),
            Incident.id.desc()
        )
    ).all()

    return [
        {
            "id": i.id,
            "incident_key": i.incident_key,
            "truck_id": i.truck_id,
            "type": i.type,
            "status": i.status,
            "start_time": i.start_time.isoformat(),
            "detected_at": (
                i.detected_at.isoformat()
                if i.detected_at else None
            ),
            "end_time": (
                i.end_time.isoformat()
                if i.end_time else None
            ),
            "reason": i.reason,
        }
        for i in incidents
    ]


@router.get("/gaps")
def get_gaps(db: Session = Depends(get_db)):
    readings = db.scalars(
        select(SensorReading).order_by(
            SensorReading.truck_id,
            SensorReading.timestamp
        )
    ).all()

    grouped = defaultdict(list)

    for reading in readings:
        grouped[reading.truck_id].append({
            "timestamp": reading.timestamp,
            "temperature_c": reading.temperature_c,
        })

    gaps = find_data_gaps(grouped)

    return [
        {
            "truck_id": gap["truck_id"],
            "start_time": gap["start_time"].isoformat(),
            "end_time": gap["end_time"].isoformat(),
            "gap_minutes": gap["gap_minutes"],
        }
        for gap in gaps
    ]



@router.get("/notifications")
def get_notifications(db: Session = Depends(get_db)):
    notifications = db.scalars(
        select(Notification).order_by(Notification.id.desc())
    ).all()

    return [
        {
            "id": n.id,
            "incident_id": n.incident_id,
            "channel": n.channel,
            "recipient": n.recipient,
            "status": n.status,
            "attempt_count": n.attempt_count,
            "sent_at": (
                n.sent_at.isoformat() if n.sent_at else None
            ),
        }
        for n in notifications
    ]
@router.get("/demo/predictive-warning")
def run_predictive_warning_demo():
    """
    Run a synthetic predictive-warning scenario.

    This does not modify the database or send notifications.
    """

    demo_readings = [
        {
            "truck_id": "DEMO-01",
            "timestamp": "2026-07-20T09:00:00",
            "temperature_c": 5.0,
            "humidity_pct": 60,
        },
        {
            "truck_id": "DEMO-01",
            "timestamp": "2026-07-20T09:05:00",
            "temperature_c": 6.0,
            "humidity_pct": 61,
        },
        {
            "truck_id": "DEMO-01",
            "timestamp": "2026-07-20T09:10:00",
            "temperature_c": 7.0,
            "humidity_pct": 62,
        },
    ]

    grouped = preprocess_readings(demo_readings)
    incidents = detect_all_incidents(grouped)

    return {
        "scenario": "Synthetic Predictive Warning Demo",
        "is_demo": True,
        "truck_id": "DEMO-01",
        "threshold_c": 8.0,
        "readings": [
            {
                **reading,
                "timestamp": reading["timestamp"].isoformat(),
            }
            for reading in grouped["DEMO-01"]
        ],
        "incidents": [
            {
                **incident,
                "start_time": incident["start_time"].isoformat(),
                "detected_at": incident["detected_at"].isoformat(),
            }
            for incident in incidents
        ],
    }