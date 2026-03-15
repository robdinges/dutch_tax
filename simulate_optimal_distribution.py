#!/usr/bin/env python3
"""Simulatie van de optimale verdeelstaat voor huishouden LR.

Aanpak (logisch, stap-voor-stap):
  Fase 1 – Binaire verkenning: per post het volledige bedrag toewijzen aan
            P1 óf P2 (2^6 = 64 combinaties). Zo wordt zichtbaar welke kant
            elke post het beste opgaat.
  Fase 2 – Verfijning: voor posten die niet triviaal zijn wordt ook een
            50/50-split getest; voor de grondslag wordt een fijnmazige
            verdeling onderzocht rondom de beste binaire uitkomst.

Invoer: submissions/LR_sim.json (kopie van LR.json)
Uitvoer: verslag in LR_verdeelstaat_optimalisatie.md
"""

from __future__ import annotations

import copy
import json
import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app import app  # noqa: E402

INPUT_FILE = Path(__file__).parent / "submissions" / "LR_sim.json"
REPORT_FILE = Path(__file__).parent / "LR_verdeelstaat_optimalisatie.md"

P1 = "000000001"
P2 = "000000002"
P1_NAAM = "R (P1)"
P2_NAAM = "L (P2)"

ITEMS = [
    "eigenwoningforfait",
    "aftrek_geen_of_kleine_eigenwoningschuld",
    "grondslag_voordeel_sparen_beleggen",
    "ingehouden_dividendbelasting",
    "ingehouden_buitenlandse_dividendbelasting",
    "vrijstelling_groene_beleggingen",
]


# ---------------------------------------------------------------------------
# Hulpfuncties
# ---------------------------------------------------------------------------

def call_api(payload: dict) -> dict:
    """Roep de berekenings-API aan via de Flask-testclient."""
    with app.test_client() as client:
        resp = client.post("/api/calculate", json=payload)
        assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.data}"
        return resp.get_json()


def totaal_nettosaldo(result: dict) -> float:
    """Som van de netto-aanslagen van alle partners (positief = te betalen)."""
    return sum(m["settlement"]["net_settlement"] for m in result["members"])


def partner_saldo(result: dict, member_id: str) -> float:
    for m in result["members"]:
        if m["member_id"] == member_id:
            return m["settlement"]["net_settlement"]
    return 0.0


def build_dist(totalen: dict, p1_shares: dict[str, float]) -> dict:
    """Bouw een verdeeldict op uit P1-aandelen (float 0..1) per post."""
    dist: dict[str, dict[str, float]] = {}
    for key in ITEMS:
        tot = totalen[key]
        p1_amt = round(tot * p1_shares[key])
        p2_amt = round(tot - p1_amt)
        dist[key] = {P1: p1_amt, P2: p2_amt}
    return dist


def build_dist_amounts(totalen: dict, p1_amounts: dict[str, float]) -> dict:
    """Bouw een verdeeldict op uit concrete P1-bedragen per post."""
    dist: dict[str, dict[str, float]] = {}
    for key in ITEMS:
        tot = totalen[key]
        # Afronden naar hele euro's (normale regels)
        p1_amt = round(p1_amounts[key])
        p2_amt = round(tot - p1_amt)
        dist[key] = {P1: p1_amt, P2: p2_amt}
    return dist


def make_payload(base: dict, dist: dict) -> dict:
    p = copy.deepcopy(base)
    p["joint_distribution"] = dist
    return p


def test_combo(base: dict, totalen: dict, p1_shares: dict[str, float]) -> tuple[float, dict, dict]:
    dist = build_dist(totalen, p1_shares)
    result = call_api(make_payload(base, dist))
    return totaal_nettosaldo(result), dist, result


# ---------------------------------------------------------------------------
# Simulatie
# ---------------------------------------------------------------------------

