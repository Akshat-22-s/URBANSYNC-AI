"""Stochastic waste fill rate prediction model.

Predicts bin fill levels using:
- Poisson accumulation model
- Historical collection patterns
- Day-of-week and time-of-day coefficients
"""

from __future__ import annotations

from typing import Any
import numpy as np
from scipy.stats import poisson


def day_of_week_coefficient(day: int) -> float:
    """Return collection pattern multiplier for the given day of the week.

    Args:
        day: Day index (0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday,
             4=Friday, 5=Saturday, 6=Sunday).

    Returns:
        Multiplier float:
        - Mon: 1.0
        - Tue: 0.9
        - Wed: 0.85
        - Thu: 0.9
        - Fri: 1.1
        - Sat: 1.3
        - Sun: 0.7
    """
    normalized_day = int(day) % 7
    coefficients = {
        0: 1.0,   # Monday
        1: 0.9,   # Tuesday
        2: 0.85,  # Wednesday
        3: 0.9,   # Thursday
        4: 1.1,   # Friday
        5: 1.3,   # Saturday
        6: 0.7,   # Sunday
    }
    return coefficients[normalized_day]


def time_of_day_coefficient(hour: int) -> float:
    """Return activity multiplier for the given hour of the day.

    Args:
        hour: Hour of day (0 to 23).

    Returns:
        Multiplier float:
        - Peak morning (8 - 10 am): 1.4
        - Lunch rush (12 - 2 pm): 1.2
        - Evening peak (5 - 7 pm): 1.3
        - Night hours (10 pm - 6 am): 0.4
        - Default / Normal hours: 1.0
    """
    normalized_hour = int(hour) % 24

    if 8 <= normalized_hour <= 10:
        return 1.4
    if 12 <= normalized_hour <= 14:
        return 1.2
    if 17 <= normalized_hour <= 19:
        return 1.3
    if normalized_hour >= 22 or normalized_hour < 6:
        return 0.4
    return 1.0


def poisson_fill_rate(
    current_pct: float,
    hours_since_collection: float,
    lambda_rate: float = 2.5,
) -> float:
    """Calculate expected bin fill percentage using a Poisson accumulation model.

    Args:
        current_pct: Starting fill percentage (0.0 to 100.0).
        hours_since_collection: Elapsed duration in hours.
        lambda_rate: Base fill accumulation rate in percentage points per hour.

    Returns:
        Expected fill percentage bounded between 0.0 and 100.0.
    """
    if hours_since_collection <= 0:
        return float(np.clip(current_pct, 0.0, 100.0))

    # Mean accumulation for the interval
    mu = float(max(0.0, lambda_rate * hours_since_collection))
    if mu <= 0.0:
        return float(np.clip(current_pct, 0.0, 100.0))

    # Expected increment from Poisson distribution mean
    expected_increment = float(poisson.mean(mu))
    predicted = current_pct + expected_increment

    return float(np.clip(predicted, 0.0, 100.0))


