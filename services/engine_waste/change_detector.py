"""Temporal waste homography & volumetric delta detection.

Ingests street imagery at T0 and T1, computes:
- Homography matrix H via ORB keypoints + RANSAC
- Debris mask delta: ΔDebris = Mask(T1) - Mask(T0)
- Volume estimation via pixel area + depth approximation
"""

from __future__ import annotations

from typing import Any
import cv2
import numpy as np


def compute_homography(img_t0: np.ndarray, img_t1: np.ndarray) -> np.ndarray:
    """Compute homography matrix H from img_t0 to img_t1 using ORB features and RANSAC.

    Args:
        img_t0: Source image at time T0 (BGR or Grayscale).
        img_t1: Reference image at time T1 (BGR or Grayscale).

    Returns:
        3x3 Homography transformation matrix as np.float64. Falls back to identity matrix
        if insufficient matching keypoints are detected.
    """
    gray_t0 = cv2.cvtColor(img_t0, cv2.COLOR_BGR2GRAY) if len(img_t0.shape) == 3 else img_t0
    gray_t1 = cv2.cvtColor(img_t1, cv2.COLOR_BGR2GRAY) if len(img_t1.shape) == 3 else img_t1

    orb = cv2.ORB_create(nfeatures=1000)
    keypoints_t0, descriptors_t0 = orb.detectAndCompute(gray_t0, None)
    keypoints_t1, descriptors_t1 = orb.detectAndCompute(gray_t1, None)

    identity_h = np.eye(3, dtype=np.float64)

    if (
        descriptors_t0 is None
        or descriptors_t1 is None
        or len(keypoints_t0) < 4
        or len(keypoints_t1) < 4
    ):
        return identity_h

    # Match keypoints with BFMatcher using Hamming distance
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(descriptors_t0, descriptors_t1)

    if len(matches) < 4:
        return identity_h

    # Sort matches by distance
    matches = sorted(matches, key=lambda m: m.distance)
    top_matches = matches[:200]

    src_points = np.float32([keypoints_t0[m.queryIdx].pt for m in top_matches]).reshape(-1, 1, 2)
    dst_points = np.float32([keypoints_t1[m.trainIdx].pt for m in top_matches]).reshape(-1, 1, 2)

    homography, inlier_mask = cv2.findHomography(src_points, dst_points, cv2.RANSAC, 5.0)

    if homography is None or homography.shape != (3, 3):
        return identity_h

    return homography.astype(np.float64)