def simulate() -> None:
    wrapper = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    base = wrapper["data"]

    # Haal totalen op via preview-endpoint
    with app.test_client() as client:
        prev = client.post("/api/joint-items-preview", json=base).get_json()
    totalen = prev["joint_distribution_totals"]

    print("Totalen gezamenlijke posten:")
    for key in ITEMS:
        print(f"  {key:<50s}: {totalen[key]:>10,.0f}")
    print()

    # Huidige situatie
    current_result = call_api(base)
    current_dist = {
        key: current_result["joint_distribution"].get(key, {}) for key in ITEMS
    }
    current_total = totaal_nettosaldo(current_result)
    current_p1 = partner_saldo(current_result, P1)
    current_p2 = partner_saldo(current_result, P2)

    print(f"Huidige verdeling  → totaal: {current_total:,.0f}  "
          f"(P1: {current_p1:,.0f}  P2: {current_p2:,.0f})\n")

    # -----------------------------------------------------------------------
    # Fase 1: binaire verkenning – per post alles naar P1 of alles naar P2
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("FASE 1 – Binaire verkenning (2^6 = 64 combinaties)")
    print("=" * 60)

    alle_resultaten: list[tuple[float, dict, dict, dict]] = []

    for bits in product([0.0, 1.0], repeat=len(ITEMS)):
        shares = dict(zip(ITEMS, bits))
        dist = build_dist(totalen, shares)
        result = call_api(make_payload(base, dist))
        totaal = totaal_nettosaldo(result)
        alle_resultaten.append((totaal, shares, dist, result))

    alle_resultaten.sort(key=lambda x: x[0])

    print(f"\nTop 5 uitkomsten (laagste totaal te betalen):")
    print(f"{'Rang':>4}  {'Totaal':>8}  {'P1':>8}  {'P2':>8}  "
          f"  {'ewf':>4}  {'afrk':>4}  {'grond':>5}  {'div':>4}  {'bdiv':>4}  {'groen':>5}")
    print("-" * 80)
    labels = [k[:5] for k in ITEMS]
    for rang, (tot, shares, dist, res) in enumerate(alle_resultaten[:5], 1):
        p1s = partner_saldo(res, P1)
        p2s = partner_saldo(res, P2)
        bits_str = "  ".join(
            f"P{'1' if shares[k] == 1.0 else '2'}" for k in ITEMS
        )
        print(f"{rang:>4}  {tot:>8,.0f}  {p1s:>8,.0f}  {p2s:>8,.0f}  {bits_str}")

    # Beste binaire combinatie
    beste_totaal_f1, beste_shares_f1, beste_dist_f1, beste_result_f1 = alle_resultaten[0]

    print(f"\nBeste binaire combinatie:")
    for key in ITEMS:
        toegewezen = "P1" if beste_shares_f1[key] == 1.0 else "P2"
        bedrag = totalen[key]
        print(f"  {key:<50s}: {bedrag:>8,.0f} → {toegewezen}")
    print(f"  Totaal te betalen: {beste_totaal_f1:,.0f}  "
          f"(P1: {partner_saldo(beste_result_f1, P1):,.0f}  "
          f"P2: {partner_saldo(beste_result_f1, P2):,.0f})")

    # -----------------------------------------------------------------------
    # Fase 2: verfijning rondom beste binaire uitkomst
    #   - Grondslag: fijnmazige stappen (5%-stappen)
    #   - Overige posten: ook 50/50 toevoegen naast beste binaire keuze
    # -----------------------------------------------------------------------
    print()
    print("=" * 60)
    print("FASE 2 – Verfijning rondom de beste binaire uitkomst")
    print("=" * 60)

    grondslag_tot = totalen["grondslag_voordeel_sparen_beleggen"]

    # Kandidaatwaarden voor grondslag P1 (stappen van 5%)
    grondslag_kand = [round(grondslag_tot * i / 20) for i in range(21)]
    # Verwijder duplicaten
    grondslag_kand = sorted(set(grondslag_kand))

    # Voor de overige posten: gebruik de beste binaire keuze én 50/50
    overige_keys = [k for k in ITEMS if k != "grondslag_voordeel_sparen_beleggen"]
    overige_kand: dict[str, list[float]] = {}
    for key in overige_keys:
        best_share = beste_shares_f1[key]
        # 0.0, 0.5, 1.0
        kand = sorted({0.0, 0.5, 1.0, best_share})
        overige_kand[key] = kand

    n_combinaties = len(grondslag_kand) * 1
    for key in overige_keys:
        n_combinaties *= len(overige_kand[key])

    print(f"Aantal te testen combinaties fase 2: {n_combinaties:,}")

    beste_totaal = beste_totaal_f1
    beste_dist = beste_dist_f1
    beste_result = beste_result_f1

    teller = 0
    for grond_p1 in grondslag_kand:
        for overige_combo in product(*[overige_kand[k] for k in overige_keys]):
            shares = dict(zip(overige_keys, overige_combo))
            # Grondslag apart als bedrag
            amounts = {k: round(totalen[k] * shares[k]) for k in overige_keys}
            amounts["grondslag_voordeel_sparen_beleggen"] = grond_p1

            dist = build_dist_amounts(totalen, amounts)
            result = call_api(make_payload(base, dist))
            totaal = totaal_nettosaldo(result)
            teller += 1

            if totaal < beste_totaal:
                beste_totaal = totaal
                beste_dist = dist
                beste_result = result
                p1s = partner_saldo(result, P1)
                p2s = partner_saldo(result, P2)
                print(f"  Nieuw minimum (combo {teller:,}): "
                      f"totaal={totaal:,.0f}  P1={p1s:,.0f}  P2={p2s:,.0f}")

    print(f"\nFase 2 klaar. {teller:,} combinaties getest.")

    beste_p1 = partner_saldo(beste_result, P1)
    beste_p2 = partner_saldo(beste_result, P2)
    besparing = current_total - beste_totaal

    print(f"\n{'=' * 60}")
    print(f"EINDRESULTAAT")
    print(f"{'=' * 60}")
    print(f"Huidige verdeling  : totaal {current_total:,.0f}  "
          f"(P1: {current_p1:,.0f}  P2: {current_p2:,.0f})")
    print(f"Optimale verdeling : totaal {beste_totaal:,.0f}  "
          f"(P1: {beste_p1:,.0f}  P2: {beste_p2:,.0f})")
    print(f"Besparing          : {besparing:,.0f}")
    print()
    print("Optimale verdeling per post:")
    for key in ITEMS:
        v1 = beste_dist[key].get(P1, 0.0)
        v2 = beste_dist[key].get(P2, 0.0)
        print(f"  {key:<50s}: P1={v1:>8,.0f}  P2={v2:>8,.0f}")

    schrijf_verslag(
        current_dist=current_dist,
        current_result=current_result,
        current_total=current_total,
        current_p1=current_p1,
        current_p2=current_p2,
        beste_dist=beste_dist,
        beste_result=beste_result,
        beste_totaal=beste_totaal,
        beste_p1=beste_p1,
        beste_p2=beste_p2,
        besparing=besparing,
        totalen=totalen,
        alle_resultaten_f1=alle_resultaten,
    )
    print(f"\nVerslag geschreven naar: {REPORT_FILE}")


