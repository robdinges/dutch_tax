# Nederlandse Inkomstenbelasting Calculator (Procesflow)

Deze applicatie rekent de particuliere Nederlandse inkomstenbelasting door op basis van een volledige procesflow:

1. Gegevens verzamelen
2. Fiscale partner bepalen
3. Inkomsten indelen in boxen
4. Gezamenlijke posten verdelen over partners
5. Box 1/2/3 per partner volledig berekenen
6. Totale belasting + verrekening per partner en huishouden
7. Eindresultaat tonen

De webapp bevat zowel de rekenengine als een overzichtelijke UI die exact op deze flow is ingericht.

## Kernfunctionaliteit

- Box 1: inkomsten met arbeidskorting per regel, huishoud-eigenwoningforfait, aftrekposten, progressieve schijven
- Box 1 kortingen: meerdere losse heffingskortingen die de gebruiker zelf invult
- Box 2: aanmerkelijk belang (>=5%), dividend/verkoop minus verkrijgingsprijs
- Box 3: spaargeld, beleggingen, overige bezittingen, schulden, heffingsvrij vermogen
- Partnerlogica: expliciete verdeling van gezamenlijke posten met somcontrole
- Gezamenlijke posten in verdeling: eigenwoningforfait, grondslag voordeel uit sparen en beleggen, vrijstelling groene beleggingen, ingehouden dividendbelasting
- Premies volksverzekeringen: AOW (0% bij AOW-gerechtigd, anders 17.9%), Anw (0.1%), Wlz (9.65%)
- Eindafrekening: per partner volledig (belasting + premies - kortingen - voorheffingen) en daarna huishoudtotaal
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
- `POST /api/joint-items-preview`
- `POST /api/calculate`

## Belangrijkste invoer (POST /api/calculate)

```json
{
  "household_id": "HH2026-001",
  "fiscal_partner": true,
  "children_count": 1,
  "joint_distribution": {
    "eigenwoningforfait": {
      "123456789": 1050,
      "987654321": 1050
    },
    "grondslag_voordeel_sparen_beleggen": {
      "123456789": 9000,
      "987654321": 6000
    },
    "vrijstelling_groene_beleggingen": {
      "123456789": 1000,
      "987654321": 500
    },
    "ingehouden_dividendbelasting": {
      "123456789": 240,
      "987654321": 60
    }
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
          {"type": "EMPLOYMENT", "amount": 65000, "labor_credit": 2400}
        ],
        "deductions": [
          {"type": "PERSONAL_ALLOWANCE", "name": "Hypotheekrente", "amount": 7000},
          {"type": "PERSONAL_ALLOWANCE", "name": "Giften", "amount": 500}
        ],
        "has_aow": false,
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
  ],
  "household_box1": {
    "own_home": {
      "has_own_home": true,
      "woz_value": 420000,
      "period_fraction": 1
    }
  }
}
```

## Output samenvatting

De response bevat:

- `members[]` met detail per persoon voor Box 1, Box 2, Box 3, premies, voorheffingen en partner-eindafrekening
- `joint_distribution` en `joint_distribution_totals`
- `box1`, `box2`, `box3` huishoudtotalen
- `settlement` met eindafrekening (`TE_BETALEN` of `TERUGGAAF`)
- `verzamelinkomen`

## Documentatie

- `GUI_README.md`: scherm- en UX-uitleg
- `DO_BESTAND.md`: exact invoermodel, formules en outputvelden

## Disclaimer

Deze software is een rekenhulp. Controleer officiële regels en definitieve bedragen altijd via de Belastingdienst of een fiscalist.
