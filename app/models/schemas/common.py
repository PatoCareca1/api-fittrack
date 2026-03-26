"""Shared domain types used across all modules.

Defines the fundamental value objects: enumerations for pose
and biological sex, the ``Measurement`` type for physical
dimensions with uncertainty, and the ``Estimate`` type for
derived metrics with confidence intervals.
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class PoseCapture(str, Enum):
    """Supported body pose perspectives for analysis."""

    FRONT = "front"
    LATERAL = "lateral"
    DORSAL = "dorsal"


class BiologicalSex(str, Enum):
    """Biological sex for equation selection."""

    MALE = "male"
    FEMALE = "female"


class Measurement(BaseModel):
    """A physical measurement with uncertainty.

    Every measurement derived from computer vision carries
    inherent error. This type enforces that uncertainty is
    always explicit — never a bare float.

    Attributes:
        value: Central value of the measurement.
        uncertainty: Standard deviation of the estimate.
        unit: Physical unit (default ``cm``).
    """

    value: float
    uncertainty: float = Field(
        ge=0.0,
        description="Standard deviation of the measurement.",
    )
    unit: str = "cm"


class Estimate(BaseModel):
    """A derived metric with 95% confidence interval.

    Mandatory output type for all composition estimates.
    Returning a bare float is never acceptable (ADR-003).

    Attributes:
        value: Central (point) estimate.
        lower_bound: Lower bound of the 95% CI.
        upper_bound: Upper bound of the 95% CI.
        method: Name of the equation or model used.
        confidence: Qualitative confidence level.
        notes: Optional warnings or caveats.
    """

    value: float
    lower_bound: float
    upper_bound: float
    method: str
    confidence: Literal["high", "medium", "low"]
    notes: list[str] = Field(default_factory=list)
