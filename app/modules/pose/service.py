"""Pose landmark extraction service.

Stub implementation for Fase 1. Returns realistic landmark
data for an average adult so that downstream modules
(calibration, measurements, estimation) can be tested
end-to-end without MediaPipe running.

The real implementation will use MediaPipe Pose to extract
33 body landmarks from each image.
"""

from dataclasses import dataclass, field

from app.models.schemas.analysis import AnalysisInput
from app.models.schemas.common import PoseCapture


@dataclass
class Landmark:
    """A single body landmark in normalized coordinates.

    Attributes:
        x: Horizontal position (0.0 = left, 1.0 = right).
        y: Vertical position (0.0 = top, 1.0 = bottom).
        z: Depth estimate (negative = closer to camera).
        visibility: Detection confidence (0.0 to 1.0).
        name: MediaPipe landmark name.
    """

    x: float
    y: float
    z: float
    visibility: float
    name: str


@dataclass
class PoseLandmarks:
    """Landmarks extracted from a single pose image.

    Attributes:
        pose: Which perspective this was captured from.
        landmarks: List of 33 MediaPipe pose landmarks.
        image_shape: Original image dimensions (h, w, c).
    """

    pose: PoseCapture
    landmarks: list[Landmark]
    image_shape: tuple[int, int, int]


@dataclass
class LandmarkResult:
    """Result of landmark extraction across all poses.

    Attributes:
        poses: Dict mapping pose type to its landmarks.
        warnings: Non-fatal issues during detection.
    """

    poses: dict[PoseCapture, PoseLandmarks] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def _stub_landmarks_front(
    image_shape: tuple[int, int, int],
) -> list[Landmark]:
    """Generate realistic frontal landmarks for an adult.

    Proportions based on average adult male (~175 cm).
    Values are normalized to [0, 1] image space.
    """
    return [
        Landmark(0.50, 0.06, -0.02, 0.99, "nose"),
        Landmark(0.49, 0.05, -0.03, 0.98, "left_eye_inner"),
        Landmark(0.48, 0.05, -0.03, 0.98, "left_eye"),
        Landmark(0.47, 0.05, -0.03, 0.97, "left_eye_outer"),
        Landmark(0.51, 0.05, -0.03, 0.98, "right_eye_inner"),
        Landmark(0.52, 0.05, -0.03, 0.98, "right_eye"),
        Landmark(0.53, 0.05, -0.03, 0.97, "right_eye_outer"),
        Landmark(0.46, 0.06, -0.02, 0.96, "left_ear"),
        Landmark(0.54, 0.06, -0.02, 0.96, "right_ear"),
        Landmark(0.49, 0.08, -0.01, 0.97, "mouth_left"),
        Landmark(0.51, 0.08, -0.01, 0.97, "mouth_right"),
        Landmark(0.40, 0.18, -0.01, 0.99, "left_shoulder"),
        Landmark(0.60, 0.18, -0.01, 0.99, "right_shoulder"),
        Landmark(0.35, 0.32, 0.00, 0.98, "left_elbow"),
        Landmark(0.65, 0.32, 0.00, 0.98, "right_elbow"),
        Landmark(0.33, 0.42, 0.01, 0.97, "left_wrist"),
        Landmark(0.67, 0.42, 0.01, 0.97, "right_wrist"),
        Landmark(0.34, 0.44, 0.01, 0.95, "left_pinky"),
        Landmark(0.66, 0.44, 0.01, 0.95, "right_pinky"),
        Landmark(0.33, 0.43, 0.01, 0.95, "left_index"),
        Landmark(0.67, 0.43, 0.01, 0.95, "right_index"),
        Landmark(0.34, 0.43, 0.02, 0.95, "left_thumb"),
        Landmark(0.66, 0.43, 0.02, 0.95, "right_thumb"),
        Landmark(0.43, 0.50, 0.00, 0.99, "left_hip"),
        Landmark(0.57, 0.50, 0.00, 0.99, "right_hip"),
        Landmark(0.42, 0.70, 0.01, 0.98, "left_knee"),
        Landmark(0.58, 0.70, 0.01, 0.98, "right_knee"),
        Landmark(0.41, 0.90, 0.02, 0.97, "left_ankle"),
        Landmark(0.59, 0.90, 0.02, 0.97, "right_ankle"),
        Landmark(0.40, 0.92, 0.03, 0.94, "left_heel"),
        Landmark(0.60, 0.92, 0.03, 0.94, "right_heel"),
        Landmark(0.39, 0.93, 0.01, 0.93, "left_foot_index"),
        Landmark(0.61, 0.93, 0.01, 0.93, "right_foot_index"),
    ]


def extract_landmarks(
    analysis_input: AnalysisInput,
) -> LandmarkResult:
    """Extract pose landmarks from all provided images.

    Stub implementation: returns realistic pre-computed
    landmarks. The real implementation will use MediaPipe
    Pose on each image.

    Args:
        analysis_input: Domain input with decoded images.

    Returns:
        LandmarkResult with landmarks for each pose.
    """
    result = LandmarkResult()

    for pose, image in analysis_input.images.items():
        shape = image.shape
        landmarks = _stub_landmarks_front(shape)

        result.poses[pose] = PoseLandmarks(
            pose=pose,
            landmarks=landmarks,
            image_shape=shape,
        )

    return result
