"""Deurenberg body fat estimation (Deurenberg et al., 1991).

Uses BMI as primary input — serves as baseline comparator
against the Navy Method. Does not require circumference
measurements, only weight, height, age, and sex.

References:
    Deurenberg P, Weststrate JA, Seidell JC. Body mass index
    as a measure of body fatness: age- and sex-specific
    prediction formulas. British Journal of Nutrition,
    65(2):105-114, 1991.
"""

from app.models.schemas.common import BiologicalSex, Estimate

# Published Standard Error of Estimate
_DEURENBERG_SEE = 3.6


def calculate_deurenberg_body_fat(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: BiologicalSex,
) -> Estimate:
    """Estimate body fat percentage via Deurenberg equation.

    Args:
        weight_kg: Body weight in kilograms.
        height_cm: Height in centimeters.
        age: Age in years.
        sex: Biological sex of the individual.

    Returns:
        Estimate with central value and 95% confidence
        interval based on published SEE.

    Raises:
        ValueError: If inputs are outside valid ranges.
    """
    if height_cm <= 0:
        raise ValueError(f"Height must be positive. Got {height_cm}.")
    if weight_kg <= 0:
        raise ValueError(f"Weight must be positive. Got {weight_kg}.")
    if age <= 0:
        raise ValueError(f"Age must be positive. Got {age}.")

    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m**2)
    sex_factor = 1.0 if sex == BiologicalSex.MALE else 0.0

    body_fat = (1.20 * bmi) + (0.23 * age) - (10.8 * sex_factor) - 5.4

    body_fat = max(body_fat, 2.0)
    body_fat = min(body_fat, 60.0)

    return Estimate(
        value=round(body_fat, 2),
        lower_bound=round(body_fat - _DEURENBERG_SEE, 2),
        upper_bound=round(body_fat + _DEURENBERG_SEE, 2),
        method="deurenberg",
        confidence="medium",
        notes=[
            "CI based on published SEE (±3.6%).",
            "Deurenberg et al., 1991.",
            "Uses BMI — does not account for body " "composition distribution.",
        ],
    )
