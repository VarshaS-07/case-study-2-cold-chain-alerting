
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path


DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "starter_kit"
    / "data"
    / "sensor_readings.json"
)

MAX_GAP_MINUTES = 7


def load_readings(file_path=DATA_PATH):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict) or not isinstance(data.get("readings"), list):
        raise ValueError("JSON must contain a 'readings' list")

    return data["readings"]


def validate_reading(reading):
    if not isinstance(reading, dict):
        raise ValueError("Reading must be an object")

    required = ["truck_id", "timestamp", "temperature_c"]

    for field in required:
        if field not in reading:
            raise ValueError(f"Missing field: {field}")

    truck_id = reading["truck_id"]
    if not isinstance(truck_id, str) or not truck_id.strip():
        raise ValueError("Invalid truck ID")

    try:
        timestamp = datetime.fromisoformat(reading["timestamp"])
    except (TypeError, ValueError):
        raise ValueError("Invalid timestamp") from None

    if timestamp.tzinfo is not None:
        raise ValueError("Expected timestamp without timezone")

    temperature = reading["temperature_c"]
    if (
        isinstance(temperature, bool)
        or not isinstance(temperature, (int, float))
        or not math.isfinite(temperature)
    ):
        raise ValueError("Invalid temperature")

    humidity = reading.get("humidity_pct")

    if humidity is not None:
        if (
            isinstance(humidity, bool)
            or not isinstance(humidity, (int, float))
            or not math.isfinite(humidity)
            or not 0 <= humidity <= 100
        ):
            raise ValueError("Invalid humidity")

    return {
        "truck_id": truck_id.strip(),
        "timestamp": timestamp,
        "temperature_c": float(temperature),
        "humidity_pct": float(humidity) if humidity is not None else None,
    }


def preprocess_readings(raw_readings):
    grouped = defaultdict(list)
    seen = {}

    for raw in raw_readings:
        reading = validate_reading(raw)

        key = (reading["truck_id"], reading["timestamp"])

        if key in seen:
            if seen[key] != reading:
                raise ValueError(
                    f"Conflicting readings for {key[0]} at {key[1]}"
                )
            continue

        seen[key] = reading
        grouped[reading["truck_id"]].append(reading)

    for truck_id in grouped:
        grouped[truck_id].sort(key=lambda item: item["timestamp"])

    return dict(sorted(grouped.items()))


def find_data_gaps(grouped_readings, max_gap_minutes=MAX_GAP_MINUTES):
    gaps = []

    for truck_id, readings in grouped_readings.items():
        for previous, current in zip(readings, readings[1:]):
            duration = (
                current["timestamp"] - previous["timestamp"]
            ).total_seconds() / 60

            if duration > max_gap_minutes:
                gaps.append({
                    "truck_id": truck_id,
                    "start_time": previous["timestamp"],
                    "end_time": current["timestamp"],
                    "gap_minutes": duration,
                })

    return gaps


def prepare_dataset(file_path=DATA_PATH):
    raw_readings = load_readings(file_path)
    grouped_readings = preprocess_readings(raw_readings)
    gaps = find_data_gaps(grouped_readings)

    return grouped_readings, gaps
