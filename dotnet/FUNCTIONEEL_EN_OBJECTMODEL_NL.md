# Dutch Tax App - Functioneel Ontwerp en Data/Objectmodel

Dit document beschrijft de functionele werking van de .NET versie en de opzet van het data- en objectmodel.

Scope:
- Frontend + API in `dotnet/DutchTax.Web`
- Berekeningen in `TaxCalculatorService`
- Domeinmodellen en tax-configuratie in `Models`

## 1. Functionele werking

De applicatie berekent voor een huishouden:
- Box1 inkomstenbelasting per persoon
- Box3 vermogensbelasting op huishoudniveau
- Totale belasting en effectieve belastingdruk

Gebruikersflow:
1. Gebruiker vult in het webformulier leden, inkomens, aftrekposten, ingehouden belasting en assets in.
2. Frontend stuurt JSON naar `POST /api/calculate`.
3. Backend valideert/parset invoer en rekent Box1 + Box3 uit.
4. Frontend toont uitsplitsing per persoon en totalen.

Belangrijk:
- Er is geen database; berekening gebeurt volledig in-memory per request.
- Taxjaarconfiguratie is hardcoded in code (2023, 2024, 2025).

## 2. Systeemopzet

Technische lagen:
- Presentatie: `wwwroot/index.html`, `wwwroot/app.js`, `wwwroot/style.css`
- API: `Program.cs` (Minimal API endpoints)
- Domein/data: `Models/DomainModels.cs`, `Models/ApiModels.cs`
- Berekeningslogica: `Services/TaxCalculatorService.cs`

Belangrijkste endpoints:
- `GET /api/income-types`
- `GET /api/asset-types`
- `GET /api/allocation-strategies`
- `POST /api/calculate`

## 3. Data contract (API)

Inkomend request (`TaxRequest`):
- `household_id`: string
- `allocation_strategy`: `EQUAL | PROPORTIONAL | CUSTOM`
- `members`: lijst van `MemberRequest`

Per `MemberRequest`:
- `full_name`, `bsn`, `residency_status`
- `incomes[]`: type + amount + description
- `deductions[]`: description + amount
- `withheld_tax`
- `assets[]`: type + value + description

Uitgaand response (`TaxCalculationResponse`):
- `box1_breakdown` per persoon
- `box1_total`, `box3_tax`, `box3_rate`
- `box3_allocation` per persoon
- `total_tax`, `total_assets`, `total_income`
- `effective_tax_rate`, `general_tax_credit`, `tax_year`

## 4. Objectmodel (domein)

Enums:
- `ResidencyStatus`: `RESIDENT`, `NON_RESIDENT`
- `AllocationStrategy`: `EQUAL`, `PROPORTIONAL`, `CUSTOM`
- `IncomeSourceType`: `EMPLOYMENT`, `SELF_EMPLOYMENT`, `RENTAL`, `PENSION`, `INVESTMENT`, `OTHER`
- `AssetType`: `SAVINGS`, `INVESTMENT`, `REAL_ESTATE`, `BUSINESS`, `OTHER`

Kernentiteiten:
- `IncomeSource`: naam, type, bruto bedrag
- `Asset`: naam, type, waarde
- `Deduction`: naam, bedrag, type
- `TaxCredit`: naam, bedrag
- `TaxBracket`: ondergrens, bovengrens, tarief
- `TaxYearConfig`: jaar, Box1 schijven, Box3 tarief, algemene heffingskorting

Taxconfig-register:
- `TaxConfigs.ByYear`: dictionary met jaarconfiguraties
- `TaxConfigs.Latest`: laatste jaar op basis van key

## 5. Rekenmodel

### 5.1 Box1 per persoon

Voor elke persoon:
1. `gross_income` = som van alle income amounts
2. `deductions` = som van aftrekposten
3. `taxable_income` = `max(0, gross_income - deductions)`
4. `box1_tax` = progressieve berekening over alle `TaxBracket` regels
5. `tax_after_credits` = `max(0, box1_tax - tax_credits)`
6. `net_liability` = `max(0, tax_after_credits - withheld_tax)`

Opmerking:
- In de huidige .NET implementatie worden `tax_credits` nog niet via request gevuld en zijn dus standaard 0.

### 5.2 Box3 op huishoudniveau

1. `total_assets` = som van alle asset values in huishouden
2. `box3_tax` = `total_assets * box3_rate`
3. Verdeling (`box3_allocation`) via `allocation_strategy`:
   - `EQUAL`: gelijk deel per persoon
   - `PROPORTIONAL`: op basis van vermogensratio
   - `CUSTOM`: momenteel fallback naar gelijke verdeling in de service

### 5.3 Totaal

Per persoon: `net_box1 + box3_share`

Huishoudtotaal:
- `total_tax` = som van alle persoonslasten
- `effective_tax_rate` = `(total_tax / total_income) * 100` (afgerond op 2 decimalen)

## 6. Validatie en defaults

Bij parsing (`ParseMember`):
- Lege naam -> `Unknown`
- Lege BSN -> gegenereerde 9-karakter fallback
- Negatieve bedragen in inkomsten/aftrek/assets worden genegeerd door filtering
- Onbekende enumwaarden vallen terug op `OTHER` of `RESIDENT`
- `withheld_tax` wordt minimaal 0

## 7. Verschil met Python model

De Python versie (`object_model.py`) bevat een uitgebreider pure-domain model met vergelijkbare concepten.
De .NET versie gebruikt dezelfde functionele kern, maar met:
- API-gestructureerde request/response modellen
- Berekening in één service (`TaxCalculatorService`)
- Minimal API in plaats van Flask endpoints

## 8. Uitbreidbaarheid

Nieuwe taxjaar toevoegen:
1. Voeg nieuw `TaxYearConfig` object toe in `TaxConfigs.ByYear`
2. Zet nieuwe `TaxBracket` lijst en rates
3. `Latest` pakt automatisch het hoogste jaar

Aanbevolen vervolgstappen:
- `CUSTOM` Box3 allocatie echt ondersteunen via inputpercentages
- `TaxCredit` invoer opnemen in API request
- Unit tests toevoegen op schijfgrenzen en allocaties