def align_images(
    img_t0: np.ndarray,
    img_t1: np.ndarray,
    H: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Warp source image img_t0 to align with perspective of img_t1 using homography matrix H.

    Args:
        img_t0: Source image at T0.
        img_t1: Destination reference image at T1.
        H: 3x3 homography transformation matrix.

    Returns:
        Tuple of (aligned_img_t0, img_t1).
    """
    height, width = img_t1.shape[:2]
    aligned_t0 = cv2.warpPerspective(img_t0, H, (width, height), flags=cv2.INTER_LINEAR)
    return aligned_t0, img_t1


def compute_debris_mask(image: np.ndarray) -> np.ndarray:
    """Generate binary mask for debris segmentation in street imagery.

    Converts image to HSV and thresholds for brown and dark debris colors:
    - Hue: 10 - 30
    - Saturation: 50 - 255
    - Value: 30 - 180

    Applies morphological open followed by close with a 5x5 kernel to remove noise
    and bridge small gaps.

    Args:
        image: Input BGR image.

    Returns:
        Binary mask (uint8) with 255 indicating debris regions and 0 elsewhere.
    """
    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_bound = np.array([10, 50, 30], dtype=np.uint8)
    upper_bound = np.array([30, 255, 180], dtype=np.uint8)

    raw_mask = cv2.inRange(hsv, lower_bound, upper_bound)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    opened_mask = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN, kernel)
    closed_mask = cv2.morphologyEx(opened_mask, cv2.MORPH_CLOSE, kernel)

    return closed_mask


def detect_debris_change(img_t0_bytes: bytes, img_t1_bytes: bytes) -> dict[str, Any]:
    """Execute end-to-end temporal debris change detection pipeline between two image frames.

    Pipeline steps:
    1. Decode images from bytes
    2. Compute homography and align T0 to T1 perspective
    3. Generate debris masks for both frames
    4. Compute delta mask (T1 - T0) for newly accumulated debris
    5. Find contours and calculate pixel area
    6. Estimate physical volume using assumed depth (0.3m pile height, 0.01 m/pixel scale)
    7. Return detailed delta and volumetric metrics

    Args:
        img_t0_bytes: Raw encoded bytes of street image at T0 (e.g. JPEG, PNG).
        img_t1_bytes: Raw encoded bytes of street image at T1 (e.g. JPEG, PNG).

    Returns:
        Dictionary containing:
        - delta_area_px: Area of newly accumulated debris in pixels
        - delta_area_m2: Area of newly accumulated debris in square meters
        - estimated_volume_m3: Estimated debris volume in cubic meters
        - fill_rate_pct: Percentage of total frame area occupied by new debris
        - num_new_debris_regions: Number of distinct debris contours detected
        - contour_centroids: List of dicts with centroid (x, y) coordinates and pixel area
        - homography_matrix: 3x3 homography matrix list representation
    """
    # 1. Decode images
    arr_t0 = np.frombuffer(img_t0_bytes, dtype=np.uint8)
    arr_t1 = np.frombuffer(img_t1_bytes, dtype=np.uint8)

    img_t0 = cv2.imdecode(arr_t0, cv2.IMREAD_COLOR)
    img_t1 = cv2.imdecode(arr_t1, cv2.IMREAD_COLOR)

    if img_t0 is None:
        raise ValueError("Failed to decode image at T0 from provided bytes.")
    if img_t1 is None:
        raise ValueError("Failed to decode image at T1 from provided bytes.")

    # 2. Compute homography and align
    homography = compute_homography(img_t0, img_t1)
    aligned_t0, aligned_t1 = align_images(img_t0, img_t1, homography)

    # 3. Generate debris masks
    mask_t0 = compute_debris_mask(aligned_t0)
    mask_t1 = compute_debris_mask(aligned_t1)

    # 4. Compute delta mask: newly accumulated debris in T1
    delta_mask = cv2.subtract(mask_t1, mask_t0)

    # 5. Find contours and extract region centroids
    contours, _ = cv2.findContours(delta_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    contour_centroids: list[dict[str, float]] = []
    min_contour_area_px = 9.0  # filter out single-pixel sensor noise

    for contour in contours:
        area = cv2.contourArea(contour)
        if area >= min_contour_area_px:
            moments = cv2.moments(contour)
            if moments["m00"] > 0:
                cx = float(moments["m10"] / moments["m00"])
                cy = float(moments["m01"] / moments["m00"])
                contour_centroids.append(
                    {
                        "x": round(cx, 2),
                        "y": round(cy, 2),
                        "area_px": round(area, 2),
                    }
                )

    # 6. Physical volume estimation
    # Scale: 0.01 m per pixel => pixel area is 0.01 * 0.01 = 0.0001 m^2
    # Average debris pile height: 0.3 meters
    pixel_scale_m = 0.01
    avg_pile_height_m = 0.3
    delta_area_px = float(np.count_nonzero(delta_mask))
    delta_area_m2 = delta_area_px * (pixel_scale_m**2)
    estimated_volume_m3 = delta_area_m2 * avg_pile_height_m

    total_image_pixels = float(aligned_t1.shape[0] * aligned_t1.shape[1])
    fill_rate_pct = (
        round((delta_area_px / total_image_pixels) * 100.0, 4)
        if total_image_pixels > 0
        else 0.0
    )

    return {
        "delta_area_px": delta_area_px,
        "delta_area_m2": round(delta_area_m2, 6),
        "estimated_volume_m3": round(estimated_volume_m3, 6),
        "fill_rate_pct": fill_rate_pct,
        "num_new_debris_regions": len(contour_centroids),
        "contour_centroids": contour_centroids,
        "homography_matrix": homography.tolist(),
    }