def predict_fill_rate(
    current_pct: float,
    hours_ahead: float,
    day: int = 0,
    hour: int = 12,
    base_lambda: float = 2.5,
) -> dict[str, Any]:
    """Predict future fill rate and estimate critical fill thresholds.

    Accounts for dynamic day-of-week and time-of-day fluctuations over the horizon.

    Args:
        current_pct: Current fill percentage of the bin (0.0 to 100.0).
        hours_ahead: Prediction window duration in hours.
        day: Current day index (0=Monday ... 6=Sunday).
        hour: Current hour of the day (0 to 23).
        base_lambda: Baseline hourly accumulation rate percentage.

    Returns:
        Dictionary containing:
        - predicted_pct: Estimated fill percentage after hours_ahead
        - time_to_75_pct_hours: Hours until bin reaches 75% fill (0.0 if already >= 75%)
        - time_to_full_hours: Hours until bin reaches 100% fill (0.0 if already full)
        - should_collect_soon: Boolean indicating if collection should be scheduled
    """
    current_val = float(np.clip(current_pct, 0.0, 100.0))

    # Simulate dynamic accumulation with fine-grained 0.5 hour integration steps
    step_size = 0.5
    total_steps = int(math_ceil_steps(hours_ahead, step_size))

    running_fill = current_val
    for step in range(total_steps):
        elapsed = step * step_size
        remaining = hours_ahead - elapsed
        delta_t = min(step_size, remaining)
        if delta_t <= 0:
            break

        curr_h = int((hour + elapsed)) % 24
        curr_d = int((day + (hour + elapsed) // 24)) % 7

        dow_mult = day_of_week_coefficient(curr_d)
        tod_mult = time_of_day_coefficient(curr_h)
        eff_lambda = base_lambda * dow_mult * tod_mult

        mu = eff_lambda * delta_t
        increment = float(poisson.mean(mu))
        running_fill = min(100.0, running_fill + increment)

    predicted_pct = round(running_fill, 2)

    # Calculate time to reach 75% fill
    time_to_75 = 0.0 if current_val >= 75.0 else None
    time_to_full = 0.0 if current_val >= 100.0 else None

    # Project forward up to 168 hours (1 week) to find threshold crossing times
    search_limit_hours = 168.0
    search_step = 0.25
    steps = int(search_limit_hours / search_step)

    sim_fill = current_val
    for s in range(1, steps + 1):
        t = s * search_step
        curr_h = int((hour + t)) % 24
        curr_d = int((day + (hour + t) // 24)) % 7

        eff_lambda = base_lambda * day_of_week_coefficient(curr_d) * time_of_day_coefficient(curr_h)
        sim_fill += eff_lambda * search_step

        if time_to_75 is None and sim_fill >= 75.0:
            time_to_75 = round(t, 2)

        if time_to_full is None and sim_fill >= 100.0:
            time_to_full = round(t, 2)
            break

    # If thresholds not reached within 1 week, set to default estimate
    if time_to_75 is None:
        remaining_to_75 = max(0.0, 75.0 - current_val)
        time_to_75 = round(remaining_to_75 / base_lambda, 2) if base_lambda > 0 else 168.0

    if time_to_full is None:
        remaining_to_full = max(0.0, 100.0 - current_val)
        time_to_full = round(remaining_to_full / base_lambda, 2) if base_lambda > 0 else 168.0

    should_collect_soon = bool(
        predicted_pct >= 75.0 or time_to_75 <= 4.0 or current_val >= 75.0
    )

    return {
        "predicted_pct": predicted_pct,
        "time_to_75_pct_hours": time_to_75,
        "time_to_full_hours": time_to_full,
        "should_collect_soon": should_collect_soon,
    }


def math_ceil_steps(total_hours: float, step_size: float) -> int:
    """Helper to calculate ceiling step count for discretization."""
    if total_hours <= 0:
        return 0
    return int(np.ceil(total_hours / step_size))


def simulate_bin_fills(
    bins: list[dict[str, Any]],
    hours: int = 24,
    tick_hours: float = 1.0,
) -> list[dict[str, Any]]:
    """Simulate fill progression for a fleet of waste bins over a given time horizon.

    Args:
        bins: List of bin dicts with keys 'id', 'current_pct' (or 'fill_pct'),
              and optional 'base_lambda', 'start_day', 'start_hour'.
        hours: Total simulation duration in hours.
        tick_hours: Time resolution per tick in hours.

    Returns:
        List of dictionaries containing each bin's simulation trajectory,
        critical threshold alerts, and estimated overflow timestamps.
    """
    results: list[dict[str, Any]] = []
    num_ticks = max(1, int(round(hours / tick_hours)))

    for b in bins:
        bin_id = b.get("id", "unknown")
        start_fill = b.get("current_pct")
        if start_fill is None:
            start_fill = b.get("fill_pct", 0.0)
        start_fill = float(np.clip(start_fill, 0.0, 100.0))

        base_lambda = float(b.get("base_lambda", 2.5))
        start_day = int(b.get("start_day", 0))
        start_hour = int(b.get("start_hour", 8))

        timeline: list[dict[str, Any]] = [
            {
                "tick": 0,
                "elapsed_hours": 0.0,
                "fill_pct": round(start_fill, 2),
                "status": "normal" if start_fill < 75.0 else "urgent",
            }
        ]

        current_level = start_fill
        threshold_75_reached_at: float | None = 0.0 if start_fill >= 75.0 else None
        overflow_reached_at: float | None = 0.0 if start_fill >= 100.0 else None

        for step in range(1, num_ticks + 1):
            elapsed = step * tick_hours
            step_hour = int((start_hour + elapsed)) % 24
            step_day = int((start_day + (start_hour + elapsed) // 24)) % 7

            eff_lambda = (
                base_lambda
                * day_of_week_coefficient(step_day)
                * time_of_day_coefficient(step_hour)
            )

            mu = eff_lambda * tick_hours
            increment = float(poisson.mean(mu))
            current_level = min(100.0, current_level + increment)

            status = "normal"
            if current_level >= 100.0:
                status = "overflow"
            elif current_level >= 75.0:
                status = "urgent"

            timeline.append(
                {
                    "tick": step,
                    "elapsed_hours": round(elapsed, 2),
                    "fill_pct": round(current_level, 2),
                    "status": status,
                }
            )

            if threshold_75_reached_at is None and current_level >= 75.0:
                threshold_75_reached_at = round(elapsed, 2)
            if overflow_reached_at is None and current_level >= 100.0:
                overflow_reached_at = round(elapsed, 2)

        results.append(
            {
                "bin_id": bin_id,
                "initial_fill_pct": round(start_fill, 2),
                "final_fill_pct": round(current_level, 2),
                "threshold_75_reached_at_hours": threshold_75_reached_at,
                "overflow_reached_at_hours": overflow_reached_at,
                "is_critical": current_level >= 75.0,
                "timeline": timeline,
            }
        )

    return results
