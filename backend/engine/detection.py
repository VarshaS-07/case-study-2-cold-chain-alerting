
from backend.engine.prediction import predict_threshold


THRESHOLD_C = 8.0
SUSTAINED_MINUTES = 20
MAX_GAP_MINUTES = 7


def make_incident(truck_id, alert_type, start, detected, reason, **extra):
    return {
        "incident_key": (
            f"{truck_id}:{alert_type}:{start.isoformat()}"
        ),
        "truck_id": truck_id,
        "type": alert_type,
        "start_time": start,
        "detected_at": detected,
        "reason": reason,
        **extra,
    }


def detect_truck_incidents(truck_id, readings):
    incidents = []

    breach_start = None
    critical_sent = False
    warning_active = False

    for index, reading in enumerate(readings):
        current_time = reading["timestamp"]
        temperature = reading["temperature_c"]

        if index > 0:
            previous_time = readings[index - 1]["timestamp"]
            gap = (current_time - previous_time).total_seconds() / 60

            if gap > MAX_GAP_MINUTES:
                breach_start = None
                critical_sent = False
                warning_active = False

        if temperature > THRESHOLD_C:
            warning_active = False

            if breach_start is None:
                breach_start = current_time
                critical_sent = False

            duration = (
                current_time - breach_start
            ).total_seconds() / 60

            if duration >= SUSTAINED_MINUTES and not critical_sent:
                incidents.append(
                    make_incident(
                        truck_id,
                        "CONFIRMED_VIOLATION",
                        breach_start,
                        current_time,
                        (
                            f"Temperature remained above {THRESHOLD_C} C "
                            f"for {duration:.0f} minutes."
                        ),
                        temperature_c=temperature,
                        duration_minutes=duration,
                    )
                )
                critical_sent = True

        else:
            breach_start = None
            critical_sent = False

            prediction = predict_threshold(readings[:index + 1])

            if prediction is None:
                warning_active = False

            elif not warning_active:
                incidents.append(
                    make_incident(
                        truck_id,
                        "PREDICTIVE_WARNING",
                        current_time,
                        current_time,
                        prediction["reason"],
                        temperature_c=temperature,
                        warming_rate=prediction["warming_rate"],
                        eta_minutes=prediction["eta_minutes"],
                    )
                )
                warning_active = True

    return incidents


def detect_all_incidents(grouped_readings):
    incidents = []

    for truck_id, readings in grouped_readings.items():
        incidents.extend(detect_truck_incidents(truck_id, readings))

    return sorted(
        incidents,
        key=lambda incident: (
            incident["detected_at"],
            incident["truck_id"],
            incident["type"],
        ),
    )
