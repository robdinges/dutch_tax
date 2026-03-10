# DO Bestand - Invoer, Berekening en Output (Procesflow 2026)

Dit document beschrijft de actuele gegevensstructuur en de exacte rekenstappen in de webapp.

## 1. Invoerstructuur

### 1.1 Huishouden

- `household_id` (string)
- `fiscal_partner` (boolean)
- `children_count` (number)
- `allocation_strategy` (`EQUAL` | `PROPORTIONAL` | `CUSTOM`)
- `custom_allocation` (map `member_id -> percentage`)
- `members` (array)

### 1.2 Persoon (`members[]`)

- `member_id` (string)
- `full_name` (string)
- `bsn` (string)
- `wage_withholding` (number)
- `dividend_withholding` (number)
- `other_prepaid_taxes` (number, optioneel)
- `box1` (object)
- `box2` (object)
- `box3` (object)

### 1.3 Box 1

- `box1.incomes[]`: `{ type, amount }`
- `box1.deductions[]`: `{ type, amount }`
- `box1.own_home`: `{ has_own_home, woz_value, period_fraction }`
- `box1.tax_credits[]`: `{ name, amount }`

### 1.4 Box 2

- `box2.has_substantial_interest` (boolean)
- `box2.dividend_income` (number)
- `box2.sale_gain` (number)
- `box2.acquisition_price` (number)

### 1.5 Box 3

- `box3.savings` (number)
- `box3.investments` (number)
- `box3.other_assets` (number)
- `box3.debts` (number)

## 2. Berekeningsstappen

### 2.1 Box 1 (per persoon)

1. `gross_income = sum(incomes.amount)`
2. `eigenwoningforfait` op basis van WOZ en periode (indien eigen woning)
3. `deductions = sum(deductions.amount)`
4. `taxable_income = max(0, gross_income + eigenwoningforfait - deductions)`
5. Box 1 belasting via progressieve schijven uit tax-config
6. Heffingskortingen worden niet automatisch bepaald:
- gebruiker voert meerdere losse posten in
- totaal heffingskortingen = som van ingevoerde posten

### 2.2 Box 2 (per persoon)

Als `has_substantial_interest = true`:

- `box2_taxable_income = max(0, dividend_income + sale_gain - acquisition_price)`
- `box2_tax = box2_taxable_income * box2_rate`

Anders:

- `box2_taxable_income = 0`
- `box2_tax = 0`

### 2.3 Box 3 (huishouden)

1. Vermogen per persoon:
- `gross_assets = savings + investments + other_assets`
- `net_assets = max(0, gross_assets - debts)`

2. Huishoudtotalen:
- `total_net_assets = sum(net_assets)`
- `tax_free_assets = single_heffingsvrij_vermogen * aantal_personen`

3. Fictief rendement:
- eerst nettofactor toepassen om schulden mee te nemen
- `deemed_return_savings = net_savings * savings_return_rate`
- `deemed_return_non_savings = net_non_savings * investment_return_rate`
- `deemed_return_total = deemed_return_savings + deemed_return_non_savings`

4. Correctie heffingsvrij vermogen:
- `corrected_assets = max(total_net_assets - tax_free_assets, 0)`
- `correction_factor = corrected_assets / total_net_assets`
- `box3_income = deemed_return_total * correction_factor`

5. Box 3 belasting:
- `box3_tax = box3_income * box3_rate`

6. Verdeling Box 3 belasting:
- `EQUAL`: gelijk
- `PROPORTIONAL`: naar netto vermogen
- `CUSTOM`: op basis van percentages

### 2.4 Totale belasting en verrekening

- `box1_box3_tax = box1_total + box3_tax`
- Premies volksverzekeringen op premie-basis `min(box1_taxable_income_total, 19.832)`:
- `AOW = 0.0%`
- `Anw = 0.1%`
- `Wlz = 9.65%`
- `gross_income_tax = box1_box3_tax + box2_total + premie_totaal`
- `total_tax_credits = sum(member credits)`
- `total_prepaid_taxes = sum(wage_withholding + dividend_withholding + other_prepaid_taxes)`
- `net_settlement = gross_income_tax - total_tax_credits - total_prepaid_taxes`

Interpretatie:

- `net_settlement >= 0` -> `TE_BETALEN`
- `net_settlement < 0` -> `TERUGGAAF`

## 3. Outputvelden

### 3.1 Response hoofdvelden

- `success`
- `tax_year`
- `fiscal_partner`
- `allocation_strategy`
- `members[]`
- `box1`
- `box2`
- `box3`
- `settlement`
- `verzamelinkomen`
- `filing_steps`
- `input_saved_to`

### 3.2 Settlement-object

- `gross_income_tax`
- `total_tax_credits`
- `total_prepaid_taxes`
- `net_settlement`
- `result_type`
- `effective_rate`

## 4. Aangifte-checklist in output

De API levert standaard:

1. Persoonsgegevens controleren
2. Inkomsten invoeren
3. Woning en hypotheek invoeren
4. Vermogen invoeren
5. Aftrekposten invoeren
6. Partnerverdeling optimaliseren
7. Controle
8. Indienen
