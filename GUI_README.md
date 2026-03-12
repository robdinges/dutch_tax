# GUI Handleiding - Procesflow Editie

De UI is opgebouwd als workflow met twee kolommen.

- Links: invoer volgens processtappen.
- Rechts: resultaten voor Box 1, Box 2, Box 3 en eindafrekening.

## Schermopbouw

### 1. Invoerblok

1. `Verzamel gegevens`

- Huishouden-ID
- Aantal personen
- Fiscaal partnerschap
- Aantal kinderen

1. `Persoonsdossiers`

Per persoon:

- Basis (naam, BSN, voorheffingen)
- Box 1 inkomsten (inclusief arbeidskorting per inkomensregel)
- Box 1 AOW-status (checkbox per persoon)
- Box 1 overige kortingen
- Box 2 aanmerkelijk belang
- Optioneel custom Box 3 percentage

1. `Eigen woning (huishouden)`

- Eigen woning aanwezig
- WOZ-waarde
- Periode

1. `Box 3 huishouden`

- Vermogen en schulden op huishoudniveau
- Schulden worden als negatieve inkomenspost meegenomen in Box 3 inkomen

1. `Verdeel gezamenlijke posten`

- Getoonde totalen voor:
	- eigenwoningforfait (bijtelling Box 1)
	- aftrek geen of kleine eigenwoningschuld (76,667% van eigenwoningforfait)
	- grondslag voordeel uit sparen en beleggen
	- vrijstelling groene beleggingen
	- ingehouden dividendbelasting
- Per partner invoervelden per post
- Validatie per regel: som partnerbedragen moet gelijk zijn aan totaal
- Knop om verdeling te bevestigen en door te gaan

1. `Controle en berekenen`

- JSON importeren
- Berekening starten

### 2. Resultatenblok

Resultaten worden opgebouwd in fiscale volgorde.

- KPI's: eindresultaat, effectief tarief, verzamelinkomen
- Box 1: detail per persoon + schijven
- Box 2: totaal belastbaar inkomen en belasting
- Box 3: netto vermogen, heffingsvrij vermogen, correctie en toerekening
- Per partner: volledige afrekening met Box 1, Box 2, Box 3, premies, heffingskortingen en voorheffingen
- Verrekening huishouden: totaal van beide partneruitkomsten

## UX-principes

- Elke sectie volgt direct de fiscale flow.
- Formulieren zijn gegroepeerd per box.
- Ontwerp werkt op desktop en mobiel.
- JSON-opslag maakt hergebruik van dossiers makkelijk.

## JSON laden

Via `Laad JSON in formulier` kun je payloads uit `submissions/` terugzetten in de UI.

Ondersteund formaat:

- Wrapped: `{ "saved_at": ..., "data": { ...payload... } }`
- Direct: `{ ...payload... }`

## Starten

```bash
python3 app.py
```

Open `http://127.0.0.1:8000`.
