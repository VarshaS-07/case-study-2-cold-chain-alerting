
from datetime import datetime

import pytest

from backend.engine.preprocessing import (
    load_readings,
    preprocess_readings,
    find_data_gaps,
    prepare_dataset,
    validate_reading,
)


def make_reading(truck_id, timestamp, temperature):
    return {
        "truck_id": truck_id,
        "timestamp": timestamp,
        "temperature_c": temperature,
        "humidity_pct": 55,
    }


def test_load_dataset():
    readings = load_readings()
    assert len(readings) == 54


def test_grouping():
    grouped, _ = prepare_dataset()

    assert len(grouped) == 5
    assert set(grouped) == {
        "T-01", "T-02", "T-03", "T-04", "T-05"
    }


def test_sorting():
    grouped, _ = prepare_dataset()

    for readings in grouped.values():
        timestamps = [item["timestamp"] for item in readings]
        assert timestamps == sorted(timestamps)


def test_exact_duplicate_removed():
    reading = make_reading(
        "T-01", "2026-07-20T08:00:00", 6.5
    )

    grouped = preprocess_readings([reading, reading.copy()])

    assert len(grouped["T-01"]) == 1


def test_conflicting_duplicate_rejected():
    first = make_reading(
        "T-01", "2026-07-20T08:00:00", 6.5
    )
    second = make_reading(
        "T-01", "2026-07-20T08:00:00", 9.0
    )

    with pytest.raises(ValueError, match="Conflicting"):
        preprocess_readings([first, second])


def test_invalid_temperature():
    reading = make_reading(
        "T-01", "2026-07-20T08:00:00", float("nan")
    )

    with pytest.raises(ValueError, match="temperature"):
        validate_reading(reading)


def test_gap_detection():
    readings = [
        make_reading("T-01", "2026-07-20T08:00:00", 7.0),
        make_reading("T-01", "2026-07-20T08:10:00", 8.5),
    ]

    grouped = preprocess_readings(readings)
    gaps = find_data_gaps(grouped)

    assert len(gaps) == 1
    assert gaps[0]["gap_minutes"] == 10


def test_actual_dataset_gap():
    _, gaps = prepare_dataset()

    assert len(gaps) == 1
    assert gaps[0]["truck_id"] == "T-04"
    assert gaps[0]["start_time"] == datetime(2026, 7, 20, 8, 30)
    assert gaps[0]["end_time"] == datetime(2026, 7, 20, 8, 40)
