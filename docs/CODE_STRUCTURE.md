# Code Structure

Dit document helpt nieuwe ontwikkelaars snel de code te begrijpen.

## Mappenstructuur

```
dutch_tax/
├── dutch_tax/              # Python-pakket met domeinlogica
│   ├── __init__.py
│   ├── models.py           # Domeinmodellen (TaxYearConfig, TaxBracket, Person, …)
│   ├── tax_brackets.py     # Jaarconfiguraties en tarieven per belastingjaar
│   └── tax_form.py         # Interactieve CLI-invoerflow
├── static/
│   ├── app.js              # UI-flow, payloadopbouw en resultatenrendering
│   └── style.css
├── templates/
│   └── index.html          # Formulier- en resultaatlayout
├── tests/                  # Unittests en integratietests
├── docs/                   # Projectdocumentatie
│   ├── CODE_STRUCTURE.md   # Dit bestand
│   ├── DO_BESTAND.md       # Invoer, berekeningsstappen en outputvelden
│   ├── GUI_README.md       # UI-flow en schermuitleg
│   └── LR_aangifte_opbouw.md  # Casusdocumentatie aangifte-opbouw
├── app.py                  # Flask-applicatie: routes en hoofdberekening
├── requirements.txt        # Python-afhankelijkheden
└── README.md
```

## Hoofdonderdelen

- `app.py`
  - Flask-routes, inputnormalisatie en hoofdberekening
- `dutch_tax/models.py`
  - Domeinmodellen (`TaxYearConfig`, `TaxBracket`, `Person`, `Household`, enz.)
- `dutch_tax/tax_brackets.py`
  - Jaarconfiguraties en tarieven
- `dutch_tax/tax_form.py`
  - Interactieve CLI-invoerflow
- `static/app.js`
  - UI-flow, payloadopbouw, resultatenrendering
- `templates/index.html`
  - Formulier- en resultaatlayout
- `submissions/*.json`
  - Opgeslagen casussen (niet ingecheckt)

## Rekenstroom in `app.py`

1. Input ophalen en opslaan (`save_input_data_to_json`).
2. Gezamenlijke huishoudvelden bepalen (woning en box3-totalen).
3. `shared_totals` opbouwen voor partnerverdeling.
4. `normalize_joint_distribution` valideren.
5. Per partner Box 1/2/3 + premies + credits berekenen.
6. Voorheffingen en drempeltoepassing (`<= EUR 57`) op partnerniveau.
7. Huishoudresultaat opbouwen vanuit partnerresultaten.

## Belangrijke helperfuncties

- `dec`, `round_down_euro`, `round_up_euro`
- `compute_box1_bracket_breakdown`
- `split_equal`, `allocate_by_weights`
- `normalize_joint_distribution`
- `compute_green_investment_credit`
- `apply_small_payable_threshold`
- `settlement_result_type`

## Wijzigrichtlijnen

- Houd berekeningslogica in backend (`app.py`), niet in frontend.
- Voeg nieuwe partner-verdeelposten altijd toe op 3 plekken:
  - `shared_totals` backend
  - `JOINT_ITEMS` frontend
  - documentatie (`docs/DO_BESTAND.md` + eventueel casusdoc)
- Voeg voor fiscale uitzonderingen altijd een gerichte unittest toe.
