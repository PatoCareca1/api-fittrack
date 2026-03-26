"""Calibration service: normalized landmarks → centimeters.

Uses the user-reported height as scale reference. The
vertical distance between the top of the head and the
ankles in normalized coordinates maps to height_cm.

Stub implementation for Fase 1 — returns calibrated
landmarks using a simple linear scale factor.
"""

from dataclasses import dataclass, field

from app.models.schemas.common import PoseCapture
from app.modules.pose.service import (
    Landmark,
    LandmarkResult,
)


@dataclass
class CalibratedLandmark:
    """Landmark with coordinates in centimeters.

    Attributes:
        x_cm: Horizontal position in centimeters.
        y_cm: Vertical position in centimeters.
        z_cm: Depth in centimeters.
        visibility: Detection confidence (0.0 to 1.0).
        name: MediaPipe landmark name.
    """

    x_cm: float
    y_cm: float
    z_cm: float
    visibility: float
    name: str


@dataclass
class CalibratedPose:
    """Calibrated landmarks for a single pose.

    Attributes:
        pose: Which perspective.
        landmarks: Landmarks in centimeters.
        scale_factor: Pixels-per-cm used for conversion.
    """

    pose: PoseCapture
    landmarks: list[CalibratedLandmark]
    scale_factor: float


@dataclass
class CalibrationResult:
    """Output of calibration across all poses.

    Attributes:
        poses: Dict mapping pose type to calibrated data.
        reference_height_cm: User-reported height used.
    """

    poses: dict[PoseCapture, CalibratedPose] = field(default_factory=dict)
    reference_height_cm: float = 0.0


def _estimate_body_span(
    landmarks: list[Landmark],
) -> float:
    """Estimate the vertical span of the body in norm coords.

    Uses nose (top proxy) to ankle midpoint (bottom proxy).
    Returns the normalized vertical distance.
    """
    nose = next(
        (lm for lm in landmarks if lm.name == "nose"),
        None,
    )
    left_ankle = next(
        (lm for lm in landmarks if lm.name == "left_ankle"),
        None,
    )
    right_ankle = next(
        (lm for lm in landmarks if lm.name == "right_ankle"),
        None,
    )

    if nose is None or (left_ankle is None and right_ankle is None):
        return 0.85  # fallback: typical body span

    ankle_y = 0.0
    if left_ankle and right_ankle:
        ankle_y = (left_ankle.y + right_ankle.y) / 2.0
    elif left_ankle:
        ankle_y = left_ankle.y
    else:
        assert right_ankle is not None
        ankle_y = right_ankle.y

    span = ankle_y - nose.y
    return max(span, 0.1)


def calibrate(
    landmark_result: LandmarkResult,
    height_cm: float,
) -> CalibrationResult:
    """Convert normalized landmarks to centimeters.

    Uses the vertical body span (nose to ankles) as the
    reference distance, mapped to the user's reported
    height. Applies a uniform scale factor.

    Args:
        landmark_result: Raw landmarks in normalized coords.
        height_cm: User-reported height in centimeters.

    Returns:
        CalibrationResult with all landmarks in cm.
    """
    result = CalibrationResult(
        reference_height_cm=height_cm,
    )

    for pose, pose_lm in landmark_result.poses.items():
        body_span = _estimate_body_span(pose_lm.landmarks)

        # nose-to-ankle ≈ 93% of total height
        effective_height = height_cm * 0.93
        scale = effective_height / body_span

        calibrated_landmarks = [
            CalibratedLandmark(
                x_cm=lm.x * scale,
                y_cm=lm.y * scale,
                z_cm=lm.z * scale,
                visibility=lm.visibility,
                name=lm.name,
            )
            for lm in pose_lm.landmarks
        ]

        result.poses[pose] = CalibratedPose(
            pose=pose,
            landmarks=calibrated_landmarks,
            scale_factor=scale,
        )

    return result
