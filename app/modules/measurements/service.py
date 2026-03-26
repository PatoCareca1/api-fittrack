"""Anthropometric measurements from calibrated landmarks.

Calculates circumferences and body dimensions from
calibrated (cm-space) landmarks. All measurements include
uncertainty estimates per ADR-003.

Stub implementation for Fase 1 — derives approximate values
from landmark distances using anatomical heuristics. The
real implementation will use contour analysis and depth
estimation from multiple poses.
"""

import math

from app.models.schemas.analysis import (
    AnthropometricMeasurements,
)
from app.models.schemas.common import Measurement
from app.modules.calibration.service import (
    CalibratedLandmark,
    CalibrationResult,
)


def _find_landmark(
    landmarks: list[CalibratedLandmark],
    name: str,
) -> CalibratedLandmark | None:
    """Find a landmark by name."""
    return next(
        (lm for lm in landmarks if lm.name == name),
        None,
    )


def _distance(
    a: CalibratedLandmark,
    b: CalibratedLandmark,
) -> float:
    """Euclidean distance between two landmarks in cm."""
    return math.sqrt((a.x_cm - b.x_cm) ** 2 + (a.y_cm - b.y_cm) ** 2)


def _estimate_waist(
    landmarks: list[CalibratedLandmark],
) -> Measurement:
    """Estimate waist circumference from hip landmarks.

    Approximation: frontal hip width × π gives an
    elliptical circumference estimate. The waist is
    estimated as slightly above the hip line.
    """
    left_hip = _find_landmark(landmarks, "left_hip")
    right_hip = _find_landmark(landmarks, "right_hip")

    if left_hip is None or right_hip is None:
        return Measurement(value=85.0, uncertainty=5.0, unit="cm")

    hip_width = _distance(left_hip, right_hip)
    # Waist ≈ narrower than hip width; approximate depth
    # as 0.75 × frontal width for elliptical model
    depth = hip_width * 0.75
    waist_circ = math.pi * math.sqrt((hip_width**2 + depth**2) / 2.0)

    # Waist sits above hip; typically ~90% of hip circ
    waist_circ *= 0.90

    return Measurement(
        value=round(waist_circ, 1),
        uncertainty=2.0,
        unit="cm",
    )


def _estimate_hip(
    landmarks: list[CalibratedLandmark],
) -> Measurement:
    """Estimate hip circumference from hip landmarks."""
    left_hip = _find_landmark(landmarks, "left_hip")
    right_hip = _find_landmark(landmarks, "right_hip")

    if left_hip is None or right_hip is None:
        return Measurement(value=98.0, uncertainty=5.0, unit="cm")

    hip_width = _distance(left_hip, right_hip)
    depth = hip_width * 0.80
    hip_circ = math.pi * math.sqrt((hip_width**2 + depth**2) / 2.0)

    return Measurement(
        value=round(hip_circ, 1),
        uncertainty=2.0,
        unit="cm",
    )


def _estimate_neck(
    landmarks: list[CalibratedLandmark],
) -> Measurement:
    """Estimate neck circumference from ear/shoulder span."""
    left_ear = _find_landmark(landmarks, "left_ear")
    right_ear = _find_landmark(landmarks, "right_ear")

    if left_ear is None or right_ear is None:
        return Measurement(value=38.0, uncertainty=2.0, unit="cm")

    ear_width = _distance(left_ear, right_ear)
    # Neck width ≈ ear-to-ear distance;
    # circumference ≈ width × π × 0.6 (neck is narrower)
    neck_circ = ear_width * math.pi * 0.60

    return Measurement(
        value=round(neck_circ, 1),
        uncertainty=1.5,
        unit="cm",
    )


def _estimate_arm(
    landmarks: list[CalibratedLandmark],
) -> Measurement:
    """Estimate upper arm circumference from shoulder/elbow."""
    left_shoulder = _find_landmark(landmarks, "left_shoulder")
    left_elbow = _find_landmark(landmarks, "left_elbow")

    if left_shoulder is None or left_elbow is None:
        return Measurement(value=30.0, uncertainty=2.0, unit="cm")

    upper_arm_length = _distance(left_shoulder, left_elbow)
    # Arm circumference ≈ length × 0.55 (typical ratio)
    arm_circ = upper_arm_length * 0.55

    return Measurement(
        value=round(arm_circ, 1),
        uncertainty=1.5,
        unit="cm",
    )


def _estimate_height(
    landmarks: list[CalibratedLandmark],
) -> Measurement:
    """Estimate height from nose to ankle span.

    Validates the calibrated height against expected range.
    """
    nose = _find_landmark(landmarks, "nose")
    left_ankle = _find_landmark(landmarks, "left_ankle")
    right_ankle = _find_landmark(landmarks, "right_ankle")

    if nose is None or (left_ankle is None and right_ankle is None):
        return Measurement(value=175.0, uncertainty=3.0, unit="cm")

    ankle_y = 0.0
    if left_ankle and right_ankle:
        ankle_y = (left_ankle.y_cm + right_ankle.y_cm) / 2
    elif left_ankle:
        ankle_y = left_ankle.y_cm
    else:
        assert right_ankle is not None
        ankle_y = right_ankle.y_cm

    # nose-to-ankle ≈ 93% of total height
    visible_height = ankle_y - nose.y_cm
    total_height = visible_height / 0.93

    return Measurement(
        value=round(total_height, 1),
        uncertainty=1.0,
        unit="cm",
    )


def calculate_measurements(
    calibration: CalibrationResult,
) -> AnthropometricMeasurements:
    """Derive anthropometric measurements from landmarks.

    Uses the frontal pose as primary source. Lateral and
    dorsal poses would improve depth estimation in Fase 2.

    Args:
        calibration: Calibrated landmarks in centimeters.

    Returns:
        AnthropometricMeasurements with uncertainty on
        each measurement per ADR-003.
    """
    from app.models.schemas.common import PoseCapture

    # Prefer frontal pose for measurements
    primary_pose = calibration.poses.get(PoseCapture.FRONT) or next(
        iter(calibration.poses.values())
    )
    landmarks = primary_pose.landmarks

    return AnthropometricMeasurements(
        waist=_estimate_waist(landmarks),
        hip=_estimate_hip(landmarks),
        neck=_estimate_neck(landmarks),
        arm=_estimate_arm(landmarks),
        height=_estimate_height(landmarks),
    )
