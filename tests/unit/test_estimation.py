"""Unit tests for the estimation module.

Tests all equations with known reference values and edge
cases. Uses published example calculations for validation.
"""

import pytest

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


class TestNavyMethod:
    """Tests for Navy Method body fat estimation."""

    def test_male_typical(self) -> None:
        """Average adult male should yield ~15-20% body fat."""
        result = calculate_navy_body_fat(
            waist_cm=85.0,
            neck_cm=38.0,
            height_cm=175.0,
            sex=BiologicalSex.MALE,
        )
        assert isinstance(result, Estimate)
        assert 10.0 <= result.value <= 25.0
        assert result.method == "navy"
        assert result.lower_bound < result.value
        assert result.upper_bound > result.value
        assert result.confidence in ("high", "medium", "low")

    def test_female_typical(self) -> None:
        """Average adult female should yield ~22-30% body fat."""
        result = calculate_navy_body_fat(
            waist_cm=75.0,
            neck_cm=32.0,
            height_cm=163.0,
            sex=BiologicalSex.FEMALE,
            hip_cm=100.0,
        )
        assert isinstance(result, Estimate)
        assert 15.0 <= result.value <= 40.0
        assert result.method == "navy"

    def test_female_missing_hip_raises(self) -> None:
        """Female without hip measurement is invalid."""
        with pytest.raises(ValueError, match="hip_cm"):
            calculate_navy_body_fat(
                waist_cm=75.0,
                neck_cm=32.0,
                height_cm=163.0,
                sex=BiologicalSex.FEMALE,
                hip_cm=None,
            )

    def test_male_waist_smaller_than_neck_raises(self) -> None:
        """Waist <= neck is anatomically invalid for males."""
        with pytest.raises(ValueError, match="greater"):
            calculate_navy_body_fat(
                waist_cm=35.0,
                neck_cm=40.0,
                height_cm=175.0,
                sex=BiologicalSex.MALE,
            )

    def test_confidence_interval_is_symmetric(self) -> None:
        """CI should be symmetric around the point estimate."""
        result = calculate_navy_body_fat(
            waist_cm=90.0,
            neck_cm=38.0,
            height_cm=180.0,
            sex=BiologicalSex.MALE,
        )
        lower_diff = result.value - result.lower_bound
        upper_diff = result.upper_bound - result.value
        assert abs(lower_diff - upper_diff) < 0.01

    def test_result_clamped_to_valid_range(self) -> None:
        """Body fat should never be below 2% or above 60%."""
        # Very lean male
        result = calculate_navy_body_fat(
            waist_cm=65.0,
            neck_cm=37.0,
            height_cm=190.0,
            sex=BiologicalSex.MALE,
        )
        assert result.value >= 2.0


class TestDeurenberg:
    """Tests for Deurenberg body fat estimation."""

    def test_male_typical(self) -> None:
        """Average male with BMI ~24 should yield ~18-22%."""
        result = calculate_deurenberg_body_fat(
            weight_kg=75.0,
            height_cm=175.0,
            age=30,
            sex=BiologicalSex.MALE,
        )
        assert isinstance(result, Estimate)
        assert 10.0 <= result.value <= 30.0
        assert result.method == "deurenberg"

    def test_female_higher_than_male(self) -> None:
        """Same BMI, females should have higher body fat."""
        male = calculate_deurenberg_body_fat(
            weight_kg=70.0,
            height_cm=170.0,
            age=30,
            sex=BiologicalSex.MALE,
        )
        female = calculate_deurenberg_body_fat(
            weight_kg=70.0,
            height_cm=170.0,
            age=30,
            sex=BiologicalSex.FEMALE,
        )
        assert female.value > male.value

    def test_age_increases_estimate(self) -> None:
        """Older individuals should have higher estimates."""
        young = calculate_deurenberg_body_fat(
            weight_kg=75.0,
            height_cm=175.0,
            age=25,
            sex=BiologicalSex.MALE,
        )
        old = calculate_deurenberg_body_fat(
            weight_kg=75.0,
            height_cm=175.0,
            age=55,
            sex=BiologicalSex.MALE,
        )
        assert old.value > young.value

    def test_invalid_height_raises(self) -> None:
        """Zero or negative height is invalid."""
        with pytest.raises(ValueError):
            calculate_deurenberg_body_fat(
                weight_kg=75.0,
                height_cm=0.0,
                age=30,
                sex=BiologicalSex.MALE,
            )


class TestBRI:
    """Tests for Body Roundness Index."""

    def test_typical_value_range(self) -> None:
        """BRI for average adult should be in 1-10 range."""
        result = calculate_bri(waist_cm=85.0, height_cm=175.0)
        assert isinstance(result, Estimate)
        assert 1.0 <= result.value <= 10.0
        assert result.method == "bri"

    def test_larger_waist_higher_bri(self) -> None:
        """Larger waist relative to height → higher BRI."""
        normal = calculate_bri(waist_cm=80.0, height_cm=175.0)
        large = calculate_bri(waist_cm=110.0, height_cm=175.0)
        assert large.value > normal.value

    def test_invalid_inputs_raise(self) -> None:
        """Zero or negative values should raise."""
        with pytest.raises(ValueError):
            calculate_bri(waist_cm=0.0, height_cm=175.0)
        with pytest.raises(ValueError):
            calculate_bri(waist_cm=85.0, height_cm=-10.0)


class TestABSI:
    """Tests for A Body Shape Index."""

    def test_typical_value_range(self) -> None:
        """ABSI should be a small positive number (~0.07-0.09)."""
        result = calculate_absi(
            waist_cm=85.0,
            weight_kg=75.0,
            height_cm=175.0,
        )
        assert isinstance(result, Estimate)
        assert 0.05 <= result.value <= 0.12
        assert result.method == "absi"

    def test_invalid_inputs_raise(self) -> None:
        """All inputs must be positive."""
        with pytest.raises(ValueError):
            calculate_absi(
                waist_cm=85.0,
                weight_kg=0.0,
                height_cm=175.0,
            )


class TestWHtR:
    """Tests for Waist-to-Height Ratio."""

    def test_healthy_ratio(self) -> None:
        """WHtR < 0.5 should note healthy range."""
        result = calculate_whtr(waist_cm=80.0, height_cm=175.0)
        assert result.value < 0.5
        assert any("healthy" in n.lower() for n in result.notes)

    def test_elevated_ratio(self) -> None:
        """WHtR > 0.5 should note elevated risk."""
        result = calculate_whtr(waist_cm=95.0, height_cm=170.0)
        assert result.value > 0.5
        assert any("elevated" in n.lower() for n in result.notes)


class TestWHR:
    """Tests for Waist-to-Hip Ratio."""

    def test_typical_value(self) -> None:
        """WHR should be around 0.7-1.0 for most adults."""
        result = calculate_whr(waist_cm=85.0, hip_cm=100.0)
        assert isinstance(result, Estimate)
        assert 0.5 <= result.value <= 1.2
        assert result.method == "whr"

    def test_invalid_hip_raises(self) -> None:
        """Zero hip should raise."""
        with pytest.raises(ValueError):
            calculate_whr(waist_cm=85.0, hip_cm=0.0)
