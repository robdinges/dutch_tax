# Verslag: Optimale verdeelstaat gezamenlijke posten – Huishouden LR (2025)

## 1. Aanleiding en doel

Dit verslag beschrijft de simulatie die is uitgevoerd om de **optimale verdeling**
van gezamenlijke belastingposten te vinden tussen de twee partners van huishouden LR:
**R (P1)** en **L (P2)**.

Bij fiscale partners mogen een aantal posten (de 'verdeelstaat') vrij worden verdeeld
over beide partners. Door slim te verdelen kan de totale belastinglast worden geminimaliseerd.
Het doel is de combinatie te vinden waarbij het **gezamenlijk te betalen bedrag** zo laag
mogelijk is.

## 2. Aanpak

### 2.1 Invoer

De simulatie maakt gebruik van `submissions/LR_sim.json`, een kopie van het
LR-huishoudbestand (`submissions/LR.json`).

### 2.2 Vrij te verdelen posten en totalen

| Post | Totaal |
|------|-------:|
| Eigenwoningforfait | € 1.326 |
| Aftrek geen/kleine eigenwoningschuld | € 1.017 |
| Grondslag voordeel sparen/beleggen (Box 3) | € 283.527 |
| Ingehouden dividendbelasting | € 780 |
| Ingehouden buitenlandse dividendbelasting | € 4 |
| Vrijstelling groene beleggingen | € 5.613 |

### 2.3 Zoekmethode – twee fasen

#### Fase 1 – Binaire verkenning (logische startbasis)

Eerst wordt per post het **volledige bedrag** óf aan P1 óf aan P2 toegewezen.
Dat levert 2⁶ = **64 combinaties** op — overzichtelijk en snel.
Zo wordt direct zichtbaar welke kant elke post het beste op gaat,
gebaseerd op de daadwerkelijke belastingberekening.

#### Fase 2 – Verfijning rondom de beste binaire combinatie

Voor de posten die niet binair zijn (met name de **grondslag sparen/beleggen**,
de grootste post) worden aanvullend tussenliggende waarden getest (stappen van 5%).
Ook 50/50-splits worden meegenomen zodat geleidelijke verdelingen niet worden gemist.
Zo wordt de definitief optimale verdeling gevonden.

Voor elke combinatie is de belastingberekening uitgevoerd via de `/api/calculate`-endpoint
van de Dutch Tax Calculator. Het totale netto te betalen bedrag (P1 + P2) is vergeleken.

## 3. Uitkomst

### 3.1 Huidige verdeling (startpunt)

| Post | P1 (R) | P2 (L) | Totaal |
|------|-------:|-------:|-------:|
| Eigenwoningforfait | € 1.326 | € 0 | € 1.326 |
| Aftrek geen/kleine eigenwoningschuld | € 1.017 | € 0 | € 1.017 |
| Grondslag voordeel sparen/beleggen (Box 3) | € 270.683 | € 12.844 | € 283.527 |
| Ingehouden dividendbelasting | € 780 | € 0 | € 780 |
| Ingehouden buitenlandse dividendbelasting | € 4 | € 0 | € 4 |
| Vrijstelling groene beleggingen | € 5.359 | € 254 | € 5.613 |

**Netto aanslag P1:** € 3.793
  
**Netto aanslag P2:** € 0
  
**Totaal te betalen:** € 3.793

### 3.2 Fase 1 – Top 10 binaire combinaties

| Rang | Totaal | P1 | P2 | ewf | aftrek | grondslag | div | b.div | groen |
|-----:|-------:|---:|---:|:---:|:------:|:---------:|:---:|:-----:|:-----:|
| 1 | € 3.670 | € -489 | € 4.159 | P2 | P1 | P2 | P2 | P2 | P2 |
| 2 | € 3.670 | € -495 | € 4.165 | P2 | P1 | P2 | P2 | P2 | P1 |
| 3 | € 3.670 | € -1.269 | € 4.939 | P2 | P1 | P2 | P1 | P2 | P2 |
| 4 | € 3.670 | € -1.275 | € 4.945 | P2 | P1 | P2 | P1 | P2 | P1 |
| 5 | € 3.670 | € 4.131 | € -461 | P2 | P1 | P1 | P2 | P1 | P2 |
| 6 | € 3.670 | € 4.125 | € -455 | P2 | P1 | P1 | P2 | P1 | P1 |
| 7 | € 3.670 | € 3.351 | € 319 | P2 | P1 | P1 | P1 | P1 | P2 |
| 8 | € 3.670 | € 3.345 | € 325 | P2 | P1 | P1 | P1 | P1 | P1 |
| 9 | € 3.674 | € -489 | € 4.163 | P2 | P1 | P2 | P2 | P1 | P2 |
| 10 | € 3.674 | € -495 | € 4.169 | P2 | P1 | P2 | P2 | P1 | P1 |

### 3.3 Fase 1 – Per post: effect van alles naar P1 vs. alles naar P2

*(overige posten op de beste binaire waarde van de winnende combinatie)*

