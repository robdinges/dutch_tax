#!/usr/bin/env python3
"""Integration test for green investment credit and foreign dividend withholding allocation."""

import unittest

from app import app


class GreenCreditAndForeignDividendTests(unittest.TestCase):
    def test_green_credit_and_foreign_dividend_are_applied(self):
        payload = {
            "household_id": "TEST_GREEN_FOREIGN_001",
            "fiscal_partner": True,
            "children_count": 0,
            "household_box1": {
                "own_home": {
                    "has_own_home": False,
                    "woz_value": 0,
                    "period_fraction": 1,
                }
            },
            "box3_household": {
                "savings_accounts": [
                    {"name": "Savings", "amount": 50000, "is_green": False}
                ],
                "investment_accounts": [
                    {
                        "name": "Global ETF",
                        "amount": 300000,
                        "is_green": False,
                        "dividend_withholding": 0,
                        "foreign_dividend_withholding": 120,
                    },
                    {
                        "name": "Green Fund",
                        "amount": 10000,
                        "is_green": True,
                        "dividend_withholding": 0,
                        "foreign_dividend_withholding": 0,
                    },
                ],
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
                        "incomes": [],
                        "deductions": [],
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
                        "incomes": [],
                        "deductions": [],
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

            self.assertIn("ingehouden_buitenlandse_dividendbelasting", totals)
            self.assertEqual(totals["ingehouden_buitenlandse_dividendbelasting"], 120.0)

            payload["joint_distribution"] = {
                "eigenwoningforfait": {"P1": totals["eigenwoningforfait"], "P2": 0},
                "aftrek_geen_of_kleine_eigenwoningschuld": {
                    "P1": totals["aftrek_geen_of_kleine_eigenwoningschuld"],
                    "P2": 0,
                },
                "grondslag_voordeel_sparen_beleggen": {
                    "P1": totals["grondslag_voordeel_sparen_beleggen"],
                    "P2": 0,
                },
                "vrijstelling_groene_beleggingen": {
                    "P1": totals["vrijstelling_groene_beleggingen"],
                    "P2": 0,
                },
                "ingehouden_dividendbelasting": {
                    "P1": totals["ingehouden_dividendbelasting"],
                    "P2": 0,
                },
                "ingehouden_buitenlandse_dividendbelasting": {
                    "P1": totals["ingehouden_buitenlandse_dividendbelasting"],
                    "P2": 0,
                },
            }

            calc_response = client.post("/api/calculate", json=payload)
            self.assertEqual(calc_response.status_code, 200)
            result = calc_response.get_json()
            self.assertTrue(result.get("success"))

            by_id = {m["member_id"]: m for m in result["members"]}
            p1 = by_id["P1"]
            p2 = by_id["P2"]

            # 0.1% of 10,000 green investments, rounded up in favor of taxpayer.
            self.assertEqual(p1["box1"]["credits"]["total"], 10.0)
            self.assertEqual(p2["box1"]["credits"]["total"], 0.0)
            self.assertEqual(result["settlement"]["total_tax_credits"], 10.0)

            self.assertEqual(p1["box3"]["foreign_dividend_withholding"], 120.0)
            self.assertEqual(p1["box3"]["foreign_dividend_tax_credit_applied"], 120.0)
            self.assertEqual(
                p1["box3"]["tax"],
                p1["box3"]["tax_before_foreign_dividend"] - p1["box3"]["foreign_dividend_tax_credit_applied"],
            )
            self.assertEqual(p2["box3"]["foreign_dividend_withholding"], 0.0)

    def test_small_payable_amount_is_zeroed(self):
        payload = {
            "household_id": "TEST_SMALL_PAYABLE_001",
            "fiscal_partner": True,
            "children_count": 0,
            "household_box1": {
                "own_home": {
                    "has_own_home": True,
                    "woz_value": 379000,
                    "period_fraction": 1,
                }
            },
            "dividend_withholding_total": 780,
            "foreign_dividend_withholding_total": 4,
            "box3_household": {
                "savings_accounts": [
                    {"name": "S1", "amount": 119247, "is_green": False}
                ],
                "investment_accounts": [
                    {"name": "I1", "amount": 279648, "is_green": False, "dividend_withholding": 780, "foreign_dividend_withholding": 4},
                    {"name": "G1", "amount": 5613, "is_green": True, "dividend_withholding": 0, "foreign_dividend_withholding": 0},
                ],
                "other_assets_items": [{"name": "Overig", "amount": 0}],
                "debt_items": [{"name": "Schuld", "amount": 0}],
            },
            "joint_distribution": {
                "eigenwoningforfait": {"P1": 1326, "P2": 0},
                "aftrek_geen_of_kleine_eigenwoningschuld": {"P1": 1017, "P2": 0},
                "grondslag_voordeel_sparen_beleggen": {"P1": 270683, "P2": 12844},
                "vrijstelling_groene_beleggingen": {"P1": 5359, "P2": 254},
                "ingehouden_dividendbelasting": {"P1": 780, "P2": 0},
                "ingehouden_buitenlandse_dividendbelasting": {"P1": 4, "P2": 0},
            },
            "members": [
                {
                    "member_id": "P1",
                    "full_name": "Partner 1",
                    "bsn": "P1",
                    "wage_withholding": 34789,
                    "box1": {
                        "incomes": [{"type": "EMPLOYMENT", "amount": 94771, "labor_credit": 3267}],
                        "deductions": [],
                        "has_aow": False,
                        "tax_credits": [{"name": "arbeidskorting", "amount": 2234}],
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
                    "wage_withholding": 6969,
                    "box1": {
                        "incomes": [
                            {"type": "EMPLOYMENT", "amount": 21822, "labor_credit": 3075},
                            {"type": "BENEFITS", "amount": 15016, "labor_credit": 0},
                        ],
                        "deductions": [],
                        "has_aow": False,
                        "tax_credits": [
                            {"name": "arbeidskorting", "amount": 3879},
                            {"name": "algemene heffingskorting", "amount": 2497},
                        ],
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
            calc_response = client.post("/api/calculate", json=payload)
            self.assertEqual(calc_response.status_code, 200)
            result = calc_response.get_json()
            self.assertTrue(result.get("success"))

            by_id = {m["member_id"]: m for m in result["members"]}
            self.assertEqual(by_id["P2"]["settlement"]["net_settlement_before_assessment_threshold"], 57.0)
            self.assertTrue(by_id["P2"]["settlement"]["assessment_threshold_applied"])
            self.assertEqual(by_id["P2"]["settlement"]["net_settlement"], 0.0)
            self.assertEqual(by_id["P2"]["settlement"]["result_type"], "NIETS_TE_BETALEN")


if __name__ == "__main__":
    unittest.main()
