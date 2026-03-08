# Dutch Tax App - Functioneel Ontwerp en Data/Objectmodel (Python)

Dit document beschrijft de werking van de **Python-versie** van de app.

Relevante bronbestanden:
- `object_model.py`
- `tax_brackets.py`
- `tax_form.py`
- `app.py` (Flask weblaag)

## 1. Functioneel overzicht

De applicatie berekent Nederlandse belasting op basis van:
- **Box1**: inkomstenbelasting (progressieve schijven)
- **Box3**: vermogensbelasting (percentage op totale assets)

Ondersteunde gebruiksvormen:
- CLI formulier: `tax_form.py`
- Voorbeelden/demo: `examples.py`, `form_demo.py`
- Web API/UI: `app.py` + `templates/` + `static/`

Hoofdfunctionaliteit:
1. Vastleggen van personen in een huishouden.
2. Registreren van inkomsten, aftrekposten, assets en eventuele heffingskortingen.
3. Berekenen van Box1 per persoon.
4. Berekenen en verdelen van Box3 op huishoudniveau.
5. Opleveren van netto belastingverplichting per persoon en totaal.

## 2. Domeinmodel (Python)

### 2.1 Enums

- `ResidencyStatus`: `RESIDENT`, `NON_RESIDENT`
- `AllocationStrategy`: `EQUAL`, `PROPORTIONAL`, `CUSTOM`
- `IncomeSourceType`: `EMPLOYMENT`, `SELF_EMPLOYMENT`, `RENTAL`, `PENSION`, `INVESTMENT`, `OTHER`
- `AssetType`: `SAVINGS`, `STOCKS`, `BONDS`, `REAL_ESTATE`, `CRYPTO`, `OTHER`

### 2.2 Kernentiteiten

- `IncomeSource`: bron van inkomen (`gross_amount`)
- `Asset`: vermogenscomponent (`value`)
- `Deduction`: aftrekpost (`amount`, `deduction_type`)
- `TaxCredit`: heffingskorting (`amount`)
- `TaxBracket`: schijf (`lower_bound`, `upper_bound`, `rate`)
- `Person`: persoon met inkomsten, assets, aftrekposten, credits en ingehouden belasting
- `Household`: verzameling van personen met gezamenlijke Box3-logica
- `TaxYearConfig`: jaarconfiguratie met schijven en tarieven

### 2.3 Validatieregels in model

- Negatieve bedragen zijn niet toegestaan voor inkomsten, assets, aftrekposten, credits.
- `Person` vereist `name` en `bsn`.
- `TaxBracket.rate` moet tussen `0` en `1` liggen.
- `TaxBracket.upper_bound` moet groter/gelijk zijn aan `lower_bound` (als aanwezig).

## 3. Rekenlogica

### 3.1 Box1 per persoon

In `Person`:
- `total_gross_income()`
- `total_deductions()`
- `compute_taxable_income()` = `max(0, gross - deductions)`
- `compute_box1_tax(brackets)` = som per schijf
- `compute_net_tax_liability(brackets)` = `max(0, max(0, box1 - credits) - withheld_tax)`

### 3.2 Box3 op huishoudniveau

In `Household`:
- `compute_box3_tax(tax_rate)` = `total_asset_value * tax_rate`
- `allocate_box3_between_partners(tax_rate, strategy, custom_allocation)`

Strategieën:
- `EQUAL`: gelijke verdeling
- `PROPORTIONAL`: naar vermogensratio
- `CUSTOM`: handmatige verdeling via dictionary

### 3.3 Totale last per persoon

`compute_total_tax(brackets, box3_rate, box3_strategy)` geeft per BSN:
- `netto_box1 + toegewezen_box3`

## 4. Taxconfiguratie

`tax_brackets.py` bevat:
- Jaarsets voor `2023`, `2024`, `2025`
- `TAX_CONFIGS` dictionary
- `get_tax_config(year)`
- `get_latest_tax_config()`

Inhoud per jaar:
- `box1_brackets`: lijst van `TaxBracket`
- `box3_rate`
- `general_tax_credit`
- `description`

## 5. Functionele datastroom

1. Invoer wordt verzameld (CLI of webformulier).
2. Data wordt gemapt naar domeinobjecten (`Person`, `Household`, etc.).
3. Jaarconfiguratie wordt geladen via `get_latest_tax_config()` of specifiek jaar.
4. Berekeningen worden uitgevoerd in domeinmethoden.
5. Resultaat wordt getoond in terminal of als JSON teruggegeven.

## 6. Uitbreidbaarheid

Nieuwe belastingjaar toevoegen:
1. Voeg een nieuwe `create_20XX_brackets()` functie toe in `tax_brackets.py`.
2. Maak een `TAX_CONFIG_20XX` object.
3. Registreer in `TAX_CONFIGS[20XX]`.

Model uitbreiden:
- Nieuwe inkomens- of assettypes via enums
- Extra validatieregels in `__post_init__`
- Nieuwe allocatiestrategieën in `Household.allocate_box3_between_partners`

## 7. Samenvatting

De Python-versie gebruikt een duidelijk domeinmodel met:
- sterke scheiding tussen data (`object_model.py`) en tariefconfiguratie (`tax_brackets.py`),
- reproduceerbare berekeningen voor Box1 en Box3,
- meerdere interfaces (CLI en web) bovenop dezelfde kernlogica.
