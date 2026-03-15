"""Centralized user-facing texts for the Dutch Tax Calculator.

All Dutch-language labels, error messages and API response strings are defined
here so they can be reviewed and updated in a single place.
"""

# ---------------------------------------------------------------------------
# Income types (Box 1)
# ---------------------------------------------------------------------------

INCOME_TYPES: list[dict] = [
    {"id": "EMPLOYMENT", "label": "Loon uit dienstverband"},
    {"id": "SELF_EMPLOYMENT", "label": "Winst uit onderneming"},
    {"id": "BENEFITS", "label": "Uitkeringen"},
    {"id": "PENSION", "label": "Pensioen"},
    {"id": "OTHER", "label": "Overig Box 1 inkomen"},
]

# ---------------------------------------------------------------------------
# Deduction types (Box 1)
# ---------------------------------------------------------------------------

BOX1_DEDUCTION_TYPES: list[dict] = [
    {"id": "MORTGAGE_INTEREST", "label": "Hypotheekrente"},
    {"id": "ENTREPRENEUR_ALLOWANCE", "label": "Ondernemersaftrek"},
    {"id": "PERSONAL_ALLOWANCE", "label": "Persoonsgebonden aftrek"},
    {"id": "OTHER", "label": "Overige aftrek"},
]

# ---------------------------------------------------------------------------
# Joint-item allocation strategies
# ---------------------------------------------------------------------------

ALLOCATION_STRATEGIES: list[dict] = [
    {"id": "EQUAL", "label": "Gelijk"},
    {"id": "PROPORTIONAL", "label": "Proportioneel op netto vermogen"},
    {"id": "CUSTOM", "label": "Aangepaste verdeling (%)"},
]

# ---------------------------------------------------------------------------
# Validation / error messages
# ---------------------------------------------------------------------------

ERROR_MIN_ONE_PERSON = "Minimaal 1 persoon is verplicht."
ERROR_DISTRIBUTION_MISSING = "Verdeling voor '{item_key}' ontbreekt of heeft onjuist formaat."
ERROR_DISTRIBUTION_NEGATIVE = "Verdeling voor '{item_key}' bevat negatieve waarde voor '{member_id}'."
ERROR_DISTRIBUTION_SUM = "Verdeling voor '{item_key}' telt op tot {provided_sum} maar moet {total_amount} zijn."
ERROR_PREVIEW = "Preview error: {detail}"
ERROR_CALCULATION = "Calculation error: {detail}"
ERROR_NOT_FOUND = "Page not found"
ERROR_SERVER = "Server error"
