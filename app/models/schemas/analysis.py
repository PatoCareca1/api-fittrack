"""Analysis-related schemas for request, response, and domain.

HTTP layer uses ``AnalysisFormData`` (populated from UploadFile
+ Form fields). Internal pipeline uses ``AnalysisInput`` with
decoded images as numpy arrays. Output uses
``AnalysisResult`` with full ``Estimate`` objects (ADR-007).
"""

from datetime import datetime
from uuid import UUID

import numpy as np
from pydantic import BaseModel, Field, model_validator

from app.models.schemas.common import (
    BiologicalSex,
    Estimate,
    Measurement,
    PoseCapture,
)


class AnalysisInput(BaseModel):
    """Internal domain schema — built after HTTP upload.

    Not exposed via API. Images are decoded numpy arrays
    ready for the CV pipeline.
    """

    model_config = {"arbitrary_types_allowed": True}

    images: dict[PoseCapture, np.ndarray]
    height_cm: float = Field(gt=0, le=300)
    weight_kg: float = Field(gt=0, le=500)
    age: int = Field(gt=0, le=150)
    sex: BiologicalSex

    @property
    def has_dorsal(self) -> bool:
        """Check if dorsal pose image was provided."""
        return PoseCapture.DORSAL in self.images

    @property
    def has_lateral(self) -> bool:
        """Check if lateral pose image was provided."""
        return PoseCapture.LATERAL in self.images

    @model_validator(mode="after")
    def validate_required_poses(self) -> "AnalysisInput":
        """Ensure frontal pose is always present."""
        if PoseCapture.FRONT not in self.images:
            raise ValueError("Frontal pose image is required.")
        return self


class AnthropometricMeasurements(BaseModel):
    """Physical body measurements derived from landmarks.

    All measurements carry uncertainty per ADR-003.
    """

    waist: Measurement
    hip: Measurement
    neck: Measurement
    arm: Measurement
    height: Measurement


class BodyMetrics(BaseModel):
    """Composition metrics — all with confidence intervals."""

    body_fat_percentage: Estimate
    lean_mass_kg: Estimate
    fat_mass_kg: Estimate
    bri: Estimate
    absi: Estimate
    waist_to_height_ratio: Estimate
    waist_to_hip_ratio: Estimate


class AnalysisWarning(BaseModel):
    """Non-fatal issue encountered during analysis."""

    code: str
    message: str
    affected_metric: str | None = None


class AnalysisResult(BaseModel):
    """Complete output of the analysis pipeline."""

    analysis_id: UUID
    user_id: UUID | None = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            tz=__import__("zoneinfo").ZoneInfo("UTC")
        )
    )
    measurements: AnthropometricMeasurements
    metrics: BodyMetrics
    poses_used: list[PoseCapture]
    warnings: list[AnalysisWarning] = Field(default_factory=list)
    disclaimer: str = (
        "Esta análise é uma estimativa baseada em visão "
        "computacional e não substitui avaliação "
        "profissional de saúde."
    )
