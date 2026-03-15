# Nederlandse Inkomstenbelasting Calculator (Procesflow)

Deze applicatie rekent particuliere Nederlandse inkomstenbelasting door op basis van een vaste procesflow:

1. Gegevens verzamelen
2. Fiscale partner en huishouden bepalen
3. Gegevens per box vastleggen
4. Gezamenlijke posten verdelen over partners
5. Box 1/2/3 en premies per partner berekenen (premies volksverzekeringen: geen afronding per premie, alleen het totaal wordt naar beneden afgerond)
6. Verrekeningen en eindafrekening bepalen

## Kernfunctionaliteit

- Box 1: inkomen, eigenwoningforfait, aftrekposten, schijven, heffingskortingen
- Box 2: aanmerkelijk belang
- Box 3: sparen, beleggen, groene beleggingen, schulden, heffingsvrij vermogen
- Partnerverdeling met somcontrole op gezamenlijke posten
- Binnenlandse dividendbelasting als voorheffing
- Buitenlandse dividendbelasting als aparte verdeelpost en directe verrekening op Box 3-belasting
- Kleine te betalen aanslag-regel: bedragen `<= EUR 57` worden op `EUR 0` gezet
- JSON-opslag/herladen via `submissions/<household_id>.json`

## API-overzicht

- `GET /`
- `GET /api/income-types`
- `GET /api/box1-deduction-types`
- `GET /api/allocation-strategies`
- `POST /api/joint-items-preview`
- `POST /api/calculate`

## Belangrijkste joint distribution posten

- `eigenwoningforfait`
- `aftrek_geen_of_kleine_eigenwoningschuld`
- `grondslag_voordeel_sparen_beleggen`
- `vrijstelling_groene_beleggingen`
- `ingehouden_dividendbelasting`
- `ingehouden_buitenlandse_dividendbelasting`

## Buitenlandse dividendbelasting

Buitenlandse bronbelasting op dividend wordt in dit programma bewust vereenvoudigd verwerkt:

- Alleen een netto te verrekenen bedrag wordt ingevoerd.
- Complexe verdrags- en bronstaatberekeningen worden niet in deze tool uitgevoerd.
- Het ingevoerde bedrag wordt direct verrekend met de berekende Box 3-belasting (met ondergrens `EUR 0`).

## Starten

```bash
python3 app.py
```

Open daarna:

```text
http://127.0.0.1:8000
```

## Documentatie

- `DO_BESTAND.md`: actuele invoer, berekeningsstappen en outputvelden
- `GUI_README.md`: UI-flow en schermuitleg
- `LR_aangifte_opbouw.md`: casusdocumentatie in aangifte-opbouw
- `CODE_STRUCTURE.md`: code-indeling voor ontwikkelaars

## Disclaimer

Deze software is een rekenhulp. Controleer definitieve fiscale regels en bedragen altijd via de Belastingdienst of een fiscalist.