def fmt_euro(v: float) -> str:
    """Formatteer een bedrag als euro met punt als duizendtalscheidingsteken."""
    return f"€ {v:,.0f}".replace(",", ".")


def schrijf_verslag(
    current_dist: dict,
    current_result: dict,
    current_total: float,
    current_p1: float,
    current_p2: float,
    beste_dist: dict,
    beste_result: dict,
    beste_totaal: float,
    beste_p1: float,
    beste_p2: float,
    besparing: float,
    totalen: dict,
    alle_resultaten_f1: list | None = None,
) -> None:
    """Schrijf een Markdown-verslag van de simulatie."""

    def p1_val(dist: dict, key: str) -> float:
        return dist.get(key, {}).get(P1, 0.0)

    def p2_val(dist: dict, key: str) -> float:
        return dist.get(key, {}).get(P2, 0.0)

    def box1_info(result: dict, mid: str) -> dict:
        for m in result["members"]:
            if m["member_id"] == mid:
                return m["box1"]
        return {}

    def box3_info(result: dict, mid: str) -> dict:
        for m in result["members"]:
            if m["member_id"] == mid:
                return m["box3"]
        return {}

    def settlement_info(result: dict, mid: str) -> dict:
        for m in result["members"]:
            if m["member_id"] == mid:
                return m["settlement"]
        return {}

    keys_nl = {
        "eigenwoningforfait": "Eigenwoningforfait",
        "aftrek_geen_of_kleine_eigenwoningschuld": "Aftrek geen/kleine eigenwoningschuld",
        "grondslag_voordeel_sparen_beleggen": "Grondslag voordeel sparen/beleggen (Box 3)",
        "ingehouden_dividendbelasting": "Ingehouden dividendbelasting",
        "ingehouden_buitenlandse_dividendbelasting": "Ingehouden buitenlandse dividendbelasting",
        "vrijstelling_groene_beleggingen": "Vrijstelling groene beleggingen",
    }

    cur_p1_box1 = box1_info(current_result, P1)
    cur_p2_box1 = box1_info(current_result, P2)
    opt_p1_box1 = box1_info(beste_result, P1)
    opt_p2_box1 = box1_info(beste_result, P2)

    cur_p1_box3 = box3_info(current_result, P1)
    cur_p2_box3 = box3_info(current_result, P2)
    opt_p1_box3 = box3_info(beste_result, P1)
    opt_p2_box3 = box3_info(beste_result, P2)

    cur_p1_settle = settlement_info(current_result, P1)
    cur_p2_settle = settlement_info(current_result, P2)
    opt_p1_settle = settlement_info(beste_result, P1)
    opt_p2_settle = settlement_info(beste_result, P2)

    lines: list[str] = []

    lines += [
        "# Verslag: Optimale verdeelstaat gezamenlijke posten – Huishouden LR (2025)",
        "",
        "## 1. Aanleiding en doel",
        "",
        "Dit verslag beschrijft de simulatie die is uitgevoerd om de **optimale verdeling**",
        "van gezamenlijke belastingposten te vinden tussen de twee partners van huishouden LR:",
        f"**{P1_NAAM}** en **{P2_NAAM}**.",
        "",
        "Bij fiscale partners mogen een aantal posten (de 'verdeelstaat') vrij worden verdeeld",
        "over beide partners. Door slim te verdelen kan de totale belastinglast worden geminimaliseerd.",
        "Het doel is de combinatie te vinden waarbij het **gezamenlijk te betalen bedrag** zo laag",
        "mogelijk is.",
        "",
        "## 2. Aanpak",
        "",
        "### 2.1 Invoer",
        "",
        "De simulatie maakt gebruik van `submissions/LR_sim.json`, een kopie van het",
        "LR-huishoudbestand (`submissions/LR.json`).",
        "",
        "### 2.2 Vrij te verdelen posten en totalen",
        "",
        "| Post | Totaal |",
        "|------|-------:|",
    ]
    for key, label in keys_nl.items():
        lines.append(f"| {label} | {fmt_euro(totalen[key])} |")

    lines += [
        "",
        "### 2.3 Zoekmethode – twee fasen",
        "",
        "#### Fase 1 – Binaire verkenning (logische startbasis)",
        "",
        "Eerst wordt per post het **volledige bedrag** óf aan P1 óf aan P2 toegewezen.",
        "Dat levert 2⁶ = **64 combinaties** op — overzichtelijk en snel.",
        "Zo wordt direct zichtbaar welke kant elke post het beste op gaat,",
        "gebaseerd op de daadwerkelijke belastingberekening.",
        "",
        "#### Fase 2 – Verfijning rondom de beste binaire combinatie",
        "",
        "Voor de posten die niet binair zijn (met name de **grondslag sparen/beleggen**,",
        "de grootste post) worden aanvullend tussenliggende waarden getest (stappen van 5%).",
        "Ook 50/50-splits worden meegenomen zodat geleidelijke verdelingen niet worden gemist.",
        "Zo wordt de definitief optimale verdeling gevonden.",
        "",
        "Voor elke combinatie is de belastingberekening uitgevoerd via de `/api/calculate`-endpoint",
        "van de Dutch Tax Calculator. Het totale netto te betalen bedrag (P1 + P2) is vergeleken.",
        "",
        "## 3. Uitkomst",
        "",
        "### 3.1 Huidige verdeling (startpunt)",
        "",
        "| Post | P1 (R) | P2 (L) | Totaal |",
        "|------|-------:|-------:|-------:|",
    ]
    for key, label in keys_nl.items():
        v1 = p1_val(current_dist, key)
        v2 = p2_val(current_dist, key)
        tot = totalen[key]
        lines.append(f"| {label} | {fmt_euro(v1)} | {fmt_euro(v2)} | {fmt_euro(tot)} |")

    lines += [
        "",
        f"**Netto aanslag P1:** {fmt_euro(current_p1)}",
        f"  ",
        f"**Netto aanslag P2:** {fmt_euro(current_p2)}",
        f"  ",
        f"**Totaal te betalen:** {fmt_euro(current_total)}",
        "",
    ]

    # Fase 1 top-10 tabel als die beschikbaar is
    if alle_resultaten_f1:
        lines += [
            "### 3.2 Fase 1 – Top 10 binaire combinaties",
            "",
            "| Rang | Totaal | P1 | P2 | ewf | aftrek | grondslag | div | b.div | groen |",
            "|-----:|-------:|---:|---:|:---:|:------:|:---------:|:---:|:-----:|:-----:|",
        ]
        for rang, (tot, shares, dist, res) in enumerate(alle_resultaten_f1[:10], 1):
            p1s = partner_saldo(res, P1)
            p2s = partner_saldo(res, P2)
            cols = [
                "P1" if shares[k] == 1.0 else "P2" for k in ITEMS
            ]
            lines.append(
                f"| {rang} | {fmt_euro(tot)} | {fmt_euro(p1s)} | {fmt_euro(p2s)} | "
                + " | ".join(cols) + " |"
            )
        lines.append("")

        # Per post laten zien welke kant beter is (enkelvoudige test)
        lines += [
            "### 3.3 Fase 1 – Per post: effect van alles naar P1 vs. alles naar P2",
            "",
            "*(overige posten op de beste binaire waarde van de winnende combinatie)*",
            "",
            "| Post | Totaal → P1 | Totaal → P2 | Voordeel |",
            "|------|------------:|------------:|:---------|",
        ]
        best_shares = alle_resultaten_f1[0][1]
        for key, label in keys_nl.items():
            # Zoek de laagste totaal waarbij deze post volledig bij P1 zit
            # en de rest op hun beste waarde
            min_p1 = min(
                (t for t, s, d, r in alle_resultaten_f1 if s[key] == 1.0),
                default=float("inf"),
            )
            min_p2 = min(
                (t for t, s, d, r in alle_resultaten_f1 if s[key] == 0.0),
                default=float("inf"),
            )
            if min_p1 < min_p2:
                voordeel = f"**P1** ({fmt_euro(min_p1 - min_p2)} goedkoper)"
            elif min_p2 < min_p1:
                voordeel = f"**P2** ({fmt_euro(min_p1 - min_p2)} goedkoper)"
            else:
                voordeel = "Gelijk"
            lines.append(
                f"| {label} | {fmt_euro(min_p1)} | {fmt_euro(min_p2)} | {voordeel} |"
            )
        lines.append("")

    lines += [
        "### 3.4 Optimale verdeling (na fase 2)",
        "",
        "| Post | P1 (R) | P2 (L) | Totaal |",
        "|------|-------:|-------:|-------:|",
    ]
    for key, label in keys_nl.items():
        v1 = p1_val(beste_dist, key)
        v2 = p2_val(beste_dist, key)
        tot = totalen[key]
        lines.append(f"| {label} | {fmt_euro(v1)} | {fmt_euro(v2)} | {fmt_euro(tot)} |")

    lines += [
        "",
        f"**Netto aanslag P1:** {fmt_euro(beste_p1)}",
        f"  ",
        f"**Netto aanslag P2:** {fmt_euro(beste_p2)}",
        f"  ",
        f"**Totaal te betalen:** {fmt_euro(beste_totaal)}",
        "",
        "### 3.5 Vergelijking en besparing",
        "",
        "| | Huidig | Optimaal | Verschil |",
        "|--|-------:|--------:|---------:|",
        f"| Netto aanslag P1 | {fmt_euro(current_p1)} | {fmt_euro(beste_p1)} "
        f"| {fmt_euro(beste_p1 - current_p1)} |",
        f"| Netto aanslag P2 | {fmt_euro(current_p2)} | {fmt_euro(beste_p2)} "
        f"| {fmt_euro(beste_p2 - current_p2)} |",
        f"| **Totaal te betalen** | **{fmt_euro(current_total)}** | **{fmt_euro(beste_totaal)}** "
        f"| **{fmt_euro(besparing)}** |",
        "",
    ]

    if besparing > 0:
        lines += [
            f"> **Belastingbesparing: {fmt_euro(besparing)}**",
            ">",
            "> Door de gezamenlijke posten optimaal te verdelen, betaalt het huishouden",
            f"> {fmt_euro(besparing)} minder belasting ten opzichte van de huidige verdeling.",
            "",
        ]
    else:
        lines += [
            "> De huidige verdeling is al optimaal (of levert hetzelfde resultaat).",
            "",
        ]

    lines += [
        "### 3.6 Toelichting op de optimale keuzes",
        "",
        "#### Eigenwoningforfait en aftrek geen/kleine eigenwoningschuld",
        "",
        "Het eigenwoningforfait is een bijtelling bij het box 1-inkomen; de aftrek is een aftrekpost.",
        "Door het eigenwoningforfait toe te wijzen aan de partner met het **laagste marginale tarief**",
        "(P2, eerste schijf ~8,17%) en de aftrek aan de partner met het **hoogste marginale tarief**",
        "(P1, derde schijf ~49,5%) wordt de belastingdruk geminimaliseerd.",
        "",
        "#### Grondslag voordeel sparen en beleggen (Box 3)",
        "",
        "Box 3 kent een vast fictief rendement en een vlak belastingtarief van 36%.",
        "Het totale box 3-belastingbedrag van het huishouden wijzigt nauwelijks door de verdeling.",
        "Wel kan het zinvol zijn om elk van de partners hun volledige heffingsvrij vermogen",
        "(€ 57.684 per persoon in 2025) te benutten.",
        "",
        "#### Ingehouden dividendbelasting",
        "",
        "De ingehouden dividendbelasting is een voorheffing die als verrekening (korting) dient.",
        "Deze wordt het best toegewezen aan de partner met de **hoogste box 3-belastingschuld**,",
        "zodat de korting volledig benut wordt.",
        "",
        "#### Vrijstelling groene beleggingen",
        "",
        "De vrijstelling voor groene beleggingen levert ook een heffingskorting op.",
        "Per partner geldt een maximale grondslag voor de korting. Een evenredige verdeling",
        "of concentratie bij één partner hangt af van of de cap per persoon wordt bereikt.",
        "",
        "## 4. Gedetailleerde belastingberekening optimale situatie",
        "",
        "### Partner 1 – R",
        "",
        f"| Onderdeel | Bedrag |",
        f"|-----------|-------:|",
        f"| Belastbaar inkomen Box 1 | {fmt_euro(opt_p1_box1.get('taxable_income', 0))} |",
        f"| Box 1 belasting | {fmt_euro(opt_p1_box1.get('tax', 0))} |",
        f"| Grondslag sparen/beleggen (Box 3) | {fmt_euro(opt_p1_box3.get('grondslag_sparen_beleggen', 0))} |",
        f"| Box 3 belasting | {fmt_euro(opt_p1_box3.get('tax', 0))} |",
        f"| Bruto inkomstenbelasting | {fmt_euro(opt_p1_settle.get('gross_income_tax', 0))} |",
        f"| Heffingskortingen | {fmt_euro(opt_p1_settle.get('tax_credits', 0))} |",
        f"| Voorheffingen | {fmt_euro(opt_p1_settle.get('prepaid_taxes', 0))} |",
        f"| **Netto te betalen** | **{fmt_euro(opt_p1_settle.get('net_settlement', 0))}** |",
        "",
        "### Partner 2 – L",
        "",
        f"| Onderdeel | Bedrag |",
        f"|-----------|-------:|",
        f"| Belastbaar inkomen Box 1 | {fmt_euro(opt_p2_box1.get('taxable_income', 0))} |",
        f"| Box 1 belasting | {fmt_euro(opt_p2_box1.get('tax', 0))} |",
        f"| Grondslag sparen/beleggen (Box 3) | {fmt_euro(opt_p2_box3.get('grondslag_sparen_beleggen', 0))} |",
        f"| Box 3 belasting | {fmt_euro(opt_p2_box3.get('tax', 0))} |",
        f"| Bruto inkomstenbelasting | {fmt_euro(opt_p2_settle.get('gross_income_tax', 0))} |",
        f"| Heffingskortingen | {fmt_euro(opt_p2_settle.get('tax_credits', 0))} |",
        f"| Voorheffingen | {fmt_euro(opt_p2_settle.get('prepaid_taxes', 0))} |",
        f"| **Netto te betalen** | **{fmt_euro(opt_p2_settle.get('net_settlement', 0))}** |",
        "",
        "## 5. Conclusie",
        "",
        f"De simulatie heeft **{fmt_euro(besparing)} belastingvoordeel** gevonden ten opzichte van de",
        "huidige verdeling door de gezamenlijke posten als volgt te verdelen:",
        "",
    ]
    for key, label in keys_nl.items():
        v1 = p1_val(beste_dist, key)
        v2 = p2_val(beste_dist, key)
        lines.append(f"- **{label}**: {fmt_euro(v1)} aan P1 / {fmt_euro(v2)} aan P2")

    lines += [
        "",
        "---",
        "",
        "*Gegenereerd door `simulate_optimal_distribution.py` op basis van `submissions/LR_sim.json`.*",
    ]

    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    simulate()
