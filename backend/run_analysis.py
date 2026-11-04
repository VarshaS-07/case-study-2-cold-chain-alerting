
from sqlalchemy import select

from backend.database import SessionLocal, init_db
from backend.models import Truck, SensorReading, Incident
from backend.engine.preprocessing import prepare_dataset
from backend.engine.detection import detect_all_incidents


def save_readings(db, grouped_readings):
    new_readings = 0

    for truck_id, readings in grouped_readings.items():
        truck = db.get(Truck, truck_id)

        if truck is None:
            db.add(Truck(truck_id=truck_id, threshold_c=8.0))
            db.flush()

        existing_times = set(
            db.scalars(
                select(SensorReading.timestamp).where(
                    SensorReading.truck_id == truck_id
                )
            ).all()
        )

        for reading in readings:
            if reading["timestamp"] in existing_times:
                continue

            db.add(
                SensorReading(
                    truck_id=truck_id,
                    timestamp=reading["timestamp"],
                    temperature_c=reading["temperature_c"],
                    humidity_pct=reading["humidity_pct"],
                )
            )
            new_readings += 1

    return new_readings


def save_incidents(db, incidents):
    new_incidents = 0

    existing_keys = set(
        db.scalars(select(Incident.incident_key)).all()
    )

    for incident in incidents:
        if incident["incident_key"] in existing_keys:
            continue

        db.add(
            Incident(
                incident_key=incident["incident_key"],
                truck_id=incident["truck_id"],
                type=incident["type"],
                start_time=incident["start_time"],
                # end_time=incident["detected_at"],
                detected_at=incident["detected_at"],
                end_time=None,
                status="DETECTED",
                reason=incident["reason"],
            )
        )

        existing_keys.add(incident["incident_key"])
        new_incidents += 1

    return new_incidents


def run_analysis():
    print("\nStarting cold-chain analysis...\n")

    init_db()

    grouped_readings, gaps = prepare_dataset()
    incidents = detect_all_incidents(grouped_readings)

    with SessionLocal() as db:
        try:
            new_readings = save_readings(db, grouped_readings)
            new_incidents = save_incidents(db, incidents)
            db.commit()
        except Exception:
            db.rollback()
            raise

    print("Analysis completed successfully.")
    print("-" * 45)
    print(f"Trucks analyzed       : {len(grouped_readings)}")
    print(f"Sensor readings       : {sum(len(v) for v in grouped_readings.values())}")
    print(f"Data gaps detected    : {len(gaps)}")
    print(f"Incidents detected    : {len(incidents)}")
    print(f"New readings saved    : {new_readings}")
    print(f"New incidents saved   : {new_incidents}")

    print("\nDetected incidents:")
    for incident in incidents:
        print(
            f"  {incident['truck_id']} | "
            f"{incident['type']} | "
            f"{incident['detected_at']} | "
            f"{incident['reason']}"
        )

    if gaps:
        print("\nData quality warnings:")
        for gap in gaps:
            print(
                f"  {gap['truck_id']}: "
                f"{gap['gap_minutes']:.0f}-minute gap "
                f"({gap['start_time']} to {gap['end_time']})"
            )


if __name__ == "__main__":
    run_analysis()
