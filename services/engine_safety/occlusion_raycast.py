"""CCTV volumetric cone occlusion raycasting.

Models CCTV cameras as conical frustums and checks if a target coordinate
is within the surveillance cone and not occluded by building geometries.

Cone parameters: radius=3, height=6, segments=16
Cone color: #06B6D4, opacity: 0.08
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

# Cone volumetric parameters
CONE_RADIUS = 3.0
CONE_HEIGHT = 6.0
CONE_SEGMENTS = 16
CONE_COLOR = "#06B6D4"
CONE_OPACITY = 0.08

# Earth coordinates conversion constants for Lucknow latitude (~26.85 deg N)
METERS_PER_DEG_LAT = 111139.0


@dataclass
class CCTVCamera:
    """Surveillance camera node with optical cone attributes."""

    camera_id: str
    lat: float
    lon: float
    altitude_m: float
    heading_deg: float  # Compass heading: 0=North, 90=East, 180=South, 270=West
    fov_deg: float      # Field of view in degrees (e.g., 60-90)
    range_m: float      # Maximum optical range in meters


@dataclass
class BuildingBlock:
    """Architectural block representing urban structures for shadow occlusion."""

    block_id: str
    center_lat: float
    center_lon: float
    width_m: float   # East-West dimension in meters
    depth_m: float   # North-South dimension in meters
    height_m: float  # Building height in meters


def _meters_per_deg_lon(lat: float) -> float:
    """Return meters per degree longitude at a given latitude."""
    return METERS_PER_DEG_LAT * math.cos(math.radians(lat))


def get_sample_cameras() -> list[CCTVCamera]:
    """Return at least 15 CCTV cameras placed around Lucknow landmarks."""
    return [
        # Hazratganj Hub
        CCTVCamera("CAM-HZG-01", 26.8467, 80.9462, altitude_m=8.0, heading_deg=45.0, fov_deg=85.0, range_m=120.0),
        CCTVCamera("CAM-HZG-02", 26.8475, 80.9455, altitude_m=7.0, heading_deg=180.0, fov_deg=75.0, range_m=100.0),
        CCTVCamera("CAM-HZG-03", 26.8458, 80.9470, altitude_m=6.5, heading_deg=315.0, fov_deg=90.0, range_m=110.0),

        # Aminabad Commercial Market
        CCTVCamera("CAM-AMN-01", 26.8520, 80.9220, altitude_m=8.5, heading_deg=90.0, fov_deg=80.0, range_m=115.0),
        CCTVCamera("CAM-AMN-02", 26.8512, 80.9215, altitude_m=6.0, heading_deg=0.0, fov_deg=75.0, range_m=95.0),

        # Charbagh Railway Junction
        CCTVCamera("CAM-CHB-01", 26.8580, 80.9215, altitude_m=9.0, heading_deg=135.0, fov_deg=95.0, range_m=140.0),
        CCTVCamera("CAM-CHB-02", 26.8572, 80.9230, altitude_m=7.5, heading_deg=270.0, fov_deg=80.0, range_m=105.0),

        # Gomti Nagar Corridor
        CCTVCamera("CAM-GMT-01", 26.8563, 80.9800, altitude_m=8.0, heading_deg=60.0, fov_deg=90.0, range_m=130.0),
        CCTVCamera("CAM-GMT-02", 26.8540, 80.9750, altitude_m=7.0, heading_deg=315.0, fov_deg=85.0, range_m=120.0),

        # Alambagh Terminal
        CCTVCamera("CAM-ALM-01", 26.8075, 80.9050, altitude_m=8.0, heading_deg=120.0, fov_deg=85.0, range_m=115.0),
        CCTVCamera("CAM-ALM-02", 26.8085, 80.9060, altitude_m=9.0, heading_deg=225.0, fov_deg=75.0, range_m=95.0),

        # Kaiserbagh Central
        CCTVCamera("CAM-KSB-01", 26.8450, 80.9380, altitude_m=7.5, heading_deg=30.0, fov_deg=85.0, range_m=110.0),

        # Indira Nagar
        CCTVCamera("CAM-IND-01", 26.8750, 80.9950, altitude_m=7.0, heading_deg=180.0, fov_deg=80.0, range_m=105.0),

        # Aliganj Kapoorthala
        CCTVCamera("CAM-ALG-01", 26.8870, 80.9380, altitude_m=7.5, heading_deg=90.0, fov_deg=85.0, range_m=115.0),

        # Mahanagar Gole Market
        CCTVCamera("CAM-MHN-01", 26.8720, 80.9330, altitude_m=7.0, heading_deg=270.0, fov_deg=75.0, range_m=100.0),

        # Husainabad Historical Zone
        CCTVCamera("CAM-HSN-01", 26.8690, 80.9200, altitude_m=10.0, heading_deg=150.0, fov_deg=90.0, range_m=150.0),

        # IT Crossing
        CCTVCamera("CAM-ITC-01", 26.8550, 80.9700, altitude_m=8.0, heading_deg=0.0, fov_deg=85.0, range_m=120.0),

        # Cantonment Sadar
        CCTVCamera("CAM-CNT-01", 26.8380, 80.9250, altitude_m=7.5, heading_deg=75.0, fov_deg=80.0, range_m=110.0),
    ]


def get_sample_buildings() -> list[BuildingBlock]:
    """Return at least 20 building blocks for shadow/occlusion geometry around Lucknow."""
    return [
        # Hazratganj Blocks
        BuildingBlock("BLD-HZG-01", 26.8469, 80.9460, width_m=35.0, depth_m=25.0, height_m=18.0),
        BuildingBlock("BLD-HZG-02", 26.8471, 80.9466, width_m=40.0, depth_m=30.0, height_m=22.0),
        BuildingBlock("BLD-HZG-03", 26.8460, 80.9470, width_m=50.0, depth_m=20.0, height_m=16.0),

        # Aminabad Blocks
        BuildingBlock("BLD-AMN-01", 26.8523, 80.9216, width_m=45.0, depth_m=35.0, height_m=20.0),
        BuildingBlock("BLD-AMN-02", 26.8517, 80.9225, width_m=40.0, depth_m=30.0, height_m=18.0),
        BuildingBlock("BLD-AMN-03", 26.8510, 80.9218, width_m=38.0, depth_m=28.0, height_m=16.0),

        # Charbagh Blocks
        BuildingBlock("BLD-CHB-01", 26.8584, 80.9210, width_m=60.0, depth_m=40.0, height_m=25.0),
        BuildingBlock("BLD-CHB-02", 26.8576, 80.9222, width_m=30.0, depth_m=25.0, height_m=24.0),

        # Gomti Nagar Blocks
        BuildingBlock("BLD-GMT-01", 26.8568, 80.9805, width_m=70.0, depth_m=50.0, height_m=32.0),
        BuildingBlock("BLD-GMT-02", 26.8559, 80.9795, width_m=45.0, depth_m=35.0, height_m=22.0),
        BuildingBlock("BLD-GMT-03", 26.8545, 80.9745, width_m=55.0, depth_m=40.0, height_m=42.0),

        # Alambagh Blocks
        BuildingBlock("BLD-ALM-01", 26.8080, 80.9045, width_m=80.0, depth_m=60.0, height_m=35.0),
        BuildingBlock("BLD-ALM-02", 26.8070, 80.9055, width_m=50.0, depth_m=30.0, height_m=26.0),

        # Kaiserbagh Block
        BuildingBlock("BLD-KSB-01", 26.8454, 80.9375, width_m=35.0, depth_m=30.0, height_m=16.0),

        # Indira Nagar Block
        BuildingBlock("BLD-IND-01", 26.8754, 80.9945, width_m=55.0, depth_m=35.0, height_m=20.0),

        # Aliganj Block
        BuildingBlock("BLD-ALG-01", 26.8874, 80.9375, width_m=45.0, depth_m=30.0, height_m=22.0),

        # Mahanagar Block
        BuildingBlock("BLD-MHN-01", 26.8724, 80.9325, width_m=40.0, depth_m=40.0, height_m=18.0),

        # Husainabad Block
        BuildingBlock("BLD-HSN-01", 26.8686, 80.9205, width_m=50.0, depth_m=30.0, height_m=22.0),

        # IT Crossing Block
        BuildingBlock("BLD-ITC-01", 26.8555, 80.9695, width_m=60.0, depth_m=35.0, height_m=20.0),

        # Cantonment Block
        BuildingBlock("BLD-CNT-01", 26.8376, 80.9255, width_m=35.0, depth_m=25.0, height_m=14.0),

        # Lalbagh Block
        BuildingBlock("BLD-LBG-01", 26.8496, 80.9355, width_m=40.0, depth_m=30.0, height_m=18.0),
    ]


def is_in_cone(camera: CCTVCamera, target_lat: float, target_lon: float) -> bool:
    """Check if target point falls within the camera's conical field of view.

    Uses camera heading, field-of-view angle, and maximum range.
    """
    m_per_deg_lon = _meters_per_deg_lon(camera.lat)
    dx = (target_lon - camera.lon) * m_per_deg_lon
    dy = (target_lat - camera.lat) * METERS_PER_DEG_LAT
    distance_m = math.sqrt(dx * dx + dy * dy)

    # Beyond camera range
    if distance_m > camera.range_m:
        return False

    # Within immediate base of camera pole
    if distance_m < 0.5:
        return True

    # Compass bearing from camera to target: 0°=North (+dy), 90°=East (+dx)
    bearing_deg = (math.degrees(math.atan2(dx, dy)) + 360.0) % 360.0

    # Angular difference between bearing and camera optical heading
    angle_diff = abs((bearing_deg - camera.heading_deg + 180.0) % 360.0 - 180.0)
    half_fov = camera.fov_deg / 2.0

    return angle_diff <= half_fov


def is_occluded(
    camera: CCTVCamera,
    target_lat: float,
    target_lon: float,
    buildings: list[BuildingBlock],
) -> bool:
    """Check if ray from camera to target is occluded by any building geometry.

    Performs 2D ray-rectangle intersection test using Liang-Barsky line clipping.
    """
    m_per_deg_lon = _meters_per_deg_lon(camera.lat)

    # Vector from camera (0, 0) to target (tx, ty)
    tx = (target_lon - camera.lon) * m_per_deg_lon
    ty = (target_lat - camera.lat) * METERS_PER_DEG_LAT

    for b in buildings:
        # Building center in local coordinates
        bx = (b.center_lon - camera.lon) * m_per_deg_lon
        by = (b.center_lat - camera.lat) * METERS_PER_DEG_LAT

        # Bounding box of building block
        half_w = b.width_m / 2.0
        half_d = b.depth_m / 2.0

        xmin = bx - half_w
        xmax = bx + half_w
        ymin = by - half_d
        ymax = by + half_d

        # Liang-Barsky segment clipping
        p = [-tx, tx, -ty, ty]
        q = [-xmin, xmax, -ymin, ymax]

        t_enter = 0.0
        t_exit = 1.0
        intersects = True

        for i in range(4):
            if p[i] == 0:
                if q[i] < 0:
                    intersects = False
                    break
            else:
                r = q[i] / p[i]
                if p[i] < 0:
                    if r > t_exit:
                        intersects = False
                        break
                    if r > t_enter:
                        t_enter = r
                else:  # p[i] > 0
                    if r < t_enter:
                        intersects = False
                        break
                    if r < t_exit:
                        t_exit = r

        if intersects and t_enter <= t_exit:
            # Check if intersection happens strictly between camera and target
            if t_enter < 0.99 and t_exit > 0.01:
                return True

    return False


def check_surveillance_status(
    lat: float,
    lon: float,
    cameras: list[CCTVCamera] | None = None,
    buildings: list[BuildingBlock] | None = None,
) -> dict[str, Any]:
    """Determine surveillance coverage and occlusion status for a coordinate.

    Returns:
    {
        status: SURVEILLANCE_LOCKED | BLIND_SPOT_DETECTED | OUT_OF_RANGE,
        covering_cameras: list[str],
        occluding_buildings: list[str],
        recommendation: str
    }
    """
    if cameras is None:
        cameras = get_sample_cameras()
    if buildings is None:
        buildings = get_sample_buildings()

    covering_cameras: list[str] = []
    blocked_cameras: list[str] = []
    candidate_cameras: list[str] = []
    occluding_buildings: set[str] = set()

    min_cam_distance = float("inf")

    for cam in cameras:
        m_per_deg_lon = _meters_per_deg_lon(cam.lat)
        dx = (lon - cam.lon) * m_per_deg_lon
        dy = (lat - cam.lat) * METERS_PER_DEG_LAT
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < min_cam_distance:
            min_cam_distance = dist

        # Check if target coordinate is inside optical cone
        if is_in_cone(cam, lat, lon):
            candidate_cameras.append(cam.camera_id)

            # Check if occluded by buildings
            occluded = False
            for bld in buildings:
                if is_occluded(cam, lat, lon, [bld]):
                    occluded = True
                    occluding_buildings.add(bld.block_id)

            if occluded:
                blocked_cameras.append(cam.camera_id)
            else:
                covering_cameras.append(cam.camera_id)

    # Evaluate overall status
    if len(covering_cameras) > 0:
        status = "SURVEILLANCE_LOCKED"
        recommendation = (
            f"Active optical tracking maintained by {len(covering_cameras)} camera(s) "
            f"({', '.join(covering_cameras)}). Video escort confirmed."
        )
    elif len(candidate_cameras) > 0:
        # All candidate cameras are blocked by urban geometry
        status = "BLIND_SPOT_DETECTED"
        bld_list = ", ".join(sorted(occluding_buildings)[:2])
        recommendation = (
            f"Urban canyon/architectural occlusion detected by {len(candidate_cameras)} camera(s) "
            f"blocked by structures ({bld_list}). Step towards open street corridor."
        )
    else:
        # Not within cone of any camera
        if min_cam_distance <= 250.0:
            status = "BLIND_SPOT_DETECTED"
            recommendation = (
                f"Near CCTV node ({round(min_cam_distance, 1)}m away) but outside optical cone field. "
                "Adjust position toward intersection lighting."
            )
        else:
            status = "OUT_OF_RANGE"
            recommendation = (
                f"Target coordinate is beyond active CCTV optical perimeter (nearest camera: {round(min_cam_distance, 1)}m). "
                "SafePath Pink Escort mobile patrol assigned."
            )

    return {
        "status": status,
        "covering_cameras": covering_cameras,
        "occluding_buildings": sorted(list(occluding_buildings)),
        "recommendation": recommendation,
        "metrics": {
            "candidate_cameras": len(candidate_cameras),
            "covering_cameras": len(covering_cameras),
            "blocked_cameras": len(blocked_cameras),
            "nearest_camera_distance_m": round(min_cam_distance, 1) if cameras else None,
        },
    }
