
THRESHOLD_C = 8.0
PREDICTION_WINDOW_MINUTES = 10
MAX_GAP_MINUTES = 7


def predict_threshold(readings, threshold=THRESHOLD_C):
    if len(readings) < 3:
        return None

    recent = readings[-3:]
    temperatures = [r["temperature_c"] for r in recent]

    # Prediction is only useful before crossing the threshold.
    if any(temp > threshold for temp in temperatures):
        return None

    # Require a consistently increasing temperature.
    if not (
        temperatures[0] < temperatures[1] < temperatures[2]
    ):
        return None

    for previous, current in zip(recent, recent[1:]):
        gap = (
            current["timestamp"] - previous["timestamp"]
        ).total_seconds() / 60

        if gap <= 0 or gap > MAX_GAP_MINUTES:
            return None

    duration = (
        recent[-1]["timestamp"] - recent[0]["timestamp"]
    ).total_seconds() / 60

    rate = (temperatures[-1] - temperatures[0]) / duration

    if rate <= 0:
        return None

    current_temp = temperatures[-1]
    eta = (threshold - current_temp) / rate

    if not 0 <= eta <= PREDICTION_WINDOW_MINUTES:
        return None

    return {
        "type": "PREDICTIVE_WARNING",
        "timestamp": recent[-1]["timestamp"],
        "temperature_c": current_temp,
        "warming_rate": round(rate, 3),
        "eta_minutes": round(eta, 2),
        "reason": (
            f"Temperature is rising at {rate:.2f} C/min. "
            f"Estimated threshold crossing in {eta:.1f} minutes."
        ),
    }
