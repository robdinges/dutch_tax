#!/usr/bin/env python3
"""Tests for 2025 Box1 bracket thresholds and rates."""

import unittest
from decimal import Decimal

from app import compute_box1_bracket_breakdown
from tax_brackets import get_tax_config


class TaxBrackets2025Tests(unittest.TestCase):
    def test_2025_brackets_match_form_example(self):
        config = get_tax_config(2025)

        # Form example: 38,441 @ 8.17%, 38,376 @ 37.48%, 18,263 @ 49.50%
        taxable_income = Decimal("95080")
        breakdown = compute_box1_bracket_breakdown(taxable_income, config.box1_brackets)

        self.assertEqual(len(breakdown), 3)

        first, second, third = breakdown

        self.assertAlmostEqual(first["rate"], 0.0817, places=8)
        self.assertAlmostEqual(first["taxable_amount"], 38441.0, places=6)
        self.assertAlmostEqual(first["tax_amount"], 3140.6297, places=6)

        self.assertAlmostEqual(second["rate"], 0.3748, places=8)
        self.assertAlmostEqual(second["taxable_amount"], 38376.0, places=6)
        self.assertAlmostEqual(second["tax_amount"], 14383.3248, places=6)

        self.assertAlmostEqual(third["rate"], 0.4950, places=8)
        self.assertAlmostEqual(third["taxable_amount"], 18263.0, places=6)
        self.assertAlmostEqual(third["tax_amount"], 9040.185, places=6)


if __name__ == "__main__":
    unittest.main()
