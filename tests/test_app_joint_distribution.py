#!/usr/bin/env python3
"""Integration tests for joint distribution effects in app-level Box1 calculations."""

import unittest
from math import floor

from app import app


class AppJointDistributionTests(unittest.TestCase):
    def test_box1_uses_forfait_addition_and_small_debt_deduction(self):
        payload = {
            "household_id": "TEST_JOINT_001",
            "fiscal_partner": True,
            "children_count": 0,
            "household_box1": {
                "own_home": {
                    "has_own_home": True,
                    "woz_value": 500000,
                    "period_fraction": 1,
                }
            },
            "box3_household": {
                "savings_accounts": [],
                "investment_accounts": [],
                "other_assets_items": [],
                "debt_items": [],
            },
            "members": [
                {
                    "member_id": "P1",
                    "full_name": "Partner 1",
                    "bsn": "P1",
                    "wage_withholding": 0,
                    "box1": {
                        "incomes": [{"type": "EMPLOYMENT", "amount": 50000, "labor_credit": 2000}],
                        "deductions": [{"type": "PERSONAL_ALLOWANCE", "name": "Aftrek", "amount": 3000}],
                        "has_aow": False,
                        "tax_credits": [],
                    },
                    "box2": {
                        "has_substantial_interest": False,
                        "dividend_income": 0,
                        "sale_gain": 0,
                        "acquisition_price": 0,
                    },
                },
                {
                    "member_id": "P2",
                    "full_name": "Partner 2",
                    "bsn": "P2",
                    "wage_withholding": 0,
                    "box1": {
                        "incomes": [{"type": "EMPLOYMENT", "amount": 30000, "labor_credit": 1000}],
                        "deductions": [{"type": "PERSONAL_ALLOWANCE", "name": "Aftrek", "amount": 1000}],
                        "has_aow": False,
                        "tax_credits": [],
                    },
                    "box2": {
                        "has_substantial_interest": False,
                        "dividend_income": 0,
                        "sale_gain": 0,
                        "acquisition_price": 0,
                    },
                },
            ],
        }

        with app.test_client() as client:
            preview_response = client.post("/api/joint-items-preview", json=payload)
            self.assertEqual(preview_response.status_code, 200)
            preview = preview_response.get_json()
            totals = preview["joint_distribution_totals"]

            # 70/30 split for own-home related joint items; rest split equally for this test.
            payload["joint_distribution"] = {
                "eigenwoningforfait": {
                    "P1": totals["eigenwoningforfait"] * 0.7,
                    "P2": totals["eigenwoningforfait"] * 0.3,
                },
                "aftrek_geen_of_kleine_eigenwoningschuld": {
                    "P1": totals["aftrek_geen_of_kleine_eigenwoningschuld"] * 0.7,
                    "P2": totals["aftrek_geen_of_kleine_eigenwoningschuld"] * 0.3,
                },
                "grondslag_voordeel_sparen_beleggen": {
                    "P1": 0,
                    "P2": 0,
                },
                "vrijstelling_groene_beleggingen": {
                    "P1": 0,
                    "P2": 0,
                },
                "ingehouden_dividendbelasting": {
                    "P1": 0,
                    "P2": 0,
                },
            }

            calc_response = client.post("/api/calculate", json=payload)
            self.assertEqual(calc_response.status_code, 200)
            result = calc_response.get_json()
            self.assertTrue(result.get("success"))

            by_id = {m["member_id"]: m for m in result["members"]}
            self.assertIn("P1", by_id)
            self.assertIn("P2", by_id)

            for member_id, expected_deductions in (("P1", 3000.0), ("P2", 1000.0)):
                member_box1 = by_id[member_id]["box1"]
                expected = (
                    member_box1["gross_income"]
                    + member_box1["eigenwoningforfait"]
                    - member_box1["aftrek_geen_of_kleine_eigenwoningschuld"]
                    - expected_deductions
                )
                expected_taxable = float(floor(max(0.0, expected)))
                self.assertAlmostEqual(member_box1["taxable_income"], expected_taxable, places=6)

            # Labor credits are tracked separately and do not reduce gross income.
            self.assertAlmostEqual(by_id["P1"]["box1"]["gross_income"], 50000.0, places=6)
            self.assertAlmostEqual(by_id["P2"]["box1"]["gross_income"], 30000.0, places=6)
            self.assertAlmostEqual(by_id["P1"]["box1"]["labor_credit_total"], 2000.0, places=6)
            self.assertAlmostEqual(by_id["P2"]["box1"]["labor_credit_total"], 1000.0, places=6)
            self.assertAlmostEqual(by_id["P1"]["box1"]["credits"]["total"], 0.0, places=6)
            self.assertAlmostEqual(by_id["P2"]["box1"]["credits"]["total"], 0.0, places=6)


if __name__ == "__main__":
    unittest.main()
