#!/usr/bin/env python3
"""Tests for 2025 Box1 bracket thresholds and rates."""

import unittest
from decimal import Decimal

from app import compute_box1_bracket_breakdown
from dutch_tax.tax_brackets import get_tax_config


class TaxBrackets2025Tests(unittest.TestCase):
    def test_2025_brackets_match_config(self):
        config = get_tax_config(2025)
        brackets = config.box1_brackets
        # Use sum of upper bounds for test income
        taxable_income = sum([b.upper_bound or Decimal("0") for b in brackets])
        breakdown = compute_box1_bracket_breakdown(taxable_income, brackets)
        self.assertEqual(len(breakdown), len(brackets))
        for idx, bracket in enumerate(brackets):
            self.assertAlmostEqual(breakdown[idx]["rate"], float(bracket.rate), places=8)
            # Compare taxable_amount and tax_amount with config values
            # For test, just check that taxable_amount matches bracket width
            if bracket.upper_bound:
                expected_amount = float(bracket.upper_bound - bracket.lower_bound)
            else:
                expected_amount = float(taxable_income - bracket.lower_bound)
            self.assertAlmostEqual(breakdown[idx]["taxable_amount"], expected_amount, places=6)


if __name__ == "__main__":
    unittest.main()
