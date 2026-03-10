# GUI Handleiding - Procesflow Editie

De nieuwe UI is opgezet als een compacte workflow met twee kolommen:

- Links: volledige invoer volgens de processtappen
- Rechts: live-resultaten in Box 1, Box 2, Box 3 en eindafrekening

## Schermopbouw

### 1. Invoerblok

Bestaat uit drie stappen:

1. `Verzamel gegevens`
- Huishouden-ID
- Aantal personen
- Fiscaal partnerschap
- Aantal kinderen
- Box 3 verdelingsmethode

2. `Persoonsdossiers`
Per persoon:
- Basis (naam, BSN, voorheffingen)
- Box 1 inkomsten
- Box 1 woning en aftrek
- Box 1 overige kortingen
- Box 2 aanmerkelijk belang
- Box 3 vermogen en schulden
- Optioneel custom Box 3 percentage

3. `Controle en berekenen`
- JSON importeren
- Berekening starten

### 2. Resultatenblok

Resultaten worden opgebouwd in dezelfde volgorde als de fiscale verwerking:

- KPI's: eindresultaat, effectief tarief, verzamelinkomen
- Box 1: detail per persoon + schijven
- Box 2: totaal belastbaar inkomen en belasting
- Box 3: netto vermogen, heffingsvrij vermogen, correctie en toerekening
- Verrekening: bruto belasting, heffingskortingen, voorheffingen, eindafrekening
- Checklist: 8 stappen voor invullen aangifte

## UX-principes

- Elke sectie volgt direct de fiscale flow
- Formulieren zijn gegroepeerd per box om fouten te verminderen
- Het ontwerp werkt op desktop en mobiel
- JSON-opslag maakt hergebruik van dossiers makkelijk

## JSON laden

Via "Laad JSON in formulier" kun je eerder opgeslagen payloads uit `submissions/` direct terugzetten in de UI.

Ondersteund formaat:

- Wrapped: `{ "saved_at": ..., "data": { ...payload... } }`
- Direct: `{ ...payload... }`

## Starten

```bash
python3 app.py
```

Open `http://127.0.0.1:8000`.
