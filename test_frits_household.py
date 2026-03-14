#!/usr/bin/env python3
"""Regressietests voor huishouden Frits – vastgelegde uitkomsten (2025).

Frits is een alleenstaande (geen fiscaal partner) met looninkomsten,
een eigen woning, spaarrekening, beleggingen en groene beleggingen.

De invoer staat in test_data/frits_input.json; alle berekende velden
worden vastgehouden als regressietestset: box 1, box 2, box 3, premies,
voorheffingen, schijven, kortingen, verdeelde posten en het eindsaldo.
"""

import json
import unittest
from pathlib import Path

from app import app

INPUT_FILE = Path(__file__).parent / "test_data" / "frits_input.json"


class FritsHouseholdTests(unittest.TestCase):
    """Vastgelegde uitkomsten voor huishouden Frits (belastingjaar 2025)."""

    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
        with app.test_client() as client:
            response = client.post("/api/calculate", json=cls.payload)
            assert response.status_code == 200, f"HTTP {response.status_code}"
            cls.result = response.get_json()
        cls.frits = cls.result["members"][0]

    # ------------------------------------------------------------------
    # Algemene response
    # ------------------------------------------------------------------

    def test_success(self):
        self.assertTrue(self.result["success"])

    def test_tax_year(self):
        self.assertEqual(self.result["tax_year"], 2025)

    def test_fiscal_partner(self):
        self.assertFalse(self.result["fiscal_partner"])

    def test_allocation_strategy(self):
        self.assertEqual(self.result["allocation_strategy"], "PROPORTIONAL")

    def test_verzamelinkomen(self):
        self.assertAlmostEqual(self.result["verzamelinkomen"], 59130.0, places=1)

    # ------------------------------------------------------------------
    # Verdeling gezamenlijke posten – totalen
    # ------------------------------------------------------------------

    def test_joint_totaal_eigenwoningforfait(self):
        self.assertAlmostEqual(
            self.result["joint_distribution_totals"]["eigenwoningforfait"], 1120.0, places=1
        )

    def test_joint_totaal_aftrek_kleine_schuld(self):
        self.assertAlmostEqual(
            self.result["joint_distribution_totals"]["aftrek_geen_of_kleine_eigenwoningschuld"],
            859.0, places=1,
        )

    def test_joint_totaal_grondslag_sparen_beleggen(self):
        self.assertAlmostEqual(
            self.result["joint_distribution_totals"]["grondslag_voordeel_sparen_beleggen"],
            25316.0, places=1,
        )

    def test_joint_totaal_vrijstelling_groene_beleggingen(self):
        self.assertAlmostEqual(
            self.result["joint_distribution_totals"]["vrijstelling_groene_beleggingen"],
            10000.0, places=1,
        )

    def test_joint_totaal_dividendbelasting(self):
        self.assertAlmostEqual(
            self.result["joint_distribution_totals"]["ingehouden_dividendbelasting"],
            150.0, places=1,
        )

    def test_joint_totaal_buitenlandse_dividendbelasting(self):
        self.assertAlmostEqual(
            self.result["joint_distribution_totals"]["ingehouden_buitenlandse_dividendbelasting"],
            0.0, places=1,
        )

    # ------------------------------------------------------------------
    # Verdeling gezamenlijke posten – toerekening Frits
    # ------------------------------------------------------------------

    def test_joint_frits_eigenwoningforfait(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["eigenwoningforfait"]["FRITS"], 1120.0, places=1
        )

    def test_joint_frits_aftrek_kleine_schuld(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["aftrek_geen_of_kleine_eigenwoningschuld"]["FRITS"],
            859.0, places=1,
        )

    def test_joint_frits_grondslag_sparen_beleggen(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["grondslag_voordeel_sparen_beleggen"]["FRITS"],
            25316.0, places=1,
        )

    def test_joint_frits_vrijstelling_groene_beleggingen(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["vrijstelling_groene_beleggingen"]["FRITS"],
            10000.0, places=1,
        )

    def test_joint_frits_dividendbelasting(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["ingehouden_dividendbelasting"]["FRITS"],
            150.0, places=1,
        )

    def test_joint_frits_buitenlandse_dividendbelasting(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["ingehouden_buitenlandse_dividendbelasting"]["FRITS"],
            0.0, places=1,
        )

    # ------------------------------------------------------------------
    # Box 1 – huishouden totalen
    # ------------------------------------------------------------------

    def test_hh_box1_total_taxable_income(self):
        self.assertAlmostEqual(self.result["box1"]["total_taxable_income"], 58261.0, places=1)

    def test_hh_box1_total_tax(self):
        self.assertAlmostEqual(self.result["box1"]["total_tax"], 10568.0, places=1)

    def test_hh_box1_schijf1_taxable_amount(self):
        schijf = self.result["box1"]["brackets_applied"][0]
        self.assertAlmostEqual(schijf["taxable_amount"], 38441.0, places=1)

    def test_hh_box1_schijf1_tax_amount(self):
        schijf = self.result["box1"]["brackets_applied"][0]
        self.assertAlmostEqual(schijf["tax_amount"], 3140.0, places=1)

    def test_hh_box1_schijf2_taxable_amount(self):
        schijf = self.result["box1"]["brackets_applied"][1]
        self.assertAlmostEqual(schijf["taxable_amount"], 19820.0, places=1)

    def test_hh_box1_schijf2_tax_amount(self):
        schijf = self.result["box1"]["brackets_applied"][1]
        self.assertAlmostEqual(schijf["tax_amount"], 7428.0, places=1)

    # ------------------------------------------------------------------
    # Box 2 – huishouden
    # ------------------------------------------------------------------

    def test_hh_box2_total_taxable_income(self):
        self.assertAlmostEqual(self.result["box2"]["total_taxable_income"], 0.0, places=1)

    def test_hh_box2_total_tax(self):
        self.assertAlmostEqual(self.result["box2"]["total_tax"], 0.0, places=1)

    # ------------------------------------------------------------------
    # Box 3 – huishouden
    # ------------------------------------------------------------------

    def test_hh_box3_total_savings(self):
        self.assertAlmostEqual(self.result["box3"]["total_savings"], 45000.0, places=1)

    def test_hh_box3_total_investments(self):
        self.assertAlmostEqual(self.result["box3"]["total_investments"], 38000.0, places=1)

    def test_hh_box3_total_other_assets(self):
        self.assertAlmostEqual(self.result["box3"]["total_other_assets"], 0.0, places=1)

    def test_hh_box3_total_debts(self):
        self.assertAlmostEqual(self.result["box3"]["total_debts"], 0.0, places=1)

    def test_hh_box3_total_net_assets(self):
        self.assertAlmostEqual(self.result["box3"]["total_net_assets"], 83000.0, places=1)

    def test_hh_box3_green_investments_total(self):
        self.assertAlmostEqual(self.result["box3"]["green_investments_total"], 10000.0, places=1)

    def test_hh_box3_green_exemption_total(self):
        self.assertAlmostEqual(self.result["box3"]["green_exemption_total"], 10000.0, places=1)

    def test_hh_box3_tax_free_assets(self):
        self.assertAlmostEqual(self.result["box3"]["tax_free_assets"], 57684.0, places=1)

    def test_hh_box3_deemed_return_savings(self):
        self.assertAlmostEqual(self.result["box3"]["deemed_return_savings"], 616.0, places=1)

    def test_hh_box3_deemed_return_non_savings(self):
        self.assertAlmostEqual(self.result["box3"]["deemed_return_non_savings"], 2234.0, places=1)

    def test_hh_box3_deemed_return_total(self):
        self.assertAlmostEqual(self.result["box3"]["deemed_return_total"], 2850.0, places=1)

    def test_hh_box3_deemed_income_before_debts(self):
        self.assertAlmostEqual(self.result["box3"]["deemed_income_before_debts"], 869.0, places=1)

    def test_hh_box3_debt_negative_income_post(self):
        self.assertAlmostEqual(self.result["box3"]["debt_negative_income_post"], 0.0, places=1)

    def test_hh_box3_corrected_deemed_return(self):
        self.assertAlmostEqual(self.result["box3"]["corrected_deemed_return"], 869.0, places=1)

    def test_hh_box3_taxable_income(self):
        self.assertAlmostEqual(self.result["box3"]["taxable_income"], 869.0, places=1)

    def test_hh_box3_total_tax(self):
        self.assertAlmostEqual(self.result["box3"]["total_tax"], 312.0, places=1)

    def test_hh_box3_foreign_dividend_withholding_total(self):
        self.assertAlmostEqual(
            self.result["box3"]["foreign_dividend_withholding_total"], 0.0, places=1
        )

    def test_hh_box3_allocation_frits(self):
        self.assertAlmostEqual(self.result["box3"]["allocation"]["FRITS"], 25316.0, places=1)

    # ------------------------------------------------------------------
    # Frits – Box 1
    # ------------------------------------------------------------------

    def test_frits_box1_gross_income(self):
        self.assertAlmostEqual(self.frits["box1"]["gross_income"], 58000.0, places=1)

    def test_frits_box1_eigenwoningforfait(self):
        self.assertAlmostEqual(self.frits["box1"]["eigenwoningforfait"], 1120.0, places=1)

    def test_frits_box1_aftrek_kleine_schuld(self):
        self.assertAlmostEqual(
            self.frits["box1"]["aftrek_geen_of_kleine_eigenwoningschuld"], 859.0, places=1
        )

    def test_frits_box1_deductions(self):
        self.assertAlmostEqual(self.frits["box1"]["deductions"], 0.0, places=1)

    def test_frits_box1_taxable_income(self):
        self.assertAlmostEqual(self.frits["box1"]["taxable_income"], 58261.0, places=1)

    def test_frits_box1_labor_credit(self):
        self.assertAlmostEqual(self.frits["box1"]["labor_credit_total"], 5158.0, places=1)

    def test_frits_box1_credits_total(self):
        self.assertAlmostEqual(self.frits["box1"]["credits"]["total"], 10.0, places=1)

    def test_frits_box1_credits_groene_beleggingen(self):
        item = self.frits["box1"]["credits"]["items"][0]
        self.assertEqual(item["name"], "Heffingskorting groene beleggingen")
        self.assertAlmostEqual(item["amount"], 10.0, places=1)

    def test_frits_box1_tax(self):
        self.assertAlmostEqual(self.frits["box1"]["tax"], 10568.0, places=1)

    def test_frits_box1_schijf1_taxable_amount(self):
        schijf = self.frits["box1"]["brackets"][0]
        self.assertAlmostEqual(schijf["taxable_amount"], 38441.0, places=1)

    def test_frits_box1_schijf1_tax_amount(self):
        schijf = self.frits["box1"]["brackets"][0]
        self.assertAlmostEqual(schijf["tax_amount"], 3140.0, places=1)

    def test_frits_box1_schijf2_taxable_amount(self):
        schijf = self.frits["box1"]["brackets"][1]
        self.assertAlmostEqual(schijf["taxable_amount"], 19820.0, places=1)

    def test_frits_box1_schijf2_tax_amount(self):
        schijf = self.frits["box1"]["brackets"][1]
        self.assertAlmostEqual(schijf["tax_amount"], 7428.0, places=1)

    # ------------------------------------------------------------------
    # Frits – Box 2
    # ------------------------------------------------------------------

    def test_frits_box2_taxable_income(self):
        self.assertAlmostEqual(self.frits["box2"]["taxable_income"], 0.0, places=1)

    def test_frits_box2_tax(self):
        self.assertAlmostEqual(self.frits["box2"]["tax"], 0.0, places=1)

    # ------------------------------------------------------------------
    # Frits – Box 3
    # ------------------------------------------------------------------

    def test_frits_box3_grondslag_sparen_beleggen(self):
        self.assertAlmostEqual(self.frits["box3"]["grondslag_sparen_beleggen"], 25316.0, places=1)

    def test_frits_box3_grondslag_voordeel_sparen_beleggen(self):
        self.assertAlmostEqual(
            self.frits["box3"]["grondslag_voordeel_sparen_beleggen"], 25316.0, places=1
        )

    def test_frits_box3_vrijstelling_groene_beleggingen(self):
        self.assertAlmostEqual(
            self.frits["box3"]["vrijstelling_groene_beleggingen"], 10000.0, places=1
        )

    def test_frits_box3_fictief_rendement_partner(self):
        self.assertAlmostEqual(self.frits["box3"]["fictief_rendement_partner"], 2850.0, places=1)

    def test_frits_box3_fictief_rendement_totaal(self):
        self.assertAlmostEqual(self.frits["box3"]["fictief_rendement_totaal"], 2850.0, places=1)

    def test_frits_box3_taxable_income(self):
        self.assertAlmostEqual(self.frits["box3"]["taxable_income"], 869.0, places=1)

    def test_frits_box3_tax_before_foreign_dividend(self):
        self.assertAlmostEqual(self.frits["box3"]["tax_before_foreign_dividend"], 312.0, places=1)

    def test_frits_box3_foreign_dividend_withholding(self):
        self.assertAlmostEqual(self.frits["box3"]["foreign_dividend_withholding"], 0.0, places=1)

    def test_frits_box3_foreign_dividend_tax_credit_applied(self):
        self.assertAlmostEqual(
            self.frits["box3"]["foreign_dividend_tax_credit_applied"], 0.0, places=1
        )

    def test_frits_box3_tax(self):
        self.assertAlmostEqual(self.frits["box3"]["tax"], 312.0, places=1)

    # ------------------------------------------------------------------
    # Frits – Premies volksverzekeringen
    # ------------------------------------------------------------------

    def test_frits_premiums_aow(self):
        self.assertAlmostEqual(self.frits["premiums"]["aow"], 6880.939, places=2)

    def test_frits_premiums_anw(self):
        self.assertAlmostEqual(self.frits["premiums"]["anw"], 38.441, places=2)

    def test_frits_premiums_wlz(self):
        self.assertAlmostEqual(self.frits["premiums"]["wlz"], 3709.5565, places=2)

    def test_frits_premiums_total(self):
        self.assertAlmostEqual(self.frits["premiums"]["total"], 10628.0, places=1)

    # ------------------------------------------------------------------
    # Frits – Voorheffingen
    # ------------------------------------------------------------------

    def test_frits_prepayments_wage_withholding(self):
        self.assertAlmostEqual(self.frits["prepayments"]["wage_withholding"], 16500.0, places=1)

    def test_frits_prepayments_dividend_withholding(self):
        self.assertAlmostEqual(self.frits["prepayments"]["dividend_withholding"], 150.0, places=1)

    def test_frits_prepayments_other(self):
        self.assertAlmostEqual(self.frits["prepayments"]["other_prepaid_taxes"], 0.0, places=1)

    def test_frits_prepayments_total(self):
        self.assertAlmostEqual(self.frits["prepayments"]["total"], 16650.0, places=1)

    # ------------------------------------------------------------------
    # Frits – Eindsaldo
    # ------------------------------------------------------------------

    def test_frits_settlement_gross_income_tax(self):
        self.assertAlmostEqual(self.frits["settlement"]["gross_income_tax"], 21508.0, places=1)

    def test_frits_settlement_tax_credits(self):
        self.assertAlmostEqual(self.frits["settlement"]["tax_credits"], 10.0, places=1)

    def test_frits_settlement_prepaid_taxes(self):
        self.assertAlmostEqual(self.frits["settlement"]["prepaid_taxes"], 16650.0, places=1)

    def test_frits_settlement_net_before_threshold(self):
        self.assertAlmostEqual(
            self.frits["settlement"]["net_settlement_before_assessment_threshold"],
            4848.0, places=1,
        )

    def test_frits_settlement_assessment_threshold_applied(self):
        self.assertFalse(self.frits["settlement"]["assessment_threshold_applied"])

    def test_frits_settlement_net(self):
        self.assertAlmostEqual(self.frits["settlement"]["net_settlement"], 4848.0, places=1)

    def test_frits_settlement_result_type(self):
        self.assertEqual(self.frits["settlement"]["result_type"], "TE_BETALEN")

    # ------------------------------------------------------------------
    # Huishouden – eindsaldo
    # ------------------------------------------------------------------

    def test_hh_settlement_box1_box3_tax(self):
        self.assertAlmostEqual(self.result["settlement"]["box1_box3_tax"], 10880.0, places=1)

    def test_hh_settlement_box2_tax(self):
        self.assertAlmostEqual(self.result["settlement"]["box2_tax"], 0.0, places=1)

    def test_hh_settlement_gross_income_tax(self):
        self.assertAlmostEqual(self.result["settlement"]["gross_income_tax"], 21508.0, places=1)

    def test_hh_settlement_total_tax_credits(self):
        self.assertAlmostEqual(self.result["settlement"]["total_tax_credits"], 10.0, places=1)

    def test_hh_settlement_total_prepaid_taxes(self):
        self.assertAlmostEqual(self.result["settlement"]["total_prepaid_taxes"], 16650.0, places=1)

    def test_hh_settlement_net_before_threshold(self):
        self.assertAlmostEqual(
            self.result["settlement"]["net_settlement_before_assessment_threshold"],
            4848.0, places=1,
        )

    def test_hh_settlement_net(self):
        self.assertAlmostEqual(self.result["settlement"]["net_settlement"], 4848.0, places=1)

    def test_hh_settlement_result_type(self):
        self.assertEqual(self.result["settlement"]["result_type"], "TE_BETALEN")

    def test_hh_settlement_effective_rate(self):
        self.assertAlmostEqual(self.result["settlement"]["effective_rate"], 37.08, places=2)

    def test_hh_settlement_premiums_basis(self):
        self.assertAlmostEqual(self.result["settlement"]["premiums"]["basis"], 38441.0, places=1)

    def test_hh_settlement_premiums_aow(self):
        self.assertAlmostEqual(self.result["settlement"]["premiums"]["aow"], 6880.939, places=2)

    def test_hh_settlement_premiums_anw(self):
        self.assertAlmostEqual(self.result["settlement"]["premiums"]["anw"], 38.441, places=2)

    def test_hh_settlement_premiums_wlz(self):
        self.assertAlmostEqual(self.result["settlement"]["premiums"]["wlz"], 3709.5565, places=2)

    def test_hh_settlement_premiums_total(self):
        self.assertAlmostEqual(self.result["settlement"]["premiums"]["total"], 10628.0, places=1)


if __name__ == "__main__":
    unittest.main()
