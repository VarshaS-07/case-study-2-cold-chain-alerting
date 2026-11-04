
from datetime import datetime, timedelta

from backend.engine.prediction import predict_threshold


def make_readings(temperatures, interval=5):
    start = datetime(2026, 7, 20, 8, 0)

    return [
        {
            "timestamp": start + timedelta(minutes=i * interval),
            "temperature_c": temp,
        }
        for i, temp in enumerate(temperatures)
    ]


def test_predictive_warning():
    readings = make_readings([6.0, 6.5, 7.0])
    result = predict_threshold(readings)

    assert result is not None
    assert result["type"] == "PREDICTIVE_WARNING"
    assert result["eta_minutes"] == 10


def test_no_warning_when_cooling():
    readings = make_readings([7.5, 7.0, 6.5])
    assert predict_threshold(readings) is None


def test_no_warning_after_threshold():
    readings = make_readings([7.0, 7.5, 8.5])
    assert predict_threshold(readings) is None


def test_no_warning_with_large_gap():
    readings = make_readings([6.0, 6.5, 7.0], interval=10)
    assert predict_threshold(readings) is None


def test_no_warning_with_insufficient_readings():
    readings = make_readings([6.0, 7.0])
    assert predict_threshold(readings) is None