| Post | Totaal → P1 | Totaal → P2 | Voordeel |
|------|------------:|------------:|:---------|
| Eigenwoningforfait | € 3.852 | € 3.670 | **P2** (€ 182 goedkoper) |
| Aftrek geen/kleine eigenwoningschuld | € 3.670 | € 3.795 | **P1** (€ -125 goedkoper) |
| Grondslag voordeel sparen/beleggen (Box 3) | € 3.670 | € 3.670 | Gelijk |
| Ingehouden dividendbelasting | € 3.670 | € 3.670 | Gelijk |
| Ingehouden buitenlandse dividendbelasting | € 3.670 | € 3.670 | Gelijk |
| Vrijstelling groene beleggingen | € 3.670 | € 3.670 | Gelijk |

### 3.4 Optimale verdeling (na fase 2)

| Post | P1 (R) | P2 (L) | Totaal |
|------|-------:|-------:|-------:|
| Eigenwoningforfait | € 0 | € 1.326 | € 1.326 |
| Aftrek geen/kleine eigenwoningschuld | € 1.017 | € 0 | € 1.017 |
| Grondslag voordeel sparen/beleggen (Box 3) | € 56.705 | € 226.822 | € 283.527 |
| Ingehouden dividendbelasting | € 390 | € 390 | € 780 |
| Ingehouden buitenlandse dividendbelasting | € 0 | € 4 | € 4 |
| Vrijstelling groene beleggingen | € 0 | € 5.613 | € 5.613 |

**Netto aanslag P1:** € 0
  
**Netto aanslag P2:** € 3.625
  
**Totaal te betalen:** € 3.625

### 3.5 Vergelijking en besparing

| | Huidig | Optimaal | Verschil |
|--|-------:|--------:|---------:|
| Netto aanslag P1 | € 3.793 | € 0 | € -3.793 |
| Netto aanslag P2 | € 0 | € 3.625 | € 3.625 |
| **Totaal te betalen** | **€ 3.793** | **€ 3.625** | **€ 168** |

> **Belastingbesparing: € 168**
>
> Door de gezamenlijke posten optimaal te verdelen, betaalt het huishouden
> € 168 minder belasting ten opzichte van de huidige verdeling.

### 3.6 Toelichting op de optimale keuzes

#### Eigenwoningforfait en aftrek geen/kleine eigenwoningschuld

Het eigenwoningforfait is een bijtelling bij het box 1-inkomen; de aftrek is een aftrekpost.
Door het eigenwoningforfait toe te wijzen aan de partner met het **laagste marginale tarief**
(P2, eerste schijf ~8,17%) en de aftrek aan de partner met het **hoogste marginale tarief**
(P1, derde schijf ~49,5%) wordt de belastingdruk geminimaliseerd.

#### Grondslag voordeel sparen en beleggen (Box 3)

Box 3 kent een vast fictief rendement en een vlak belastingtarief van 36%.
Het totale box 3-belastingbedrag van het huishouden wijzigt nauwelijks door de verdeling.
Wel kan het zinvol zijn om elk van de partners hun volledige heffingsvrij vermogen
(€ 57.684 per persoon in 2025) te benutten.

#### Ingehouden dividendbelasting

De ingehouden dividendbelasting is een voorheffing die als verrekening (korting) dient.
Deze wordt het best toegewezen aan de partner met de **hoogste box 3-belastingschuld**,
zodat de korting volledig benut wordt.

#### Vrijstelling groene beleggingen

De vrijstelling voor groene beleggingen levert ook een heffingskorting op.
Per partner geldt een maximale grondslag voor de korting. Een evenredige verdeling
of concentratie bij één partner hangt af van of de cap per persoon wordt bereikt.

## 4. Gedetailleerde belastingberekening optimale situatie

### Partner 1 – R

| Onderdeel | Bedrag |
|-----------|-------:|
| Belastbaar inkomen Box 1 | € 93.754 |
| Box 1 belasting | € 25.906 |
| Grondslag sparen/beleggen (Box 3) | € 56.704 |
| Box 3 belasting | € 924 |
| Bruto inkomstenbelasting | € 37.458 |
| Heffingskortingen | € 2.234 |
| Voorheffingen | € 35.179 |
| **Netto te betalen** | **€ 0** |

### Partner 2 – L

| Onderdeel | Bedrag |
|-----------|-------:|
| Belastbaar inkomen Box 1 | € 38.164 |
| Box 1 belasting | € 3.117 |
| Grondslag sparen/beleggen (Box 3) | € 226.823 |
| Box 3 belasting | € 3.696 |
| Bruto inkomstenbelasting | € 17.365 |
| Heffingskortingen | € 6.382 |
| Voorheffingen | € 7.358 |
| **Netto te betalen** | **€ 3.625** |

## 5. Conclusie

De simulatie heeft **€ 168 belastingvoordeel** gevonden ten opzichte van de
huidige verdeling door de gezamenlijke posten als volgt te verdelen:

- **Eigenwoningforfait**: € 0 aan P1 / € 1.326 aan P2
- **Aftrek geen/kleine eigenwoningschuld**: € 1.017 aan P1 / € 0 aan P2
- **Grondslag voordeel sparen/beleggen (Box 3)**: € 56.705 aan P1 / € 226.822 aan P2
- **Ingehouden dividendbelasting**: € 390 aan P1 / € 390 aan P2
- **Ingehouden buitenlandse dividendbelasting**: € 0 aan P1 / € 4 aan P2
- **Vrijstelling groene beleggingen**: € 0 aan P1 / € 5.613 aan P2

---

*Gegenereerd door `simulate_optimal_distribution.py` op basis van `submissions/LR_sim.json`.*
