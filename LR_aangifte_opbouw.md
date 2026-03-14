# Aangifte-opbouw LR (2025)

Dit document volgt qua hoofdstukken en volgorde zoveel mogelijk de oorspronkelijke aangifte-uitdraai voor huishouden `LR`.

## Belangrijk Aandachtspunt

Buitenlandse dividenden vereisen in de praktijk een eigen, complexere berekening (per land, bronheffing, verdragsregels en eventuele verrekenbeperkingen).

Voor dit programma is daarom gekozen voor een vereenvoudigde aanpak:
- Alleen het netto te verrekenen bedrag wordt ingevoerd (`foreign_dividend_withholding`).
- De uitgebreide fiscale detailberekening van buitenlandse bronbelasting wordt in dit programma niet uitgevoerd.
- Het ingevoerde buitenlandse bedrag wordt direct als verrekening toegepast op de berekende Box 3-belasting (met ondergrens 0).

## Gegevens Huishouden

- Huishouden-ID: `LR`
- Fiscaal partners: `ja`
- Kinderen: `0`
- Taxjaar: `2025`

## Persoon 1

### Inkomsten uit loondienst

- Werkgever: `werkP1 N.V.`
- Soort inkomsten: `Loon binnen Nederland`
- Loon: `EUR 94.771`
- Loonheffing: `EUR 34.789`
- Arbeidskorting (uit loongegevens): `EUR 3.267`

### Reiskosten / Wajong

- Openbaar vervoer woon-werk: `nee`
- Recht op Wajong in 2025: `nee`

## Persoon 2

### Inkomsten uit loondienst

- Werkgever: `werkP2`
- Soort inkomsten: `Loon binnen Nederland`
- Loon: `EUR 21.822`
- Loonheffing: `EUR 1.600`
- Arbeidskorting (uit loongegevens): `EUR 3.075`

### Pensioen en andere uitkeringen

- Uitkeringsinstantie: `UWV`
- Type: `WIA/IOAW-uitkering`
- Uitkering: `EUR 15.016`
- Loonheffing op uitkering: `EUR 5.368`

## Woningen en Andere Onroerende Zaken

- Eigen woning aanwezig: `ja`
- WOZ-waarde: `EUR 379.000`
- Periode: `heel jaar 2025`
- Tijdelijke verhuur: `nee`
- Erfpachtcanon: `nee`

## Bankrekeningen en Andere Bezittingen

### Bank- en Spaarrekeningen

- Totaal bank- en spaarrekeningen: `EUR 119.247`

### Beleggingen

- Totaal beleggingen (niet-groen): `EUR 279.648`
- Groene beleggingen: `EUR 5.613`

### Schulden

- Totale schulden in box 3: `EUR 0`

## Ingehouden Dividendbelasting

### Binnenlands dividend

- Totaal binnenlandse dividendbelasting: `EUR 780`
- Verdeling:
- Persoon 1: `EUR 780`
- Persoon 2: `EUR 0`

### Buitenlands dividend (vereenvoudigd model)

- Totaal buitenlandse bronbelasting (netto ingevoerd): `EUR 4`
- Verdeling:
- Persoon 1: `EUR 4`
- Persoon 2: `EUR 0`

## Verdelen (Gezamenlijke Posten)

- Inkomsten eigen woning: totaal `EUR 1.326`
- Persoon 1 `EUR 1.326`, Persoon 2 `EUR 0`

- Aftrek geen of kleine eigenwoningschuld: totaal `EUR 1.017`
- Persoon 1 `EUR 1.017`, Persoon 2 `EUR 0`

- Grondslag voordeel sparen en beleggen: totaal `EUR 283.527`
- Persoon 1 `EUR 270.683`, Persoon 2 `EUR 12.844`

- Vrijstelling groene beleggingen: totaal `EUR 5.613`
- Persoon 1 `EUR 5.359`, Persoon 2 `EUR 254`

- Ingehouden dividendbelasting (binnenlands): totaal `EUR 780`
- Persoon 1 `EUR 780`, Persoon 2 `EUR 0`

- Ingehouden buitenlandse dividendbelasting: totaal `EUR 4`
- Persoon 1 `EUR 4`, Persoon 2 `EUR 0`

## Overzicht Belasting en Premies

- Te betalen Persoon 1: `EUR 3.793`
- Te betalen Persoon 2: `EUR 0`
- Totaal te betalen huishouden: `EUR 3.793`

## Berekening Persoon 1 (Samenvatting)

 - Premie volksverzekeringen: `EUR 10.628` (berekend zonder afronding per premie, alleen het totaal wordt naar beneden afgerond)

## Berekening Persoon 2 (Samenvatting)

 - Premie volksverzekeringen: `EUR 10.185` (berekend zonder afronding per premie, alleen het totaal wordt naar beneden afgerond)

## Opmerking Over Gebruik

Dit document is bedoeld als functionele documentatie in aangifte-structuur voor controle en afstemming. Voor buitenlandse dividendverrekening wordt bewust gewerkt met een netto invoerbedrag in plaats van volledige verdrags- en bronstaatberekening.
