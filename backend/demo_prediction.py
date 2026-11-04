from backend.engine.preprocessing import preprocess_readings
from backend.engine.detection import detect_all_incidents


def main():
    # Synthetic readings for demonstration only.
    # This data is NOT part of the original case-study dataset.
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

    print("\n=== PREDICTIVE WARNING DEMO ===")
    print("Scenario: Temperature rising toward 8°C")
    print("Truck: DEMO-01")
    print("Readings: 5.0°C → 6.0°C → 7.0°C\n")

    if not incidents:
        print("No warning generated.")
        return

    for incident in incidents:
        print("Alert Type:", incident["type"])
        print("Truck:", incident["truck_id"])
        print("Detected At:", incident["detected_at"])
        print("Temperature:", incident["temperature_c"], "°C")
        print("Reason:", incident["reason"])
        print("Warming Rate:", incident["warming_rate"], "°C/min")
        print("ETA:", incident["eta_minutes"], "minutes")


if __name__ == "__main__":
    main()