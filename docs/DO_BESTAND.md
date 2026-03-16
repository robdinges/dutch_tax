# DO Bestand - Invoer, Berekening en Output (Procesflow 2026)

Dit document beschrijft de actuele structuur en rekengang van de Python webapp.

## 1. Invoerstructuur

### 1.1 Huishouden

- `household_id` (string)
- `fiscal_partner` (boolean)
- `children_count` (number)
- `household_box1.own_home`: `{ has_own_home, woz_value, period_fraction }`
- `box3_household`
- `joint_distribution`
- `members[]`

`joint_distribution` bevat:

- `eigenwoningforfait`
- `aftrek_geen_of_kleine_eigenwoningschuld`
- `grondslag_voordeel_sparen_beleggen`
- `vrijstelling_groene_beleggingen`
- `ingehouden_dividendbelasting`
- `ingehouden_buitenlandse_dividendbelasting`

### 1.2 Box 3 huishouden

- `savings_accounts[]`: `{ name, amount, is_green }`
- `investment_accounts[]`: `{ name, amount, is_green, dividend_withholding, foreign_dividend_withholding }`
- `other_assets_items[]`: `{ name, amount }`
- `debt_items[]`: `{ name, amount }`
- `total_dividend_withholding`
- `total_foreign_dividend_withholding`

## 2. Berekening (hoofdlijnen)

### 2.1 Box 1

Per persoon:

- `gross_income = sum(incomes.amount)`
- `box1_taxable_income = max(0, gross_income + eigenwoningforfait_share - small_debt_deduction_share - deductions)`
- Schijftarief-berekening op `box1_taxable_income`

Huishouden:

- Eigenwoningforfait op huishoudniveau uit WOZ/periode
- Aftrek geen/kleine eigenwoningschuld = `round_up(eigenwoningforfait * 76.667%)`

### 2.2 Box 2

- Alleen actief bij `has_substantial_interest = true`
- `box2_taxable_income = max(0, dividend_income + sale_gain - acquisition_price)`
- `box2_tax = box2_taxable_income * box2_rate`

### 2.3 Box 3

Huishouden:

- Vermogen uit sparen/beleggen/overig minus schulden
- Fictief rendement op sparen en beleggen
- Correctie met heffingsvrij vermogen
- `box3_taxable_income = max(0, corrected_deemed_return)`

Partners:

- Verdeling van `grondslag_voordeel_sparen_beleggen`
- Toerekening van Box 3 belastbaar inkomen op basis van verdeelde grondslag
- `box3_tax_before_foreign_dividend = box3_taxable_member * box3_rate`
- `foreign_dividend_tax_credit_applied = min(box3_tax_before_foreign_dividend, foreign_dividend_withholding_share)`
- `box3_tax_member = max(0, box3_tax_before_foreign_dividend - foreign_dividend_tax_credit_applied)`

### 2.4 Groene beleggingen

- Vrijstelling groene beleggingen is een verdeelpost
- Daarnaast wordt heffingskorting groene beleggingen toegevoegd:
- `credit = round_up(min(green_exemption_share, cap_single) * rate)`

### 2.5 Voorheffingen en eindafrekening

Per persoon:

- `prepaid_taxes = wage_withholding + ingehouden_dividendbelasting + other_prepaid_taxes`
- `gross_member_tax = box1_tax + box2_tax + box3_tax_member + premiums`
- `net_member_settlement_before_threshold = gross_member_tax - tax_credits - prepaid_taxes`
- Kleine aanslag-regel: als `0 <= net <= 57`, dan `net = 0` en resultaat `NIETS_TE_BETALEN`

Huishouden:

- `settlement.net_settlement` is de som van partner-nettoresultaten na drempeltoepassing

## 3. Outputvelden

Belangrijkste response-onderdelen:

- `members[]`
- `joint_distribution`, `joint_distribution_totals`
- `box1`, `box2`, `box3` totaalblokken
- `settlement` huishouden
- `verzamelinkomen`

Extra relevante velden:

- `members[].settlement.net_settlement_before_assessment_threshold`
- `members[].settlement.assessment_threshold_applied`
- `members[].box3.tax_before_foreign_dividend`
- `members[].box3.foreign_dividend_tax_credit_applied`

## 4. Opmerking Buitenlandse Dividendbelasting

Buitenlandse dividendbelasting wordt in dit programma als netto invoer/verrekenpost behandeld. De uitgebreide verdrags- en bronstaatberekening valt buiten scope.
