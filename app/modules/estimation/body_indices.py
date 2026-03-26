"""Body shape indices: BRI, ABSI, WHtR, WHR.

These metrics replace BMI as primary indicators (ADR-002).
Each returns an ``Estimate`` with confidence interval.

References:
    Thomas DM et al. A novel body shape index and body
    roundness index. Obesity, 21(11):2264-2271, 2013.

    Krakauer NY, Krakauer JC. A new body shape index predicts
    mortality hazard independently of body mass index.
    PLOS ONE, 7(7):e39504, 2012.

    Ashwell M et al. Waist-to-height ratio is a better
    screening tool than waist circumference and BMI for
    adult cardiometabolic risk factors. Obesity Reviews,
    13(3):275-286, 2012.

    WHO. Waist circumference and waist-hip ratio: report
    of a WHO expert consultation. Geneva, 2008.
"""

import math

from app.models.schemas.common import Estimate


def calculate_bri(
    waist_cm: float,
    height_cm: float,
) -> Estimate:
    """Calculate Body Roundness Index (Thomas et al., 2013).

    BRI quantifies body shape and correlates with visceral
    adiposity better than BMI.

    Args:
        waist_cm: Waist circumference in centimeters.
        height_cm: Height in centimeters.

    Returns:
        Estimate with BRI value and confidence interval.

    Raises:
        ValueError: If inputs are invalid or produce
            mathematically undefined results.
    """
    if waist_cm <= 0 or height_cm <= 0:
        raise ValueError(
            "Waist and height must be positive. "
            f"Got waist={waist_cm}, height={height_cm}."
        )

    waist_radius = waist_cm / (2 * math.pi)
    half_height = 0.5 * height_cm
    eccentricity_sq = (waist_radius**2) / (half_height**2)

    if eccentricity_sq >= 1.0:
        raise ValueError(
            "Waist-to-height ratio produces invalid BRI. "
            "Waist circumference may be unrealistically "
            f"large relative to height. Got waist={waist_cm}, "
            f"height={height_cm}."
        )

    bri = 364.2 - 365.5 * math.sqrt(1.0 - eccentricity_sq)

    # BRI uncertainty: ~5% relative error from measurement
    uncertainty = bri * 0.05

    return Estimate(
        value=round(bri, 2),
        lower_bound=round(bri - uncertainty, 2),
        upper_bound=round(bri + uncertainty, 2),
        method="bri",
        confidence="medium",
        notes=["Thomas et al., 2013."],
    )


def calculate_absi(
    waist_cm: float,
    weight_kg: float,
    height_cm: float,
) -> Estimate:
    """Calculate A Body Shape Index (Krakauer & Krakauer, 2012).

    ABSI isolates the effect of waist circumference from
    overall body size. Higher ABSI predicts higher mortality.

    Args:
        waist_cm: Waist circumference in centimeters.
        weight_kg: Body weight in kilograms.
        height_cm: Height in centimeters.

    Returns:
        Estimate with ABSI value and confidence interval.

    Raises:
        ValueError: If inputs are invalid.
    """
    if waist_cm <= 0 or weight_kg <= 0 or height_cm <= 0:
        raise ValueError(
            "All inputs must be positive. "
            f"Got waist={waist_cm}, weight={weight_kg}, "
            f"height={height_cm}."
        )

    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m**2)

    # Convert waist to meters for the standard ABSI formula
    waist_m = waist_cm / 100.0
    absi = waist_m / (bmi ** (2.0 / 3.0) * height_m**0.5)

    # ABSI uncertainty: ~5% relative error
    uncertainty = absi * 0.05

    return Estimate(
        value=round(absi, 6),
        lower_bound=round(absi - uncertainty, 6),
        upper_bound=round(absi + uncertainty, 6),
        method="absi",
        confidence="medium",
        notes=["Krakauer & Krakauer, 2012."],
    )


def calculate_whtr(
    waist_cm: float,
    height_cm: float,
) -> Estimate:
    """Calculate Waist-to-Height Ratio.

    WHtR > 0.5 indicates elevated cardiometabolic risk.
    Simple, robust across ethnicities.

    Args:
        waist_cm: Waist circumference in centimeters.
        height_cm: Height in centimeters.

    Returns:
        Estimate with WHtR and confidence interval.

    Raises:
        ValueError: If inputs are invalid.
    """
    if waist_cm <= 0 or height_cm <= 0:
        raise ValueError(
            "Waist and height must be positive. "
            f"Got waist={waist_cm}, height={height_cm}."
        )

    whtr = waist_cm / height_cm

    # Propagated uncertainty from waist measurement (~1.5 cm)
    waist_uncertainty_cm = 1.5
    whtr_uncertainty = waist_uncertainty_cm / height_cm

    risk_note = (
        "WHtR > 0.5 indicates elevated " "cardiometabolic risk."
        if whtr > 0.5
        else "WHtR within healthy range."
    )

    return Estimate(
        value=round(whtr, 4),
        lower_bound=round(whtr - whtr_uncertainty, 4),
        upper_bound=round(whtr + whtr_uncertainty, 4),
        method="whtr",
        confidence="high",
        notes=[
            risk_note,
            "Ashwell et al., 2012.",
        ],
    )


def calculate_whr(
    waist_cm: float,
    hip_cm: float,
) -> Estimate:
    """Calculate Waist-to-Hip Ratio (WHO, 2008).

    Args:
        waist_cm: Waist circumference in centimeters.
        hip_cm: Hip circumference in centimeters.

    Returns:
        Estimate with WHR and confidence interval.

    Raises:
        ValueError: If inputs are invalid.
    """
    if waist_cm <= 0 or hip_cm <= 0:
        raise ValueError(
            "Waist and hip must be positive. "
            f"Got waist={waist_cm}, hip={hip_cm}."
        )

    whr = waist_cm / hip_cm

    # Propagated uncertainty from both measurements
    measurement_uncertainty = 1.5  # cm per measurement
    whr_uncertainty = whr * math.sqrt(
        (measurement_uncertainty / waist_cm) ** 2
        + (measurement_uncertainty / hip_cm) ** 2
    )

    return Estimate(
        value=round(whr, 4),
        lower_bound=round(whr - whr_uncertainty, 4),
        upper_bound=round(whr + whr_uncertainty, 4),
        method="whr",
        confidence="high",
        notes=["WHO, 2008."],
    )
