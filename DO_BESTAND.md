# DO Bestand - Invoer, Berekeningen en Output

Dit document beschrijft exact welke invoervelden de applicatie verwacht, welke berekeningen worden uitgevoerd en welke outputvelden worden teruggegeven/getoond.

## 1. Verwachte invoervelden

Invoer gebeurt als JSON payload (web API) of equivalent via de CLI-form.

### 1.1 Huishouden

- `household_id` (string)
- `allocation_strategy` (string): `EQUAL`, `PROPORTIONAL`, `CUSTOM`
- `members` (array van personen)

### 1.2 Persoon (`members[]`)

- `full_name` (string)
- `bsn` (string)
- `residency_status` (string): `RESIDENT` of `NON_RESIDENT`
- `withheld_tax` (number, >= 0)
- `incomes` (array)
- `deductions` (array)
- `tax_credits` (array)
- `assets` (array)
- `own_home` (object, optioneel)

### 1.3 Inkomsten (`incomes[]`)

- `type` (string): `EMPLOYMENT`, `SELF_EMPLOYMENT`, `RENTAL`, `PENSION`, `INVESTMENT`, `OTHER`
- `amount` (number, >= 0)
- `description` (string, optioneel)

### 1.4 Aftrekposten (`deductions[]`)

- `description` (string)
- `amount` (number, >= 0)

### 1.5 Heffingskortingen (`tax_credits[]`)

- `name` (string)
- `amount` (number, >= 0)
- `description` (string, optioneel)

### 1.6 Vermogen (`assets[]`)

- `type` (string): `SAVINGS`, `INVESTMENT`, `REAL_ESTATE`, `BUSINESS`, `OTHER` (intern ook extra assettypes ondersteund)
- `value` (number, >= 0)
- `dividend_tax_paid` (number, >= 0): dividendbelasting betaald op deze beleggingsrekening (alleen niet-spaarvermogen)
- `description` (string, optioneel)

### 1.7 Eigen woning (`own_home`)

- `woz_value` (number, >= 0)
- `period_fraction` (number tussen 0 en 1)

## 2. Exacte berekeningen

De berekeningen volgen de domeinlogica in `object_model.py` en de jaarconfiguratie in `tax_brackets.py`.

### 2.1 Box1 - per persoon

1. `total_gross_income = som(inkomsten)`
2. `eigenwoningforfait = functie(woz_value, period_fraction)` indien eigen woning
3. `total_deductions = som(aftrekposten)`
4. `taxable_income = max(0, total_gross_income + eigenwoningforfait - total_deductions)`
5. Box1-schijven:
- Voor elke schijf: `taxable_in_bracket = bracket.taxable_amount(taxable_income)`
- `tax_in_bracket = taxable_in_bracket * bracket.rate`
6. `box1_tax = som(tax_in_bracket)`
7. `tax_after_credits = max(0, box1_tax - total_tax_credits)`
8. `net_liability = max(0, tax_after_credits - withheld_tax)`
9. `dividend_tax_paid_total = som(asset.dividend_tax_paid voor assets met type != SAVINGS)`
10. `prepaid_taxes = withheld_tax + dividend_tax_paid_total`

### 2.2 Box3 - huishouden

1. Splitsing vermogen:
- `savings_assets = som(assets met type SAVINGS)`
- `investment_assets = som(assets met type != SAVINGS)`
- `total_assets = savings_assets + investment_assets`

2. Fictief rendement:
- `savings_deemed_return = savings_assets * box3_savings_return_rate`
- `investment_deemed_return = investment_assets * box3_investment_return_rate`
- `deemed_return = savings_deemed_return + investment_deemed_return`

3. Heffingsvrij vermogen:
- `tax_free_assets = box3_tax_free_assets_single` bij 1 persoon
- `tax_free_assets = box3_tax_free_assets_partner` bij 2+ personen

4. Correctie volgens formule:
- `corrected_assets = max(total_assets - tax_free_assets, 0)`
- `correction_factor = corrected_assets / total_assets` (0 als total_assets = 0)
- `corrected_deemed_return = correction_factor * deemed_return`

Equivalent geformuleerd:
- `(gecorrigeerd_vermogen / totaal_vermogen) * fictief_rendement = inkomsten uit vermogen van box 3`

5. Box3 belasting:
- `box3_tax = corrected_deemed_return * box3_rate`

6. Verdeling Box3 over personen:
- `EQUAL`: gelijke delen
- `PROPORTIONAL`: verhouding op basis van fictief rendement per persoon
- `CUSTOM`: opgegeven custom-verdeling

### 2.3 Huishoudtotalen en eindafrekening

1. `box1_taxable_income_total = som(taxable_income per persoon)`
2. `verzamelinkomen = box1_taxable_income_total + corrected_deemed_return`
3. `gross_income_tax = box1_total + box3_tax`
4. `total_tax_credits = som(heffingskortingen per persoon)`
5. `total_prepaid_taxes = som(withheld_tax + dividend_tax_paid_total per persoon)`
6. `net_settlement = gross_income_tax - total_tax_credits - total_prepaid_taxes`

Interpretatie:
- `net_settlement > 0`: te betalen
- `net_settlement < 0`: te ontvangen

## 3. Outputvelden

### 3.1 API output (`POST /api/calculate`)

- `success`
- `box1_breakdown` (per persoon):
- `gross_income`
- `deductions`
- `taxable_income`
- `box1_tax`
- `box1_brackets` (toegepaste schijven)
- `tax_credits`
- `withheld_tax`
- `dividend_tax_paid` (totaal over alle beleggingsrekeningen van de persoon)
- `prepaid_taxes`
- `net_liability`
- `assets`
- `box1_total`
- `box1_taxable_income_total`
- `box1_brackets_applied` (geaggregeerde schijven eindafrekening)
- `box3_tax`
- `box3_rate`
- `box3_savings_return_rate`
- `box3_investment_return_rate`
- `box3_savings_assets`
- `box3_investment_assets`
- `box3_savings_deemed_return`
- `box3_investment_deemed_return`
- `box3_correction_factor`
- `box3_corrected_savings_deemed_return`
- `box3_corrected_investment_deemed_return`
- `box3_deemed_return`
- `box3_corrected_deemed_return`
- `box3_tax_free_assets`
- `box3_allocation`
- `total_tax`
- `gross_income_tax`
- `verzamelinkomen`
- `total_prepaid_taxes`
- `total_tax_credits`
- `net_settlement`
- `total_assets`
- `total_income`
- `effective_tax_rate`
- `general_tax_credit`
- `tax_year`
- `input_saved_to`

### 3.2 GUI outputvelden (resultatenpaneel)

- Samenvatting:
- `totalTaxAmount`
- `effectiveRateAmount`
- Box1:
- `box1Details`
- `box1Total`
- Box3:
- `totalAssets`
- `box3Rate`
- `box3Allocation`
- `box3Total`
- Procesflow/Eindafrekening:
- `box1BracketApplication`
- `box3SavingsAssets`
- `box3SavingsDeemedReturn` (gecorrigeerd)
- `box3InvestmentAssets`
- `box3InvestmentDeemedReturn` (gecorrigeerd)
- `box3CorrectionFactor`
- `box1TaxableIncomeTotal`
- `box3DeemedReturn`
- `box3TaxFreeAssets`
- `box3CorrectedDeemedReturn`
- `verzamelinkomen`
- `grossIncomeTax`
- `totalPrepaidTaxes`
- `totalTaxCredits`
- `netSettlement`
- `finalTotalTax`
