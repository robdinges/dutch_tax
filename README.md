# Nederlandse Inkomstenbelasting Calculator (Procesflow)

Deze applicatie rekent de particuliere Nederlandse inkomstenbelasting door op basis van een volledige procesflow:

1. Gegevens verzamelen
2. Fiscale partner bepalen
3. Inkomsten indelen in boxen
4. Box 1 berekenen
5. Box 2 berekenen
6. Box 3 berekenen (incl. schulden)
7. Totale belasting + verrekening
8. Aangifte-checklist tonen

De webapp bevat zowel de rekenengine als een overzichtelijke UI die exact op deze flow is ingericht.

## Kernfunctionaliteit

- Box 1: inkomsten, eigenwoningforfait, aftrekposten, progressieve schijven
- Box 1 kortingen: meerdere losse heffingskortingen die de gebruiker zelf invult
- Box 2: aanmerkelijk belang (>=5%), dividend/verkoop minus verkrijgingsprijs
- Box 3: spaargeld, beleggingen, overige bezittingen, schulden, heffingsvrij vermogen
- Partnerlogica: verdeling Box 3 met `EQUAL`, `PROPORTIONAL` of `CUSTOM`
- Premies volksverzekeringen: AOW/Anw/Wlz worden na Box1+Box3 toegevoegd
- Eindafrekening: belasting + premies, daarna kortingen, daarna voorheffingen
- JSON-opslag en herladen van invoer via `submissions/<household_id>.json`

## Starten

```bash
python3 app.py
```

Open daarna:

```text
http://127.0.0.1:8000
```

## API-overzicht

- `GET /`
- `GET /api/income-types`
- `GET /api/box1-deduction-types`
- `GET /api/allocation-strategies`
- `POST /api/calculate`

## Belangrijkste invoer (POST /api/calculate)

```json
{
  "household_id": "HH2026-001",
  "fiscal_partner": true,
  "children_count": 1,
  "allocation_strategy": "PROPORTIONAL",
  "custom_allocation": {
    "123456789": 70,
    "987654321": 30
  },
  "members": [
    {
      "member_id": "123456789",
      "full_name": "Jan Jansen",
      "bsn": "123456789",
      "wage_withholding": 12000,
      "dividend_withholding": 300,
      "box1": {
        "incomes": [
          {"type": "EMPLOYMENT", "amount": 65000}
        ],
        "deductions": [
          {"type": "PERSONAL_ALLOWANCE", "name": "Hypotheekrente", "amount": 7000},
          {"type": "PERSONAL_ALLOWANCE", "name": "Giften", "amount": 500}
        ],
        "own_home": {
          "has_own_home": true,
          "woz_value": 420000,
          "period_fraction": 1
        },
        "tax_credits": [
          {"name": "Algemene heffingskorting", "amount": 1500},
          {"name": "Arbeidskorting", "amount": 2400}
        ]
      },
      "box2": {
        "has_substantial_interest": false,
        "dividend_income": 0,
        "sale_gain": 0,
        "acquisition_price": 0
      },
      "box3": {
        "savings": 50000,
        "investments": 25000,
        "other_assets": 0,
        "debts": 10000
      }
    }
  ]
}
```

## Output samenvatting

De response bevat:

- `members[]` met detail per persoon voor Box 1, Box 2, Box 3 en voorheffingen
- `box1`, `box2`, `box3` huishoudtotalen
- `settlement` met eindafrekening (`TE_BETALEN` of `TERUGGAAF`)
- `verzamelinkomen`

## Documentatie

- `GUI_README.md`: scherm- en UX-uitleg
- `DO_BESTAND.md`: exact invoermodel, formules en outputvelden

## Disclaimer

Deze software is een rekenhulp. Controleer officiële regels en definitieve bedragen altijd via de Belastingdienst of een fiscalist.
