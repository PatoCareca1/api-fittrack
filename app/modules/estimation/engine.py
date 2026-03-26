"""Estimation engine — orchestrates all equations.

Receives anthropometric measurements and user data, runs
every applicable equation, and assembles the complete
``BodyMetrics`` output.
"""

from app.models.schemas.analysis import (
    AnthropometricMeasurements,
    BodyMetrics,
)
from app.models.schemas.common import BiologicalSex, Estimate
from app.modules.estimation.body_indices import (
    calculate_absi,
    calculate_bri,
    calculate_whr,
    calculate_whtr,
)
from app.modules.estimation.deurenberg import (
    calculate_deurenberg_body_fat,
)
from app.modules.estimation.navy import (
    calculate_navy_body_fat,
)


def estimate_body_metrics(
    measurements: AnthropometricMeasurements,
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: BiologicalSex,
) -> BodyMetrics:
    """Run all estimation equations and build BodyMetrics.

    Uses Navy Method as the primary body fat estimate
    (ADR-006). Deurenberg runs in parallel as baseline.
    The Navy result is used for lean/fat mass derivation.

    Args:
        measurements: Calibrated anthropometric
            measurements from the CV pipeline.
        weight_kg: Body weight in kilograms.
        height_cm: Height in centimeters.
        age: Age in years.
        sex: Biological sex for equation selection.

    Returns:
        Complete BodyMetrics with all estimates.
    """
    waist = measurements.waist.value
    hip = measurements.hip.value
    neck = measurements.neck.value

    # --- Body fat percentage (primary: Navy) ---
    navy_bf = calculate_navy_body_fat(
        waist_cm=waist,
        neck_cm=neck,
        height_cm=height_cm,
        sex=sex,
        hip_cm=hip,
    )

    # Deurenberg as parallel baseline
    deurenberg_bf = calculate_deurenberg_body_fat(
        weight_kg=weight_kg,
        height_cm=height_cm,
        age=age,
        sex=sex,
    )
    navy_bf.notes.append(f"Deurenberg baseline: {deurenberg_bf.value}%.")

    # --- Derived mass estimates ---
    fat_mass = weight_kg * (navy_bf.value / 100.0)
    lean_mass = weight_kg - fat_mass

    # Propagate Navy SEE to mass estimates
    bf_see = (navy_bf.upper_bound - navy_bf.lower_bound) / 2.0
    fat_mass_see = weight_kg * (bf_see / 100.0)

    fat_mass_estimate = Estimate(
        value=round(fat_mass, 2),
        lower_bound=round(fat_mass - fat_mass_see, 2),
        upper_bound=round(fat_mass + fat_mass_see, 2),
        method="navy_derived",
        confidence=navy_bf.confidence,
        notes=["Derived from Navy body fat estimate."],
    )

    lean_mass_estimate = Estimate(
        value=round(lean_mass, 2),
        lower_bound=round(lean_mass - fat_mass_see, 2),
        upper_bound=round(lean_mass + fat_mass_see, 2),
        method="navy_derived",
        confidence=navy_bf.confidence,
        notes=["Derived from Navy body fat estimate."],
    )

    # --- Body shape indices ---
    bri = calculate_bri(
        waist_cm=waist,
        height_cm=height_cm,
    )

    absi = calculate_absi(
        waist_cm=waist,
        weight_kg=weight_kg,
        height_cm=height_cm,
    )

    whtr = calculate_whtr(
        waist_cm=waist,
        height_cm=height_cm,
    )

    whr = calculate_whr(
        waist_cm=waist,
        hip_cm=hip,
    )

    return BodyMetrics(
        body_fat_percentage=navy_bf,
        lean_mass_kg=lean_mass_estimate,
        fat_mass_kg=fat_mass_estimate,
        bri=bri,
        absi=absi,
        waist_to_height_ratio=whtr,
        waist_to_hip_ratio=whr,
    )
