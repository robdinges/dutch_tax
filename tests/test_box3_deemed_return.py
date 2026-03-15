#!/usr/bin/env python3
"""Tests for Box3 deemed return split (savings vs investments)."""

import unittest
from decimal import Decimal

from object_model import (
    AllocationStrategy,
    Asset,
    AssetType,
    Household,
    Person,
)


class Box3DeemedReturnTests(unittest.TestCase):
    def test_box3_tax_uses_split_deemed_return(self):
        person = Person(name="A", bsn="100000001")
        person.assets = [
            Asset(name="Savings", asset_type=AssetType.SAVINGS, value=Decimal("100000")),
            Asset(name="ETF", asset_type=AssetType.INVESTMENT, value=Decimal("200000")),
        ]

        household = Household(household_id="HH1", members=[person])

        tax = household.compute_box3_tax(
            tax_rate=Decimal("0.35"),
            savings_return_rate=Decimal("0.01"),
            investment_return_rate=Decimal("0.06"),
        )

        # Deemed return = 100k*1% + 200k*6% = 13,000; tax = 35% => 4,550
        self.assertEqual(tax, Decimal("4550.00"))

    def test_proportional_allocation_uses_deemed_return_ratio(self):
        p1 = Person(name="A", bsn="100000002")
        p1.assets = [Asset(name="Savings", asset_type=AssetType.SAVINGS, value=Decimal("100000"))]

        p2 = Person(name="B", bsn="100000003")
        p2.assets = [Asset(name="Invest", asset_type=AssetType.INVESTMENT, value=Decimal("100000"))]

        household = Household(household_id="HH2", members=[p1, p2])

        allocation = household.allocate_box3_between_partners(
            tax_rate=Decimal("0.35"),
            strategy=AllocationStrategy.PROPORTIONAL,
            savings_return_rate=Decimal("0.01"),
            investment_return_rate=Decimal("0.06"),
        )

        total = sum(allocation.values(), Decimal("0"))
        self.assertEqual(total, Decimal("2450.00"))

        # p1 deemed return 1,000; p2 deemed return 6,000 => 1:6 ratio
        self.assertAlmostEqual(float(allocation[p1.bsn]), 350.00, places=6)
        self.assertAlmostEqual(float(allocation[p2.bsn]), 2100.00, places=6)


if __name__ == "__main__":
    unittest.main()
