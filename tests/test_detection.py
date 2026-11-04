
from datetime import datetime, timedelta

from backend.engine.detection import detect_truck_incidents


def make_readings(temperatures, interval=5):
    start = datetime(2026, 7, 20, 8, 0)

    return [
        {
            "timestamp": start + timedelta(minutes=i * interval),
            "temperature_c": temp,
        }
        for i, temp in enumerate(temperatures)
    ]


def critical_incidents(incidents):
    return [
        incident for incident in incidents
        if incident["type"] == "CONFIRMED_VIOLATION"
    ]


def test_sustained_violation():
    readings = make_readings([8.5, 9.0, 9.2, 9.4, 9.1, 8.8])
    incidents = detect_truck_incidents("T-01", readings)

    critical = critical_incidents(incidents)

    assert len(critical) == 1
    assert critical[0]["duration_minutes"] == 20


def test_short_spike_ignored():
    readings = make_readings([6.0, 8.9, 6.5, 6.0])
    incidents = detect_truck_incidents("T-02", readings)

    assert len(critical_incidents(incidents)) == 0


def test_gap_breaks_violation():
    readings = make_readings([8.5, 9.0, 9.2, 9.4, 9.5])
    readings[3]["timestamp"] += timedelta(minutes=10)
    readings[4]["timestamp"] += timedelta(minutes=10)

    incidents = detect_truck_incidents("T-04", readings)

    assert len(critical_incidents(incidents)) == 0


def test_no_duplicate_critical_alert():
    readings = make_readings([8.5, 9.0, 9.2, 9.4, 9.5, 9.6, 9.7])
    incidents = detect_truck_incidents("T-01", readings)

    assert len(critical_incidents(incidents)) == 1


def test_recovery_allows_new_incident():
    readings = make_readings(
        [8.5, 9.0, 9.2, 9.4, 9.5, 7.0,
         8.5, 9.0, 9.2, 9.4, 9.5]
    )

    incidents = detect_truck_incidents("T-01", readings)

    assert len(critical_incidents(incidents)) == 2
