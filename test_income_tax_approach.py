#!/usr/bin/env python3
"""Tests for combined Box1/Box3 income tax approach and settlement."""

import unittest
from decimal import Decimal

from object_model import (
    Asset,
    AssetType,
    Deduction,
    Household,
    IncomeSource,
    IncomeSourceType,
    Person,
    TaxCredit,
)


class IncomeTaxApproachTests(unittest.TestCase):
    def test_box3_corrected_deemed_return_with_tax_free_assets(self):
        person = Person(name="A", bsn="200000001")
        person.assets = [
            Asset(name="Savings", asset_type=AssetType.SAVINGS, value=Decimal("100000")),
            Asset(name="Invest", asset_type=AssetType.INVESTMENT, value=Decimal("100000")),
        ]
        household = Household(household_id="HHA", members=[person])

        # Total deemed return: 100k*1.44% + 100k*5.88% = 7,320
        # Corrected assets ratio with 57k allowance: 143k / 200k = 0.715
        # Corrected deemed return: 5,233.8
        corrected = household.compute_box3_corrected_deemed_return(
            savings_return_rate=Decimal("0.0144"),
            investment_return_rate=Decimal("0.0588"),
            tax_free_assets=Decimal("57000"),
        )

        self.assertAlmostEqual(float(corrected), 5233.8, places=6)

        tax = household.compute_box3_tax(
            tax_rate=Decimal("0.36"),
            savings_return_rate=Decimal("0.0144"),
            investment_return_rate=Decimal("0.0588"),
            tax_free_assets=Decimal("57000"),
        )
        self.assertAlmostEqual(float(tax), 1884.168, places=6)

    def test_combined_settlement_after_prepaid_and_credits(self):
        person = Person(
            name="B",
            bsn="200000002",
            income_sources=[
                IncomeSource(
                    name="Employer",
                    source_type=IncomeSourceType.EMPLOYMENT,
                    gross_amount=Decimal("50000"),
                )
            ],
            deductions=[
                Deduction(name="Mortgage", amount=Decimal("5000"), deduction_type="personal")
            ],
            tax_credits=[
                TaxCredit(name="Arbeidskorting", amount=Decimal("2000"))
            ],
            withheld_tax=Decimal("9000"),
        )
        person.assets = [
            Asset(name="Savings", asset_type=AssetType.SAVINGS, value=Decimal("100000")),
            Asset(name="Broker", asset_type=AssetType.INVESTMENT, value=Decimal("50000"), dividend_tax_paid=Decimal("300")),
        ]

        household = Household(household_id="HHB", members=[person])

        # Box1 tax from bracket table where all 45,000 falls in first 19.06% and second for the excess.
        from tax_brackets import get_tax_config

        config = get_tax_config(2025)
        box1_tax = person.compute_box1_tax(config.box1_brackets)
        box3_tax = household.compute_box3_tax(
            tax_rate=config.box3_rate,
            savings_return_rate=config.box3_savings_return_rate,
            investment_return_rate=config.box3_investment_return_rate,
            tax_free_assets=config.box3_tax_free_assets_single,
        )

        gross_income_tax = box1_tax + box3_tax
        net_settlement = gross_income_tax - person.total_tax_credits() - person.compute_prepaid_taxes()

        # Smoke check for final settlement formula requested by user.
        self.assertAlmostEqual(
            float(net_settlement),
            float(gross_income_tax - Decimal("2000") - Decimal("9300")),
            places=6,
        )


if __name__ == "__main__":
    unittest.main()
