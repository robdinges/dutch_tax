#!/usr/bin/env python3
"""Regressietests voor huishouden LR – vastgelegde uitkomsten (2025).

Dit testbestand legt de verwachte uitkomsten van huishouden LR vast als testset.
De invoer staat in test_data/LR_input.json; de verwachte waarden zijn afgeleid
van de berekening zoals die door de huidige implementatie wordt geproduceerd en
zijn geverifieerd aan de hand van de documentatie in LR_aangifte_opbouw.md.
"""

import json
import unittest
from pathlib import Path

from app import app

INPUT_FILE = Path(__file__).parent / "test_data" / "LR_input.json"


class LRHouseholdTests(unittest.TestCase):
    """Vastgelegde uitkomsten voor huishouden LR (belastingjaar 2025)."""

    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
        with app.test_client() as client:
            response = client.post("/api/calculate", json=cls.payload)
            assert response.status_code == 200, f"HTTP {response.status_code}"
            cls.result = response.get_json()
        cls.by_id = {m["member_id"]: m for m in cls.result["members"]}

    # ------------------------------------------------------------------
    # Algemene response
    # ------------------------------------------------------------------

    def test_success(self):
        self.assertTrue(self.result["success"])

    def test_tax_year(self):
        self.assertEqual(self.result["tax_year"], 2025)

    def test_fiscal_partner(self):
        self.assertTrue(self.result["fiscal_partner"])

    # ------------------------------------------------------------------
    # Verdeling gezamenlijke posten
    # ------------------------------------------------------------------

    def test_joint_eigenwoningforfait(self):
        jd = self.result["joint_distribution_totals"]
        self.assertAlmostEqual(jd["eigenwoningforfait"], 1326.0, places=1)

    def test_joint_aftrek_kleine_eigenwoningschuld(self):
        jd = self.result["joint_distribution_totals"]
        self.assertAlmostEqual(jd["aftrek_geen_of_kleine_eigenwoningschuld"], 1017.0, places=1)

    def test_joint_grondslag_sparen_beleggen(self):
        jd = self.result["joint_distribution_totals"]
        self.assertAlmostEqual(jd["grondslag_voordeel_sparen_beleggen"], 283527.0, places=1)

    def test_joint_vrijstelling_groene_beleggingen(self):
        jd = self.result["joint_distribution_totals"]
        self.assertAlmostEqual(jd["vrijstelling_groene_beleggingen"], 5613.0, places=1)

    def test_joint_dividendbelasting(self):
        jd = self.result["joint_distribution_totals"]
        self.assertAlmostEqual(jd["ingehouden_dividendbelasting"], 780.0, places=1)

    def test_joint_buitenlandse_dividendbelasting(self):
        jd = self.result["joint_distribution_totals"]
        self.assertAlmostEqual(jd["ingehouden_buitenlandse_dividendbelasting"], 4.0, places=1)

    # ------------------------------------------------------------------
    # Box 1 totalen
    # ------------------------------------------------------------------

    def test_box1_total_taxable_income(self):
        self.assertAlmostEqual(self.result["box1"]["total_taxable_income"], 131918.0, places=1)

    def test_box1_total_tax(self):
        self.assertAlmostEqual(self.result["box1"]["total_tax"], 29572.0, places=1)

    # ------------------------------------------------------------------
    # Box 3 totalen
    # ------------------------------------------------------------------

    def test_box3_total_taxable_income(self):
        self.assertAlmostEqual(self.result["box3"]["taxable_income"], 12848.0, places=1)

    def test_box3_total_tax(self):
        self.assertAlmostEqual(self.result["box3"]["total_tax"], 4619.0, places=1)

    def test_box3_total_net_assets(self):
        self.assertAlmostEqual(self.result["box3"]["total_net_assets"], 398895.0, places=1)

    # ------------------------------------------------------------------
    # Verzamelinkomen
    # ------------------------------------------------------------------

    def test_verzamelinkomen(self):
        self.assertAlmostEqual(self.result["verzamelinkomen"], 144762.0, places=1)

    # ------------------------------------------------------------------
    # Persoon 1
    # ------------------------------------------------------------------

    def test_p1_box1_gross_income(self):
        self.assertAlmostEqual(self.by_id["P1"]["box1"]["gross_income"], 94771.0, places=1)

    def test_p1_box1_taxable_income(self):
        self.assertAlmostEqual(self.by_id["P1"]["box1"]["taxable_income"], 95080.0, places=1)

    def test_p1_box1_tax(self):
        self.assertAlmostEqual(self.by_id["P1"]["box1"]["tax"], 26563.0, places=1)

    def test_p1_box1_eigenwoningforfait(self):
        self.assertAlmostEqual(self.by_id["P1"]["box1"]["eigenwoningforfait"], 1326.0, places=1)

    def test_p1_box1_aftrek_kleine_schuld(self):
        self.assertAlmostEqual(
            self.by_id["P1"]["box1"]["aftrek_geen_of_kleine_eigenwoningschuld"], 1017.0, places=1
        )

    def test_p1_box1_labor_credit(self):
        self.assertAlmostEqual(self.by_id["P1"]["box1"]["labor_credit_total"], 3267.0, places=1)

    def test_p1_box3_tax(self):
        self.assertAlmostEqual(self.by_id["P1"]["box3"]["tax"], 4411.0, places=1)

    def test_p1_premiums_total(self):
        self.assertAlmostEqual(self.by_id["P1"]["premiums"]["total"], 10628.0, places=1)

    def test_p1_settlement_gross_income_tax(self):
        self.assertAlmostEqual(self.by_id["P1"]["settlement"]["gross_income_tax"], 41602.0, places=1)

    def test_p1_settlement_prepaid_taxes(self):
        self.assertAlmostEqual(self.by_id["P1"]["settlement"]["prepaid_taxes"], 35569.0, places=1)

    def test_p1_settlement_net(self):
        self.assertAlmostEqual(self.by_id["P1"]["settlement"]["net_settlement"], 6027.0, places=1)

    def test_p1_settlement_result_type(self):
        self.assertEqual(self.by_id["P1"]["settlement"]["result_type"], "TE_BETALEN")

    # ------------------------------------------------------------------
    # Persoon 2
    # ------------------------------------------------------------------

    def test_p2_box1_gross_income(self):
        self.assertAlmostEqual(self.by_id["P2"]["box1"]["gross_income"], 36838.0, places=1)

    def test_p2_box1_taxable_income(self):
        self.assertAlmostEqual(self.by_id["P2"]["box1"]["taxable_income"], 36838.0, places=1)

    def test_p2_box1_tax(self):
        self.assertAlmostEqual(self.by_id["P2"]["box1"]["tax"], 3009.0, places=1)

    def test_p2_box1_labor_credit(self):
        self.assertAlmostEqual(self.by_id["P2"]["box1"]["labor_credit_total"], 3075.0, places=1)

    def test_p2_box3_tax(self):
        self.assertAlmostEqual(self.by_id["P2"]["box3"]["tax"], 208.0, places=1)

    def test_p2_premiums_total(self):
        self.assertAlmostEqual(self.by_id["P2"]["premiums"]["total"], 10185.0, places=1)

    def test_p2_settlement_gross_income_tax(self):
        self.assertAlmostEqual(self.by_id["P2"]["settlement"]["gross_income_tax"], 13402.0, places=1)

    def test_p2_settlement_prepaid_taxes(self):
        self.assertAlmostEqual(self.by_id["P2"]["settlement"]["prepaid_taxes"], 6968.0, places=1)

    def test_p2_settlement_net(self):
        self.assertAlmostEqual(self.by_id["P2"]["settlement"]["net_settlement"], 6433.0, places=1)

    def test_p2_settlement_result_type(self):
        self.assertEqual(self.by_id["P2"]["settlement"]["result_type"], "TE_BETALEN")

    # ------------------------------------------------------------------
    # Huishouden eindsaldo
    # ------------------------------------------------------------------

    def test_household_net_settlement(self):
        self.assertAlmostEqual(self.result["settlement"]["net_settlement"], 12460.0, places=1)

    def test_household_result_type(self):
        self.assertEqual(self.result["settlement"]["result_type"], "TE_BETALEN")

    def test_household_total_prepaid_taxes(self):
        self.assertAlmostEqual(self.result["settlement"]["total_prepaid_taxes"], 42537.0, places=1)

    def test_household_gross_income_tax(self):
        self.assertAlmostEqual(self.result["settlement"]["gross_income_tax"], 55005.0, places=1)


if __name__ == "__main__":
    unittest.main()
