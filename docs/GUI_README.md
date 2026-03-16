# GUI Handleiding - Procesflow Editie

## Schermindeling

- Links: invoerflow
- Rechts: resultaten en samenvattingen

## Invoerflow

1. `Verzamel gegevens`
- Huishouden-ID
- Aantal personen
- Fiscaal partnerschap
- Aantal kinderen
- JSON laden

2. `Persoonsdossiers`
- Naam/BSN
- Box 1 inkomensregels
- AOW-status
- Persoonsgebonden aftrek
- Box 2 gegevens
- Heffingskortingen

3. `Eigen woning (huishouden)`
- Aan/uit
- WOZ
- Periode

4. `Box 3 (huishouden)`
- Spaarrekeningen
- Beleggingsrekeningen
- Overige bezittingen
- Schulden
- Per beleggingsrekening:
- `dividend_withholding` (binnenlands)
- `foreign_dividend_withholding` (buitenlands, netto verrekenbedrag)

5. `Verdeel gezamenlijke posten`
- Eigenwoningforfait
- Aftrek kleine/geen eigenwoningschuld
- Grondslag sparen/beleggen
- Vrijstelling groene beleggingen
- Ingehouden dividendbelasting (binnenlands)
- Ingehouden buitenlandse dividendbelasting
- Validatie: som partnerbedragen moet per regel gelijk zijn aan totaal

6. `Controle en berekenen`
- Alleen mogelijk na bevestigde geldige verdeling

## Resultaten

- KPI's: nettoresultaat, effectief tarief, verzamelinkomen
- Box 1, Box 2, Box 3 details
- Per partner:
- Box 3 belasting voor en na verrekening buitenlands dividend
- Heffingskortingen inclusief groene-beleggingenkorting
- Voorheffingen en eindafrekening
- Huishouden:
- nettoresultaat na kleine-aanslagregel (`<= EUR 57` => `NIETS_TE_BETALEN` op persoonsniveau)

## JSON-formaat

Ondersteund:

- Wrapped: `{ "saved_at": ..., "data": { ...payload... } }`
- Direct: `{ ...payload... }`

## Starten

```bash
python3 app.py
```

Open `http://127.0.0.1:8000`.
