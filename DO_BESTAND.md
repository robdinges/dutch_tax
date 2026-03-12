# DO Bestand - Invoer, Berekening en Output (Procesflow 2026)

Dit document beschrijft de actuele gegevensstructuur en rekenstappen in de webapp.

## 1. Invoerstructuur

### 1.1 Huishouden

- `household_id` (string)
- `fiscal_partner` (boolean)
- `children_count` (number)
- `joint_distribution` (object met verdeling van gezamenlijke posten per `member_id`)
- `household_box1.own_home`: `{ has_own_home, woz_value, period_fraction }`
- `box3_household` (object)
- `members` (array)

`joint_distribution` bevat:

- `eigenwoningforfait`: `{ member_id: amount }`
- `aftrek_geen_of_kleine_eigenwoningschuld`: `{ member_id: amount }`
- `grondslag_voordeel_sparen_beleggen`: `{ member_id: amount }`
- `vrijstelling_groene_beleggingen`: `{ member_id: amount }`
- `ingehouden_dividendbelasting`: `{ member_id: amount }`

### 1.2 Persoon (`members[]`)

- `member_id` (string)
- `full_name` (string)
- `bsn` (string)
- `wage_withholding` (number)
- `dividend_withholding` (number, optioneel)
- `other_prepaid_taxes` (number, optioneel)
- `box1` (object)
- `box2` (object)

### 1.3 Box 1

- `box1.incomes[]`: `{ type, amount, labor_credit, source }`
- `box1.deductions[]`: `{ type, name, amount }`
- `box1.has_aow`: boolean (ontvangt al AOW)
- `box1.tax_credits[]`: `{ name, amount }`

### 1.4 Box 2

- `box2.has_substantial_interest` (boolean)
- `box2.dividend_income` (number)
- `box2.sale_gain` (number)
- `box2.acquisition_price` (number)

### 1.5 Box 3 (huishouden)

- `box3_household.savings_accounts[]`: `{ name, amount, is_green }`
- `box3_household.investment_accounts[]`: `{ name, amount, is_green, dividend_withholding }`
- `box3_household.other_assets_items[]`: `{ name, amount }`
- `box3_household.debt_items[]`: `{ name, amount }`

## 2. Berekeningsstappen

### 2.1 Box 1 (per persoon)

1. Per inkomensregel: `net_line_income = amount - labor_credit`.
1. `gross_income = sum(amount)`.
1. Huishoudelijk eigenwoningforfait op basis van WOZ en periode.
1. Eigenwoningforfait per persoon volgens `joint_distribution.eigenwoningforfait` (bijtelling).
1. Aftrek geen/kleine eigenwoningschuld per persoon volgens `joint_distribution.aftrek_geen_of_kleine_eigenwoningschuld`.
1. `deductions = sum(deductions.amount)`.
1. `taxable_income = max(0, gross_income + eigenwoningforfait_share - aftrek_geen_of_kleine_eigenwoningschuld_share - deductions)`.
1. Box 1 belasting via progressieve schijven.

### 2.2 Box 2 (per persoon)

Als `has_substantial_interest = true`:

- `box2_taxable_income = max(0, dividend_income + sale_gain - acquisition_price)`
- `box2_tax = box2_taxable_income * box2_rate`

Anders:

- `box2_taxable_income = 0`
- `box2_tax = 0`

### 2.3 Box 3 (huishouden)

`Groen sparen` en `groene beleggingen` tellen niet mee in de totale grondslag voor sparen/beleggen.

1. Vermogenscomponenten:

- `gross_assets = savings + investments + other_assets`
- `total_debts = sum(abs(debt_items.amount))`
- `total_net_assets = max(0, gross_assets - total_debts)`

1. Fictief rendement:

- `deemed_return_savings = net_savings * savings_return_rate`
- `deemed_return_non_savings = net_non_savings * investment_return_rate`
- `deemed_return_total = deemed_return_savings + deemed_return_non_savings`

1. Correctie heffingsvrij vermogen:

- `corrected_assets = max(total_net_assets - tax_free_assets, 0)`
- `correction_factor = corrected_assets / total_net_assets`
- `deemed_income_before_debts = deemed_return_total * correction_factor`

1. Schulden als negatieve inkomenspost:

- `debt_negative_income_post = -total_debts`
- `box3_income = deemed_income_before_debts + debt_negative_income_post`
- `box3_taxable_income = max(0, box3_income)`
- `box3_tax = box3_taxable_income * box3_rate`

1. Gezamenlijke grondslag wordt verdeeld volgens `joint_distribution.grondslag_voordeel_sparen_beleggen`.
1. Vrijstelling groene beleggingen wordt verdeeld volgens `joint_distribution.vrijstelling_groene_beleggingen`.
1. Per persoon:

- `box3_taxable_income_member = max(0, grondslag_share - green_exemption_share)`
- `box3_tax_member = box3_taxable_income_member * box3_rate`

### 2.4 Premies volksverzekeringen

Op basis van Box 1 belastbaar inkomen per persoon:

- `AOW = 17.9%`, behalve `0%` bij `box1.has_aow = true`
- `Anw = 0.1%`
- `Wlz = 9.65%`

### 2.5 Totale belasting en verrekening

- `box1_box3_tax = box1_total + box3_tax`
- `gross_income_tax = box1_box3_tax + box2_total + premie_totaal`
- `total_tax_credits = sum(member credits)`
- `dividend_withholding` per persoon komt uit `joint_distribution.ingehouden_dividendbelasting`
- `total_prepaid_taxes = sum(wage_withholding + dividend_withholding + other_prepaid_taxes)`

Per persoon:

- `gross_income_tax_member = box1_tax + box2_tax + box3_tax + premium_total`
- `net_settlement_member = gross_income_tax_member - tax_credits - prepaid_taxes`

Huishouden:

- `net_settlement = sum(net_settlement_member)`
- `net_settlement = gross_income_tax - total_tax_credits - total_prepaid_taxes`

Interpretatie:

- `net_settlement >= 0` -> `TE_BETALEN`
- `net_settlement < 0` -> `TERUGGAAF`

## 3. Outputvelden

### 3.1 Response hoofdvelden

- `success`
- `tax_year`
- `fiscal_partner`
- `joint_distribution`
- `joint_distribution_totals`
- `members[]`
- `box1`
- `box2`
- `box3`
- `settlement`
- `verzamelinkomen`
- `input_saved_to`

### 3.2 Settlement-object

- `gross_income_tax`
- `total_tax_credits`
- `total_prepaid_taxes`
- `net_settlement`
- `result_type`
- `effective_rate`

## 4. Opmerking

De checklist-uitvoer is verwijderd uit API-response en UI.
