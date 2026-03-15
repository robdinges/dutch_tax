#!/usr/bin/env python3
"""Regressietests voor huishouden LR – vastgelegde uitkomsten (2025).

Dit testbestand legt de verwachte uitkomsten van huishouden LR vast als testset.
De invoer staat in tests/lr_household_testdata.json; de verwachte waarden zijn afgeleid
van de berekening zoals die door de huidige implementatie wordt geproduceerd en
zijn geverifieerd aan de hand van de documentatie in LR_aangifte_opbouw.md.

Alle berekende velden worden vastgehouden: box 1, box 2, box 3, premies,
voorheffingen, schijven, kortingen, verdeelde posten en het eindsaldo.
"""

import json
import unittest
from pathlib import Path

from app import app

INPUT_FILE = Path(__file__).parent / "lr_household_testdata.json"


class LRHouseholdTests(unittest.TestCase):
    """Vastgelegde uitkomsten voor huishouden LR (belastingjaar 2025)."""

    @classmethod
    def setUpClass(cls):
        wrapper = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
        cls.payload = wrapper["data"]
        with app.test_client() as client:
            response = client.post("/api/calculate", json=cls.payload)
            assert response.status_code == 200, f"HTTP {response.status_code}"
            cls.result = response.get_json()
        cls.p1 = {m["member_id"]: m for m in cls.result["members"]}["P1"]
        cls.p2 = {m["member_id"]: m for m in cls.result["members"]}["P2"]

    # ------------------------------------------------------------------
    # Algemene response
    # ------------------------------------------------------------------

    def test_success(self):
        self.assertTrue(self.result["success"])

    def test_tax_year(self):
        self.assertEqual(self.result["tax_year"], 2025)

    def test_fiscal_partner(self):
        self.assertTrue(self.result["fiscal_partner"])

    def test_allocation_strategy(self):
        self.assertEqual(self.result["allocation_strategy"], "PROPORTIONAL")

    def test_verzamelinkomen(self):
        self.assertAlmostEqual(self.result["verzamelinkomen"], 144762.0, places=1)

    # ------------------------------------------------------------------
    # Verdeling gezamenlijke posten – totalen
    # ------------------------------------------------------------------

    def test_joint_totaal_eigenwoningforfait(self):
        self.assertAlmostEqual(
            self.result["joint_distribution_totals"]["eigenwoningforfait"], 1326.0, places=1
        )

    def test_joint_totaal_aftrek_kleine_schuld(self):
        self.assertAlmostEqual(
            self.result["joint_distribution_totals"]["aftrek_geen_of_kleine_eigenwoningschuld"],
            1017.0, places=1,
        )

    def test_joint_totaal_grondslag_sparen_beleggen(self):
        self.assertAlmostEqual(
            self.result["joint_distribution_totals"]["grondslag_voordeel_sparen_beleggen"],
            283527.0, places=1,
        )

    def test_joint_totaal_vrijstelling_groene_beleggingen(self):
        self.assertAlmostEqual(
            self.result["joint_distribution_totals"]["vrijstelling_groene_beleggingen"],
            5613.0, places=1,
        )

    def test_joint_totaal_dividendbelasting(self):
        self.assertAlmostEqual(
            self.result["joint_distribution_totals"]["ingehouden_dividendbelasting"],
            780.0, places=1,
        )

    def test_joint_totaal_buitenlandse_dividendbelasting(self):
        self.assertAlmostEqual(
            self.result["joint_distribution_totals"]["ingehouden_buitenlandse_dividendbelasting"],
            4.0, places=1,
        )

    # ------------------------------------------------------------------
    # Verdeling gezamenlijke posten – toerekening P1
    # ------------------------------------------------------------------

    def test_joint_p1_eigenwoningforfait(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["eigenwoningforfait"]["P1"], 1326.0, places=1
        )

    def test_joint_p1_aftrek_kleine_schuld(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["aftrek_geen_of_kleine_eigenwoningschuld"]["P1"],
            1017.0, places=1,
        )

    def test_joint_p1_grondslag_sparen_beleggen(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["grondslag_voordeel_sparen_beleggen"]["P1"],
            270683.0, places=1,
        )

    def test_joint_p1_vrijstelling_groene_beleggingen(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["vrijstelling_groene_beleggingen"]["P1"],
            5359.0, places=1,
        )

    def test_joint_p1_dividendbelasting(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["ingehouden_dividendbelasting"]["P1"],
            780.0, places=1,
        )

    def test_joint_p1_buitenlandse_dividendbelasting(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["ingehouden_buitenlandse_dividendbelasting"]["P1"],
            4.0, places=1,
        )

    # ------------------------------------------------------------------
    # Verdeling gezamenlijke posten – toerekening P2
    # ------------------------------------------------------------------

    def test_joint_p2_eigenwoningforfait(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["eigenwoningforfait"]["P2"], 0.0, places=1
        )

    def test_joint_p2_aftrek_kleine_schuld(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["aftrek_geen_of_kleine_eigenwoningschuld"]["P2"],
            0.0, places=1,
        )

    def test_joint_p2_grondslag_sparen_beleggen(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["grondslag_voordeel_sparen_beleggen"]["P2"],
            12844.0, places=1,
        )

    def test_joint_p2_vrijstelling_groene_beleggingen(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["vrijstelling_groene_beleggingen"]["P2"],
            254.0, places=1,
        )

    def test_joint_p2_dividendbelasting(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["ingehouden_dividendbelasting"]["P2"],
            0.0, places=1,
        )

    def test_joint_p2_buitenlandse_dividendbelasting(self):
        self.assertAlmostEqual(
            self.result["joint_distribution"]["ingehouden_buitenlandse_dividendbelasting"]["P2"],
            0.0, places=1,
        )

    # ------------------------------------------------------------------
    # Box 1 – huishouden totalen
    # ------------------------------------------------------------------

    def test_hh_box1_total_taxable_income(self):
        self.assertAlmostEqual(self.result["box1"]["total_taxable_income"], 131918.0, places=1)

    def test_hh_box1_total_tax(self):
        self.assertAlmostEqual(self.result["box1"]["total_tax"], 29572.0, places=1)

    def test_hh_box1_schijf1_taxable_amount(self):
        schijf = self.result["box1"]["brackets_applied"][0]
        self.assertAlmostEqual(schijf["taxable_amount"], 75279.0, places=1)

    def test_hh_box1_schijf1_tax_amount(self):
        schijf = self.result["box1"]["brackets_applied"][0]
        self.assertAlmostEqual(schijf["tax_amount"], 6149.0, places=1)

    def test_hh_box1_schijf2_taxable_amount(self):
        schijf = self.result["box1"]["brackets_applied"][1]
        self.assertAlmostEqual(schijf["taxable_amount"], 38376.0, places=1)

    def test_hh_box1_schijf2_tax_amount(self):
        schijf = self.result["box1"]["brackets_applied"][1]
        self.assertAlmostEqual(schijf["tax_amount"], 14383.0, places=1)

    def test_hh_box1_schijf3_taxable_amount(self):
        schijf = self.result["box1"]["brackets_applied"][2]
        self.assertAlmostEqual(schijf["taxable_amount"], 18263.0, places=1)

    def test_hh_box1_schijf3_tax_amount(self):
        schijf = self.result["box1"]["brackets_applied"][2]
        self.assertAlmostEqual(schijf["tax_amount"], 9040.0, places=1)

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
        self.assertAlmostEqual(self.result["box3"]["total_savings"], 119247.0, places=1)

    def test_hh_box3_total_investments(self):
        self.assertAlmostEqual(self.result["box3"]["total_investments"], 279648.0, places=1)

    def test_hh_box3_total_other_assets(self):
        self.assertAlmostEqual(self.result["box3"]["total_other_assets"], 0.0, places=1)

    def test_hh_box3_total_debts(self):
        self.assertAlmostEqual(self.result["box3"]["total_debts"], 0.0, places=1)

    def test_hh_box3_total_net_assets(self):
        self.assertAlmostEqual(self.result["box3"]["total_net_assets"], 398895.0, places=1)

    def test_hh_box3_green_investments_total(self):
        self.assertAlmostEqual(self.result["box3"]["green_investments_total"], 5613.0, places=1)

    def test_hh_box3_green_exemption_total(self):
        self.assertAlmostEqual(self.result["box3"]["green_exemption_total"], 5613.0, places=1)

    def test_hh_box3_tax_free_assets(self):
        self.assertAlmostEqual(self.result["box3"]["tax_free_assets"], 115368.0, places=1)

    def test_hh_box3_deemed_return_savings(self):
        self.assertAlmostEqual(self.result["box3"]["deemed_return_savings"], 1633.0, places=1)

    def test_hh_box3_deemed_return_non_savings(self):
        self.assertAlmostEqual(self.result["box3"]["deemed_return_non_savings"], 16443.0, places=1)

    def test_hh_box3_deemed_return_total(self):
        self.assertAlmostEqual(self.result["box3"]["deemed_return_total"], 18076.0, places=1)

    def test_hh_box3_deemed_income_before_debts(self):
        self.assertAlmostEqual(self.result["box3"]["deemed_income_before_debts"], 12848.0, places=1)

    def test_hh_box3_debt_negative_income_post(self):
        self.assertAlmostEqual(self.result["box3"]["debt_negative_income_post"], 0.0, places=1)

    def test_hh_box3_corrected_deemed_return(self):
        self.assertAlmostEqual(self.result["box3"]["corrected_deemed_return"], 12848.0, places=1)

    def test_hh_box3_taxable_income(self):
        self.assertAlmostEqual(self.result["box3"]["taxable_income"], 12848.0, places=1)

    def test_hh_box3_total_tax(self):
        self.assertAlmostEqual(self.result["box3"]["total_tax"], 4619.0, places=1)

    def test_hh_box3_foreign_dividend_withholding_total(self):
        self.assertAlmostEqual(
            self.result["box3"]["foreign_dividend_withholding_total"], 4.0, places=1
        )

    def test_hh_box3_allocation_p1(self):
        self.assertAlmostEqual(self.result["box3"]["allocation"]["P1"], 270683.0, places=1)

    def test_hh_box3_allocation_p2(self):
        self.assertAlmostEqual(self.result["box3"]["allocation"]["P2"], 12844.0, places=1)

    # ------------------------------------------------------------------
    # Persoon 1 – Box 1
    # ------------------------------------------------------------------

    def test_p1_box1_gross_income(self):
        self.assertAlmostEqual(self.p1["box1"]["gross_income"], 94771.0, places=1)

    def test_p1_box1_eigenwoningforfait(self):
        self.assertAlmostEqual(self.p1["box1"]["eigenwoningforfait"], 1326.0, places=1)

    def test_p1_box1_aftrek_kleine_schuld(self):
        self.assertAlmostEqual(
            self.p1["box1"]["aftrek_geen_of_kleine_eigenwoningschuld"], 1017.0, places=1
        )

    def test_p1_box1_deductions(self):
        self.assertAlmostEqual(self.p1["box1"]["deductions"], 0.0, places=1)

    def test_p1_box1_taxable_income(self):
        self.assertAlmostEqual(self.p1["box1"]["taxable_income"], 95080.0, places=1)

    def test_p1_box1_labor_credit(self):
        self.assertAlmostEqual(self.p1["box1"]["labor_credit_total"], 3267.0, places=1)

    def test_p1_box1_credits_total(self):
        self.assertAlmostEqual(self.p1["box1"]["credits"]["total"], 6.0, places=1)

    def test_p1_box1_credits_groene_beleggingen(self):
        item = self.p1["box1"]["credits"]["items"][0]
        self.assertEqual(item["name"], "Heffingskorting groene beleggingen")
        self.assertAlmostEqual(item["amount"], 6.0, places=1)

    def test_p1_box1_tax(self):
        self.assertAlmostEqual(self.p1["box1"]["tax"], 26563.0, places=1)

    def test_p1_box1_schijf1_taxable_amount(self):
        schijf = self.p1["box1"]["brackets"][0]
        self.assertAlmostEqual(schijf["taxable_amount"], 38441.0, places=1)

    def test_p1_box1_schijf1_tax_amount(self):
        schijf = self.p1["box1"]["brackets"][0]
        self.assertAlmostEqual(schijf["tax_amount"], 3140.0, places=1)

    def test_p1_box1_schijf2_taxable_amount(self):
        schijf = self.p1["box1"]["brackets"][1]
        self.assertAlmostEqual(schijf["taxable_amount"], 38376.0, places=1)

    def test_p1_box1_schijf2_tax_amount(self):
        schijf = self.p1["box1"]["brackets"][1]
        self.assertAlmostEqual(schijf["tax_amount"], 14383.0, places=1)

    def test_p1_box1_schijf3_taxable_amount(self):
        schijf = self.p1["box1"]["brackets"][2]
        self.assertAlmostEqual(schijf["taxable_amount"], 18263.0, places=1)

    def test_p1_box1_schijf3_tax_amount(self):
        schijf = self.p1["box1"]["brackets"][2]
        self.assertAlmostEqual(schijf["tax_amount"], 9040.0, places=1)

    # ------------------------------------------------------------------
    # Persoon 1 – Box 2
    # ------------------------------------------------------------------

    def test_p1_box2_taxable_income(self):
        self.assertAlmostEqual(self.p1["box2"]["taxable_income"], 0.0, places=1)

    def test_p1_box2_tax(self):
        self.assertAlmostEqual(self.p1["box2"]["tax"], 0.0, places=1)

    # ------------------------------------------------------------------
    # Persoon 1 – Box 3
    # ------------------------------------------------------------------

    def test_p1_box3_grondslag_sparen_beleggen(self):
        self.assertAlmostEqual(self.p1["box3"]["grondslag_sparen_beleggen"], 270683.0, places=1)

    def test_p1_box3_grondslag_voordeel_sparen_beleggen(self):
        self.assertAlmostEqual(
            self.p1["box3"]["grondslag_voordeel_sparen_beleggen"], 270683.0, places=1
        )

    def test_p1_box3_vrijstelling_groene_beleggingen(self):
        self.assertAlmostEqual(
            self.p1["box3"]["vrijstelling_groene_beleggingen"], 5359.0, places=1
        )

    def test_p1_box3_fictief_rendement_partner(self):
        self.assertAlmostEqual(self.p1["box3"]["fictief_rendement_partner"], 17257.0, places=1)

    def test_p1_box3_fictief_rendement_totaal(self):
        self.assertAlmostEqual(self.p1["box3"]["fictief_rendement_totaal"], 18076.0, places=1)

    def test_p1_box3_taxable_income(self):
        self.assertAlmostEqual(self.p1["box3"]["taxable_income"], 12264.0, places=1)

    def test_p1_box3_tax_before_foreign_dividend(self):
        self.assertAlmostEqual(self.p1["box3"]["tax_before_foreign_dividend"], 4415.0, places=1)

    def test_p1_box3_foreign_dividend_withholding(self):
        self.assertAlmostEqual(self.p1["box3"]["foreign_dividend_withholding"], 4.0, places=1)

    def test_p1_box3_foreign_dividend_tax_credit_applied(self):
        self.assertAlmostEqual(
            self.p1["box3"]["foreign_dividend_tax_credit_applied"], 4.0, places=1
        )

    def test_p1_box3_tax(self):
        self.assertAlmostEqual(self.p1["box3"]["tax"], 4411.0, places=1)

    # ------------------------------------------------------------------
    # Persoon 1 – Premies volksverzekeringen
    # ------------------------------------------------------------------

    def test_p1_premiums_aow(self):
        self.assertAlmostEqual(self.p1["premiums"]["aow"], 6880.939, places=2)

    def test_p1_premiums_anw(self):
        self.assertAlmostEqual(self.p1["premiums"]["anw"], 38.441, places=2)

    def test_p1_premiums_wlz(self):
        self.assertAlmostEqual(self.p1["premiums"]["wlz"], 3709.5565, places=2)

    def test_p1_premiums_total(self):
        self.assertAlmostEqual(self.p1["premiums"]["total"], 10628.0, places=1)

    # ------------------------------------------------------------------
    # Persoon 1 – Voorheffingen
    # ------------------------------------------------------------------

    def test_p1_prepayments_wage_withholding(self):
        self.assertAlmostEqual(self.p1["prepayments"]["wage_withholding"], 34789.0, places=1)

    def test_p1_prepayments_dividend_withholding(self):
        self.assertAlmostEqual(self.p1["prepayments"]["dividend_withholding"], 780.0, places=1)

    def test_p1_prepayments_other(self):
        self.assertAlmostEqual(self.p1["prepayments"]["other_prepaid_taxes"], 0.0, places=1)

    def test_p1_prepayments_total(self):
        self.assertAlmostEqual(self.p1["prepayments"]["total"], 35569.0, places=1)

    # ------------------------------------------------------------------
    # Persoon 1 – Eindsaldo
    # ------------------------------------------------------------------

    def test_p1_settlement_gross_income_tax(self):
        self.assertAlmostEqual(self.p1["settlement"]["gross_income_tax"], 41602.0, places=1)

    def test_p1_settlement_tax_credits(self):
        self.assertAlmostEqual(self.p1["settlement"]["tax_credits"], 6.0, places=1)

    def test_p1_settlement_prepaid_taxes(self):
        self.assertAlmostEqual(self.p1["settlement"]["prepaid_taxes"], 35569.0, places=1)

    def test_p1_settlement_net_before_threshold(self):
        self.assertAlmostEqual(
            self.p1["settlement"]["net_settlement_before_assessment_threshold"], 6027.0, places=1
        )

    def test_p1_settlement_assessment_threshold_applied(self):
        self.assertFalse(self.p1["settlement"]["assessment_threshold_applied"])

    def test_p1_settlement_net(self):
        self.assertAlmostEqual(self.p1["settlement"]["net_settlement"], 6027.0, places=1)

    def test_p1_settlement_result_type(self):
        self.assertEqual(self.p1["settlement"]["result_type"], "TE_BETALEN")

    # ------------------------------------------------------------------
    # Persoon 2 – Box 1
    # ------------------------------------------------------------------

    def test_p2_box1_gross_income(self):
        self.assertAlmostEqual(self.p2["box1"]["gross_income"], 36838.0, places=1)

    def test_p2_box1_eigenwoningforfait(self):
        self.assertAlmostEqual(self.p2["box1"]["eigenwoningforfait"], 0.0, places=1)

    def test_p2_box1_aftrek_kleine_schuld(self):
        self.assertAlmostEqual(
            self.p2["box1"]["aftrek_geen_of_kleine_eigenwoningschuld"], 0.0, places=1
        )

    def test_p2_box1_deductions(self):
        self.assertAlmostEqual(self.p2["box1"]["deductions"], 0.0, places=1)

    def test_p2_box1_taxable_income(self):
        self.assertAlmostEqual(self.p2["box1"]["taxable_income"], 36838.0, places=1)

    def test_p2_box1_labor_credit(self):
        self.assertAlmostEqual(self.p2["box1"]["labor_credit_total"], 3075.0, places=1)

    def test_p2_box1_credits_total(self):
        self.assertAlmostEqual(self.p2["box1"]["credits"]["total"], 1.0, places=1)

    def test_p2_box1_credits_groene_beleggingen(self):
        item = self.p2["box1"]["credits"]["items"][0]
        self.assertEqual(item["name"], "Heffingskorting groene beleggingen")
        self.assertAlmostEqual(item["amount"], 1.0, places=1)

    def test_p2_box1_tax(self):
        self.assertAlmostEqual(self.p2["box1"]["tax"], 3009.0, places=1)

    def test_p2_box1_schijf1_taxable_amount(self):
        schijf = self.p2["box1"]["brackets"][0]
        self.assertAlmostEqual(schijf["taxable_amount"], 36838.0, places=1)

    def test_p2_box1_schijf1_tax_amount(self):
        schijf = self.p2["box1"]["brackets"][0]
        self.assertAlmostEqual(schijf["tax_amount"], 3009.0, places=1)

    # ------------------------------------------------------------------
    # Persoon 2 – Box 2
    # ------------------------------------------------------------------

    def test_p2_box2_taxable_income(self):
        self.assertAlmostEqual(self.p2["box2"]["taxable_income"], 0.0, places=1)

    def test_p2_box2_tax(self):
        self.assertAlmostEqual(self.p2["box2"]["tax"], 0.0, places=1)

    # ------------------------------------------------------------------
    # Persoon 2 – Box 3
    # ------------------------------------------------------------------

    def test_p2_box3_grondslag_sparen_beleggen(self):
        self.assertAlmostEqual(self.p2["box3"]["grondslag_sparen_beleggen"], 12844.0, places=1)

    def test_p2_box3_grondslag_voordeel_sparen_beleggen(self):
        self.assertAlmostEqual(
            self.p2["box3"]["grondslag_voordeel_sparen_beleggen"], 12844.0, places=1
        )

    def test_p2_box3_vrijstelling_groene_beleggingen(self):
        self.assertAlmostEqual(
            self.p2["box3"]["vrijstelling_groene_beleggingen"], 254.0, places=1
        )

    def test_p2_box3_fictief_rendement_partner(self):
        self.assertAlmostEqual(self.p2["box3"]["fictief_rendement_partner"], 819.0, places=1)

    def test_p2_box3_fictief_rendement_totaal(self):
        self.assertAlmostEqual(self.p2["box3"]["fictief_rendement_totaal"], 18076.0, places=1)

    def test_p2_box3_taxable_income(self):
        self.assertAlmostEqual(self.p2["box3"]["taxable_income"], 580.0, places=1)

    def test_p2_box3_tax_before_foreign_dividend(self):
        self.assertAlmostEqual(self.p2["box3"]["tax_before_foreign_dividend"], 208.0, places=1)

    def test_p2_box3_foreign_dividend_withholding(self):
        self.assertAlmostEqual(self.p2["box3"]["foreign_dividend_withholding"], 0.0, places=1)

    def test_p2_box3_foreign_dividend_tax_credit_applied(self):
        self.assertAlmostEqual(
            self.p2["box3"]["foreign_dividend_tax_credit_applied"], 0.0, places=1
        )

    def test_p2_box3_tax(self):
        self.assertAlmostEqual(self.p2["box3"]["tax"], 208.0, places=1)

    # ------------------------------------------------------------------
    # Persoon 2 – Premies volksverzekeringen
    # ------------------------------------------------------------------

    def test_p2_premiums_aow(self):
        self.assertAlmostEqual(self.p2["premiums"]["aow"], 6594.002, places=2)

    def test_p2_premiums_anw(self):
        self.assertAlmostEqual(self.p2["premiums"]["anw"], 36.838, places=2)

    def test_p2_premiums_wlz(self):
        self.assertAlmostEqual(self.p2["premiums"]["wlz"], 3554.867, places=2)

    def test_p2_premiums_total(self):
        self.assertAlmostEqual(self.p2["premiums"]["total"], 10185.0, places=1)

    # ------------------------------------------------------------------
    # Persoon 2 – Voorheffingen
    # ------------------------------------------------------------------

    def test_p2_prepayments_wage_withholding(self):
        self.assertAlmostEqual(self.p2["prepayments"]["wage_withholding"], 6968.0, places=1)

    def test_p2_prepayments_dividend_withholding(self):
        self.assertAlmostEqual(self.p2["prepayments"]["dividend_withholding"], 0.0, places=1)

    def test_p2_prepayments_other(self):
        self.assertAlmostEqual(self.p2["prepayments"]["other_prepaid_taxes"], 0.0, places=1)

    def test_p2_prepayments_total(self):
        self.assertAlmostEqual(self.p2["prepayments"]["total"], 6968.0, places=1)

    # ------------------------------------------------------------------
    # Persoon 2 – Eindsaldo
    # ------------------------------------------------------------------

    def test_p2_settlement_gross_income_tax(self):
        self.assertAlmostEqual(self.p2["settlement"]["gross_income_tax"], 13402.0, places=1)

    def test_p2_settlement_tax_credits(self):
        self.assertAlmostEqual(self.p2["settlement"]["tax_credits"], 1.0, places=1)

    def test_p2_settlement_prepaid_taxes(self):
        self.assertAlmostEqual(self.p2["settlement"]["prepaid_taxes"], 6968.0, places=1)

    def test_p2_settlement_net_before_threshold(self):
        self.assertAlmostEqual(
            self.p2["settlement"]["net_settlement_before_assessment_threshold"], 6433.0, places=1
        )

    def test_p2_settlement_assessment_threshold_applied(self):
        self.assertFalse(self.p2["settlement"]["assessment_threshold_applied"])

    def test_p2_settlement_net(self):
        self.assertAlmostEqual(self.p2["settlement"]["net_settlement"], 6433.0, places=1)

    def test_p2_settlement_result_type(self):
        self.assertEqual(self.p2["settlement"]["result_type"], "TE_BETALEN")

    # ------------------------------------------------------------------
    # Huishouden – eindsaldo
    # ------------------------------------------------------------------

    def test_hh_settlement_box1_box3_tax(self):
        self.assertAlmostEqual(self.result["settlement"]["box1_box3_tax"], 34191.0, places=1)

    def test_hh_settlement_box2_tax(self):
        self.assertAlmostEqual(self.result["settlement"]["box2_tax"], 0.0, places=1)

    def test_hh_settlement_gross_income_tax(self):
        self.assertAlmostEqual(self.result["settlement"]["gross_income_tax"], 55005.0, places=1)

    def test_hh_settlement_total_tax_credits(self):
        self.assertAlmostEqual(self.result["settlement"]["total_tax_credits"], 7.0, places=1)

    def test_hh_settlement_total_prepaid_taxes(self):
        self.assertAlmostEqual(self.result["settlement"]["total_prepaid_taxes"], 42537.0, places=1)

    def test_hh_settlement_net_before_threshold(self):
        self.assertAlmostEqual(
            self.result["settlement"]["net_settlement_before_assessment_threshold"],
            12461.0, places=1,
        )

    def test_hh_settlement_net(self):
        self.assertAlmostEqual(self.result["settlement"]["net_settlement"], 12460.0, places=1)

    def test_hh_settlement_result_type(self):
        self.assertEqual(self.result["settlement"]["result_type"], "TE_BETALEN")

    def test_hh_settlement_effective_rate(self):
        self.assertAlmostEqual(self.result["settlement"]["effective_rate"], 41.79, places=2)

    def test_hh_settlement_premiums_basis(self):
        self.assertAlmostEqual(self.result["settlement"]["premiums"]["basis"], 75279.0, places=1)

    def test_hh_settlement_premiums_aow(self):
        self.assertAlmostEqual(self.result["settlement"]["premiums"]["aow"], 13474.941, places=2)

    def test_hh_settlement_premiums_anw(self):
        self.assertAlmostEqual(self.result["settlement"]["premiums"]["anw"], 75.279, places=2)

    def test_hh_settlement_premiums_wlz(self):
        self.assertAlmostEqual(self.result["settlement"]["premiums"]["wlz"], 7264.4235, places=2)

    def test_hh_settlement_premiums_total(self):
        self.assertAlmostEqual(self.result["settlement"]["premiums"]["total"], 20814.0, places=1)


if __name__ == "__main__":
    unittest.main()
