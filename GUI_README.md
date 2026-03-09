# Nederlandse Belastingcalculator - Web GUI

Webinterface voor berekening van inkomstenbelasting op basis van Box1 en Box3 (belastingjaar 2025).

## Wat is nieuw in de GUI

- Volledig Nederlandstalige schermteksten.
- Invoer in 3 logische tabs:
1. `Huishouden`
2. `Personen`
3. `Importeren & Berekenen`
- Per persoon ondersteuning voor:
- inkomstenbronnen
- aftrekposten
- heffingskortingen
- eigen woning (WOZ + periode)
- voorheffingen (loonheffing + dividendbelasting)
- Box3-vermogen
- Resultaten met procesflow:
- Box1 belastbaar inkomen
- Box3 fictief rendement
- correctie heffingsvrij vermogen
- verzamelinkomen
- bruto inkomstenbelasting
- voorheffingen + heffingskortingen
- eindafrekening

## Starten

```bash
python3 app.py
```

Of expliciet met dezelfde interpreter als tests:

```bash
/usr/local/bin/python3.11 app.py
```

Open daarna:

```text
http://127.0.0.1:8000
```

## Procesflow in de GUI

### 1. Huishouden

- `Huishouden-ID`
- `Aantal personen`
- Box3-verdelingsmethode:
- `Gelijk`
- `Proportioneel (op fictief rendement)`
- `Aangepaste percentages`

### 2. Personen

Per persoon:

- Basis:
- naam, BSN, fiscale woonstatus
- Inkomsten:
- type + bedrag
- Aftrekposten:
- omschrijving + bedrag
- Heffingskortingen:
- naam + bedrag (bijv. arbeidskorting, ouderenkorting)
- Eigen woning:
- aan/uit
- WOZ-waarde
- periode (0-1)
- Voorheffingen:
- ingehouden loonheffing
- betaalde dividendbelasting
- Vermogen (Box3):
- type + waarde + dividendbelasting per beleggingsrekening

### 3. Importeren & Berekenen

- JSON-bestand kiezen en laden uit `submissions/`
- Berekening starten

## Resultatenpaneel

Toont:

- Box1 detail per persoon
- Box3 detail en verdeling
- Procesflow-overzicht:
- Box1 belastbaar inkomen totaal
- Box3 fictief rendement
- toegepast heffingsvrij vermogen
- Box3 gecorrigeerd fictief rendement
- correctiefactor: `(gecorrigeerd_vermogen / totaal_vermogen)`
- verzamelinkomen
- bruto inkomstenbelasting (Box1 + Box3)
- voorheffingen (loon + dividend)
- heffingskortingen
- eindafrekening

Zie ook `DO_BESTAND.md` voor volledige specificatie van invoervelden, exacte formules en outputvelden.

## JSON-invoer opslaan/laden

- Elke `POST /api/calculate` wordt opgeslagen in:
- `submissions/<household_id>.json`
- In de GUI kun je deze JSON opnieuw laden via tab `Importeren & Berekenen`.

## API-endpoints

- `GET /`
- `GET /api/income-types`
- `GET /api/asset-types`
- `GET /api/allocation-strategies`
- `POST /api/calculate`

## Opmerking

Deze tool is een rekenhulp. Voor officiële aangifte en definitieve bedragen: controleer altijd bij de Belastingdienst of een fiscalist.
