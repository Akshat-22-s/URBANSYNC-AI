"""
UrbanSync AI - SILN Departure Intelligence Calculator
=====================================================
Implements the SILN (Spatially-Informed Latency-Neutral) departure calculation formula:
- T_arrive = T_event - 5 minutes
- B_dynamic = B_parking + B_toll + B_weather
- T_depart = T_arrive - D_transit - B_dynamic
- Urgency categorization based on time remaining until T_depart:
    * > 30 min: PLENTY_OF_TIME
    * 15-30 min: LEAVE_SOON
    * 5-15 min: LEAVE_NOW
    * < 5 min: LATE
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union


def calculate_dynamic_buffer(
    parking_min: float = 5.0,
    toll_min: float = 0.0,
    weather_min: float = 0.0
) -> Dict[str, float]:
    """
    Calculate dynamic buffer components for parking search, toll plaza waits, and weather degradation.

    Parameters
    ----------
    parking_min : float, optional
        Estimated time in minutes to locate parking at destination (default is 5.0).
    toll_min : float, optional
        Estimated cumulative queue delay at toll booths in minutes (default is 0.0).
    weather_min : float, optional
        Estimated transit buffer for precipitation/fog/road conditions in minutes (default is 0.0).

    Returns
    -------
    dict
        Dictionary containing breakdown and total dynamic buffer:
        {
            "parking_min": float,
            "toll_min": float,
            "weather_min": float,
            "total": float
        }
    """
    parking = max(0.0, float(parking_min))
    toll = max(0.0, float(toll_min))
    weather = max(0.0, float(weather_min))
    total = parking + toll + weather

    return {
        "parking_min": round(parking, 2),
        "toll_min": round(toll, 2),
        "weather_min": round(weather, 2),
        "total": round(total, 2)
    }


def calculate_departure(
    event_time: Union[datetime, str],
    transit_duration_min: float,
    parking_min: float = 5.0,
    toll_min: float = 0.0,
    weather_min: float = 0.0,
    current_time: Optional[Union[datetime, str]] = None
) -> Dict[str, Any]:
    """
    Execute full SILN departure intelligence calculation.

    Parameters
    ----------
    event_time : datetime or str
        Scheduled start time of the target appointment/event (ISO string or datetime).
    transit_duration_min : float
        Estimated travel time along primary route in minutes.
    parking_min : float, optional
        Buffer time in minutes allocated for parking (default is 5.0).
    toll_min : float, optional
        Buffer time in minutes allocated for toll delays (default is 0.0).
    weather_min : float, optional
        Buffer time in minutes allocated for weather friction (default is 0.0).
    current_time : datetime or str, optional
        Evaluation timestamp (defaults to current system time with matching timezone).

    Returns
    -------
    dict
        Full SILN calculation result:
        {
            "event_time": datetime,
            "arrive_by": datetime,
            "transit_duration_min": float,
            "dynamic_buffer": dict,
            "depart_at": datetime,
            "urgency": str,
            "lead_time_min": float
        }
    """
    # Parse event_time if string
    if isinstance(event_time, str):
        event_time_dt = datetime.fromisoformat(event_time)
    else:
        event_time_dt = event_time

    # Determine reference current_time
    if current_time is None:
        if event_time_dt.tzinfo is not None:
            now_dt = datetime.now(event_time_dt.tzinfo)
        else:
            now_dt = datetime.now()
    elif isinstance(current_time, str):
        now_dt = datetime.fromisoformat(current_time)
    else:
        now_dt = current_time

    # Ensure timezone consistency between now_dt and event_time_dt
    if event_time_dt.tzinfo is not None and now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=event_time_dt.tzinfo)
    elif event_time_dt.tzinfo is None and now_dt.tzinfo is not None:
        event_time_dt = event_time_dt.replace(tzinfo=now_dt.tzinfo)

    transit_min = max(0.0, float(transit_duration_min))

    # T_arrive = T_event - 5 minutes
    arrive_by = event_time_dt - timedelta(minutes=5)

    # B_dynamic = B_parking + B_toll + B_weather
    dynamic_buffer = calculate_dynamic_buffer(
        parking_min=parking_min,
        toll_min=toll_min,
        weather_min=weather_min
    )
    total_buffer_min = dynamic_buffer["total"]

    # T_depart = T_arrive - D_transit - B_dynamic
    total_travel_and_buffer_min = transit_min + total_buffer_min
    depart_at = arrive_by - timedelta(minutes=total_travel_and_buffer_min)

    # Time remaining until T_depart
    lead_time_seconds = (depart_at - now_dt).total_seconds()
    lead_time_min = lead_time_seconds / 60.0

    # Urgency classification
    if lead_time_min > 30.0:
        urgency = "PLENTY_OF_TIME"
    elif lead_time_min >= 15.0:
        urgency = "LEAVE_SOON"
    elif lead_time_min >= 5.0:
        urgency = "LEAVE_NOW"
    else:
        urgency = "LATE"

    return {
        "event_time": event_time_dt,
        "arrive_by": arrive_by,
        "transit_duration_min": round(transit_min, 2),
        "dynamic_buffer": dynamic_buffer,
        "depart_at": depart_at,
        "urgency": urgency,
        "lead_time_min": round(lead_time_min, 2)
    }


def check_reroute(
    current_delay_min: float,
    current_eta_min: float,
    detour_eta_min: float
) -> Dict[str, Any]:
    """
    Evaluate whether a vehicle should reroute based on congestion delay and detour ETA delta.

    Reroute Rule:
    If current_delay > 4.0 min AND (current_eta - detour_eta) >= 3.0 min:
        Recommend reroute.

    Parameters
    ----------
    current_delay_min : float
        Current accumulated delay along the active route in minutes.
    current_eta_min : float
        Projected remaining travel time along current route in minutes.
    detour_eta_min : float
        Projected travel time along alternate detour route in minutes.

    Returns
    -------
    dict
        {
            "should_reroute": bool,
            "time_saved_min": float,
            "reason": str
        }
    """
    delay = float(current_delay_min)
    curr_eta = float(current_eta_min)
    alt_eta = float(detour_eta_min)

    time_saved_min = curr_eta - alt_eta

    if delay > 4.0 and time_saved_min >= 3.0:
        should_reroute = True
        reason = (
            f"Reroute recommended: current delay of {delay:.1f} min exceeds threshold (>4 min) "
            f"and detour saves {time_saved_min:.1f} min (threshold >= 3 min)."
        )
    elif delay <= 4.0:
        should_reroute = False
        reason = (
            f"Current route delay ({delay:.1f} min) does not exceed threshold (>4 min). "
            f"Reroute not justified."
        )
    else:
        should_reroute = False
        reason = (
            f"Current route delay is {delay:.1f} min, but detour only saves {max(0.0, time_saved_min):.1f} min "
            f"(threshold requires at least 3.0 min saved)."
        )

    return {
        "should_reroute": should_reroute,
        "time_saved_min": round(max(0.0, time_saved_min), 2),
        "reason": reason
    }
