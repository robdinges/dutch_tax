#!/usr/bin/env python3
"""Tests for 2025 eigenwoningforfait support."""

import unittest
from decimal import Decimal

from object_model import (
    Deduction,
    IncomeSource,
    IncomeSourceType,
    OwnHome,
    Person,
    ResidencyStatus,
    calculate_eigenwoningforfait,
)
from tax_brackets import get_tax_config


class EigenwoningforfaitCalculationTests(unittest.TestCase):
    """Unit tests for threshold handling and period fractions."""

    def test_threshold_boundaries(self):
        test_cases = [
            (12_499, 12_499 * 0.0),
            (12_500, 12_500 * 0.0010),
            (24_999, 24_999 * 0.0010),
            (25_000, 25_000 * 0.0020),
            (49_999, 49_999 * 0.0020),
            (50_000, 50_000 * 0.0025),
            (74_999, 74_999 * 0.0025),
            (75_000, 75_000 * 0.0035),
            (1_330_000, 1_330_000 * 0.0035),
            (1_330_001, 4_655 + 0.0235 * 1),
        ]

        for woz_value, expected in test_cases:
            with self.subTest(woz_value=woz_value):
                result = calculate_eigenwoningforfait(float(woz_value))
                self.assertAlmostEqual(result, expected, places=6)

    def test_partial_year_ownership(self):
        result = calculate_eigenwoningforfait(500_000, 0.5)
        expected = 500_000 * 0.0035 * 0.5
        self.assertAlmostEqual(result, expected, places=6)


class EigenwoningforfaitIntegrationTests(unittest.TestCase):
    """Integration tests with Box1 taxable income and taxes."""

    def test_taxable_income_includes_own_home_and_deduction(self):
        person = Person(
            name="Test User",
            bsn="000000001",
            residency_status=ResidencyStatus.RESIDENT,
            income_sources=[
                IncomeSource(
                    name="Salary",
                    source_type=IncomeSourceType.EMPLOYMENT,
                    gross_amount=Decimal("50000"),
                )
            ],
            deductions=[
                Deduction(
                    name="Mortgage Rent",
                    amount=Decimal("5000"),
                    deduction_type="personal",
                )
            ],
            own_home=OwnHome(woz_value=500_000, period_fraction=1.0),
        )

        # 50,000 + 1,750 (forfait) - 5,000 deduction
        self.assertEqual(person.compute_taxable_income(), Decimal("46750.0"))

    def test_box1_tax_integration_with_eigenwoningforfait(self):
        config_2025 = get_tax_config(2025)

        without_home = Person(
            name="No Home",
            bsn="000000002",
            income_sources=[
                IncomeSource(
                    name="Salary",
                    source_type=IncomeSourceType.EMPLOYMENT,
                    gross_amount=Decimal("30000"),
                )
            ],
        )

        with_home = Person(
            name="With Home",
            bsn="000000003",
            income_sources=[
                IncomeSource(
                    name="Salary",
                    source_type=IncomeSourceType.EMPLOYMENT,
                    gross_amount=Decimal("30000"),
                )
            ],
            own_home=OwnHome(woz_value=400_000, period_fraction=1.0),
        )

        tax_without_home = without_home.compute_box1_tax(config_2025.box1_brackets)
        tax_with_home = with_home.compute_box1_tax(config_2025.box1_brackets)

        # For WOZ 400,000 in 2025 band: 0.35% => 1,400 additional taxable income.
        expected_delta = Decimal("1400") * Decimal("0.0817")
        self.assertEqual(tax_with_home - tax_without_home, expected_delta)


if __name__ == "__main__":
    unittest.main()
