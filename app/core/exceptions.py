"""Domain-specific exceptions for FitTrack.

Each exception maps to a clear failure mode in the analysis
pipeline, enabling granular error handling in route handlers.
"""


class FitTrackError(Exception):
    """Base exception for all FitTrack domain errors."""

    def __init__(self, message: str = "An error occurred.") -> None:
        self.message = message
        super().__init__(self.message)


class AuthenticationError(FitTrackError):
    """Invalid credentials or expired token."""

    def __init__(self, message: str = "Authentication failed.") -> None:
        super().__init__(message)


class PoseDetectionError(FitTrackError):
    """MediaPipe failed to detect pose landmarks."""

    def __init__(
        self,
        message: str = "Could not detect pose landmarks.",
        pose: str | None = None,
    ) -> None:
        self.pose = pose
        super().__init__(message)


class CalibrationError(FitTrackError):
    """Pixel-to-centimeter conversion failed."""

    def __init__(
        self,
        message: str = "Calibration failed.",
    ) -> None:
        super().__init__(message)


class MeasurementError(FitTrackError):
    """Anthropometric measurement calculation failed."""

    def __init__(
        self,
        message: str = "Measurement calculation failed.",
    ) -> None:
        super().__init__(message)


class AnalysisError(FitTrackError):
    """Top-level analysis pipeline failure."""

    def __init__(
        self,
        message: str = "Analysis could not be completed.",
        warnings: list[str] | None = None,
    ) -> None:
        self.warnings = warnings or []
        super().__init__(message)
