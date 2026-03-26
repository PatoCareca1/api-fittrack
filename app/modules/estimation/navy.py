"""Navy Method body fat estimation (Hodgdon & Beckett, 1984).

Uses circumference measurements directly — the natural input
for computer vision-derived measurements. Primary equation
for Fase 1 (ADR-006).

References:
    Hodgdon JA, Beckett MB. Prediction of percent body fat
    for US Navy men and women from body circumferences and
    height. Naval Health Research Center, Report No. 84-11,
    1984.
"""

import math

from app.models.schemas.common import BiologicalSex, Estimate

# Published Standard Error of Estimate (SEE)
# ADR-008: using published SEE as proxy in Fase 1.
# Full error propagation deferred to Fase 2.
_NAVY_SEE = 3.5


def calculate_navy_body_fat(
    waist_cm: float,
    neck_cm: float,
    height_cm: float,
    sex: BiologicalSex,
    hip_cm: float | None = None,
) -> Estimate:
    """Estimate body fat percentage via the Navy Method.

    Args:
        waist_cm: Waist circumference in centimeters.
        neck_cm: Neck circumference in centimeters.
        height_cm: Height in centimeters.
        sex: Biological sex of the individual.
        hip_cm: Hip circumference in centimeters.
            Required for female sex.

    Returns:
        Estimate with central value and 95% confidence
        interval based on published SEE.

    Raises:
        ValueError: If hip_cm is missing for female sex
            or if measurements produce invalid log inputs.
    """
    if sex == BiologicalSex.FEMALE and hip_cm is None:
        raise ValueError("hip_cm is required for female sex.")

    if sex == BiologicalSex.MALE:
        diff = waist_cm - neck_cm
        if diff <= 0:
            raise ValueError(
                "Waist must be greater than neck "
                f"for male equation. Got waist={waist_cm}, "
                f"neck={neck_cm}."
            )
        density = (
            1.0324
            - 0.19077 * math.log10(diff)
            + 0.15456 * math.log10(height_cm)
        )
    else:
        assert hip_cm is not None
        combined = waist_cm + hip_cm - neck_cm
        if combined <= 0:
            raise ValueError(
                "waist + hip - neck must be positive "
                "for female equation. "
                f"Got waist={waist_cm}, hip={hip_cm}, "
                f"neck={neck_cm}."
            )
        density = (
            1.29579
            - 0.35004 * math.log10(combined)
            + 0.22100 * math.log10(height_cm)
        )

    body_fat = (495.0 / density) - 450.0
    body_fat = max(body_fat, 2.0)
    body_fat = min(body_fat, 60.0)

    return Estimate(
        value=round(body_fat, 2),
        lower_bound=round(body_fat - _NAVY_SEE, 2),
        upper_bound=round(body_fat + _NAVY_SEE, 2),
        method="navy",
        confidence="medium",
        notes=[
            "CI based on published SEE (±3.5%).",
            "Hodgdon & Beckett, 1984.",
        ],
    )
