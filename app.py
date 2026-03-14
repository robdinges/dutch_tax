"""Dutch Tax Calculator web application (procesflow versie)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import json
from pathlib import Path
import re

from flask import Flask, jsonify, render_template, request

from object_model import calculate_eigenwoningforfait
from tax_brackets import get_latest_tax_config

app = Flask(__name__)
app.config["SECRET_KEY"] = "dutch-tax-calculator-secret"


BOX2_RATE_2025 = Decimal("0.269")
SMALL_OWN_HOME_DEBT_DEDUCTION_RATE = Decimal("0.76667")
SMALL_PAYABLE_ASSESSMENT_THRESHOLD = Decimal("57")


def dec(value: object, default: str = "0") -> Decimal:
    """Convert value to Decimal safely."""
    if value in (None, ""):
        return Decimal(default)
    return Decimal(str(value))


def round_down_euro(value: Decimal) -> Decimal:
    return value.quantize(Decimal("1"), rounding=ROUND_FLOOR)


def round_up_euro(value: Decimal) -> Decimal:
    return value.quantize(Decimal("1"), rounding=ROUND_CEILING)


def save_input_data_to_json(data: dict) -> str:
    """Persist submitted form data to a stable JSON file per household ID."""
    submissions_dir = Path(__file__).parent / "submissions"
    submissions_dir.mkdir(parents=True, exist_ok=True)

    household_id = str(data.get("household_id", "WEB_001")).strip() or "WEB_001"
    safe_household_id = re.sub(r"[^A-Za-z0-9_-]", "_", household_id)
    file_path = submissions_dir / f"{safe_household_id}.json"

    payload = {
        "saved_at": datetime.now().isoformat(),
        "household_id": household_id,
        "data": data,
    }
    file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(file_path)


def compute_box1_bracket_breakdown(taxable_income: Decimal, brackets: list) -> list[dict]:
    """Return per-bracket tax application details for Box1."""
    breakdown = []
    for bracket in sorted(brackets, key=lambda b: b.lower_bound):
        taxable_in_bracket = bracket.taxable_amount(taxable_income)
        if taxable_in_bracket <= 0:
            continue
        tax_in_bracket = round_down_euro(taxable_in_bracket * bracket.rate)
        breakdown.append(
            {
                "description": bracket.description,
                "lower_bound": float(bracket.lower_bound),
                "upper_bound": float(bracket.upper_bound) if bracket.upper_bound is not None else None,
                "rate": float(bracket.rate),
                "taxable_amount": float(taxable_in_bracket),
                "tax_amount": float(tax_in_bracket),
            }
        )
    return breakdown


def compute_box3_allocation(
    member_ids: list[str],
    member_net_assets: dict[str, Decimal],
    strategy: str,
    total_box3_tax: Decimal,
    custom_percentages: dict[str, Decimal],
) -> dict[str, Decimal]:
    """Allocate Box3 tax over members based on selected strategy."""
    if not member_ids:
        return {}

    if strategy == "EQUAL":
        each = total_box3_tax / Decimal(len(member_ids))
        return {mid: each for mid in member_ids}

    if strategy == "CUSTOM" and custom_percentages:
        total_pct = sum(custom_percentages.values(), Decimal("0"))
        if total_pct > 0:
            return {
                mid: total_box3_tax * (custom_percentages.get(mid, Decimal("0")) / total_pct)
                for mid in member_ids
            }

    total_net_assets = sum(member_net_assets.values(), Decimal("0"))
    if total_net_assets <= 0:
        each = total_box3_tax / Decimal(len(member_ids))
        return {mid: each for mid in member_ids}

    return {
        mid: total_box3_tax * (member_net_assets[mid] / total_net_assets)
        for mid in member_ids
    }


def split_equal(member_ids: list[str], total: Decimal) -> dict[str, Decimal]:
    """Split a total over members while preserving the exact sum via last-member remainder."""
    if not member_ids:
        return {}
    if len(member_ids) == 1:
        return {member_ids[0]: total}

    each = round_down_euro(total / Decimal(len(member_ids)))
    allocation = {member_id: each for member_id in member_ids}
    allocated_total = each * Decimal(len(member_ids))
    allocation[member_ids[-1]] = total - (allocated_total - each)
    return allocation


def allocate_by_weights(
    member_ids: list[str],
    total: Decimal,
    weights: dict[str, Decimal],
) -> dict[str, Decimal]:
    """Allocate a total by member weights while preserving the exact sum via last-member remainder."""
    if not member_ids:
        return {}

    total_weight = sum((max(Decimal("0"), weights.get(member_id, Decimal("0"))) for member_id in member_ids), Decimal("0"))
    if total_weight <= 0:
        return split_equal(member_ids, total)

    allocation: dict[str, Decimal] = {}
    running = Decimal("0")
    for idx, member_id in enumerate(member_ids):
        if idx == len(member_ids) - 1:
            amount = total - running
        else:
            ratio = max(Decimal("0"), weights.get(member_id, Decimal("0"))) / total_weight
            amount = round_down_euro(total * ratio)
            running += amount
        allocation[member_id] = amount

    return allocation


def normalize_joint_distribution(
    member_ids: list[str],
    shared_totals: dict[str, Decimal],
    raw_distribution: dict,
    must_validate: bool,
) -> tuple[dict[str, dict[str, Decimal]], list[str]]:
    """Normalize and validate partner allocation for shared posts."""
    distribution: dict[str, dict[str, Decimal]] = {}
    errors: list[str] = []

    for item_key, total_amount in shared_totals.items():
        item_distribution_raw = raw_distribution.get(item_key, {}) if isinstance(raw_distribution, dict) else {}

        if (not isinstance(item_distribution_raw, dict)) and must_validate:
            errors.append(f"Verdeling voor '{item_key}' ontbreekt of heeft onjuist formaat.")
            continue

        item_distribution: dict[str, Decimal] = {}
        provided_sum = Decimal("0")
        for member_id in member_ids:
            amount = dec(item_distribution_raw.get(member_id, "0")) if isinstance(item_distribution_raw, dict) else Decimal("0")
            if amount < 0:
                errors.append(f"Verdeling voor '{item_key}' bevat negatieve waarde voor '{member_id}'.")
            item_distribution[member_id] = amount
            provided_sum += amount

        if must_validate:
            if abs(provided_sum - total_amount) > Decimal("0.01"):
                errors.append(
                    f"Verdeling voor '{item_key}' telt op tot {provided_sum} maar moet {total_amount} zijn."
                )
            distribution[item_key] = item_distribution
        else:
            distribution[item_key] = split_equal(member_ids, total_amount)

    return distribution, errors


def compute_green_investment_credit(green_exemption_share: Decimal, config) -> Decimal:
    """Compute taxpayer-favorable green investment tax credit per member."""
    green_credit_base_capped = min(green_exemption_share, config.green_investment_credit_base_cap_single)
    return round_up_euro(green_credit_base_capped * config.green_investment_tax_credit_rate)


def apply_small_payable_threshold(net_amount: Decimal) -> tuple[Decimal, bool]:
    """Apply small payable assessment rule: payable amounts up to threshold become zero."""
    if Decimal("0") <= net_amount <= SMALL_PAYABLE_ASSESSMENT_THRESHOLD:
        return Decimal("0"), True
    return net_amount, False


def settlement_result_type(net_settlement: Decimal) -> str:
    """Return settlement label used in responses."""
    if net_settlement == 0:
        return "NIETS_TE_BETALEN"
    return "TE_BETALEN" if net_settlement > 0 else "TERUGGAAF"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/income-types")
def get_income_types():
    return jsonify(
        {
            "types": [
                {"id": "EMPLOYMENT", "label": "Loon uit dienstverband"},
                {"id": "SELF_EMPLOYMENT", "label": "Winst uit onderneming"},
                {"id": "BENEFITS", "label": "Uitkeringen"},
                {"id": "PENSION", "label": "Pensioen"},
                {"id": "OTHER", "label": "Overig Box 1 inkomen"},
            ]
        }
    )


@app.route("/api/box1-deduction-types")
def get_box1_deduction_types():
    return jsonify(
        {
            "types": [
                {"id": "MORTGAGE_INTEREST", "label": "Hypotheekrente"},
                {"id": "ENTREPRENEUR_ALLOWANCE", "label": "Ondernemersaftrek"},
                {"id": "PERSONAL_ALLOWANCE", "label": "Persoonsgebonden aftrek"},
                {"id": "OTHER", "label": "Overige aftrek"},
            ]
        }
    )


@app.route("/api/allocation-strategies")
def get_allocation_strategies():
    return jsonify(
        {
            "strategies": [
                {"id": "EQUAL", "label": "Gelijk"},
                {"id": "PROPORTIONAL", "label": "Proportioneel op netto vermogen"},
                {"id": "CUSTOM", "label": "Custom verdeling (%)"},
            ]
        }
    )


@app.route("/api/joint-items-preview", methods=["POST"])
def preview_joint_items():
    """Return exact totals for the joint items that must be distributed between partners."""
    try:
        data = request.get_json() or {}
        config = get_latest_tax_config()

        members = data.get("members", [])
        if not members:
            return jsonify({"error": "Minimaal 1 persoon is verplicht."}), 400

        member_ids: list[str] = []
        member_labels: dict[str, str] = {}
        member_box3_inputs: list[dict] = []
        for idx, member in enumerate(members, start=1):
            member_id = member.get("member_id") or member.get("bsn") or f"member_{idx}"
            member_ids.append(member_id)
            member_labels[member_id] = member.get("full_name", f"Persoon {idx}")

            box3_data = member.get("box3", {})
            member_investment_accounts = box3_data.get("investment_accounts", [])
            accounts_investments_total = sum(
                (
                    round_down_euro(dec(account.get("amount", account.get("value"))))
                    for account in member_investment_accounts
                    if not bool(account.get("is_green", account.get("isGreen", False)))
                ),
                Decimal("0"),
            )
            accounts_green_investments_total = sum(
                (
                    round_down_euro(dec(account.get("amount", account.get("value"))))
                    for account in member_investment_accounts
                    if bool(account.get("is_green", account.get("isGreen", False)))
                ),
                Decimal("0"),
            )
            account_dividend_withholding_total = sum(
                (round_up_euro(dec(account.get("dividend_withholding"))) for account in member_investment_accounts),
                Decimal("0"),
            )
            account_foreign_dividend_withholding_total = sum(
                (round_up_euro(dec(account.get("foreign_dividend_withholding"))) for account in member_investment_accounts),
                Decimal("0"),
            )
            member_box3_inputs.append(
                {
                    "savings": round_down_euro(dec(box3_data.get("savings"))),
                    "investments": (
                        accounts_investments_total
                        if member_investment_accounts
                        else round_down_euro(dec(box3_data.get("investments")))
                    ),
                    "other_assets": round_down_euro(dec(box3_data.get("other_assets"))),
                    "debts": round_up_euro(dec(box3_data.get("debts"))),
                    "green_investments": accounts_green_investments_total,
                    "direct_dividend_withholding": (
                        account_dividend_withholding_total
                        if member_investment_accounts
                        else round_up_euro(
                            dec(member.get("dividend_withholding", member.get("box2", {}).get("withheld_dividend_tax", "0")))
                        )
                    ),
                    "direct_foreign_dividend_withholding": (
                        account_foreign_dividend_withholding_total
                        if member_investment_accounts
                        else round_up_euro(dec(member.get("foreign_dividend_withholding", "0")))
                    ),
                }
            )

        household_box1 = data.get("household_box1") or {}
        household_own_home = household_box1.get("own_home", data.get("own_home", {}))
        household_woz_value = round_down_euro(dec(household_own_home.get("woz_value", "0")))
        household_period_fraction = float(household_own_home.get("period_fraction", 1) or 1)
        household_has_own_home = bool(household_own_home.get("has_own_home", False)) and household_woz_value > 0
        household_eigenwoningforfait = (
            round_down_euro(dec(calculate_eigenwoningforfait(float(household_woz_value), household_period_fraction)))
            if household_has_own_home
            else Decimal("0")
        )
        # This deduction is taxpayer-favorable and should round up to whole euros.
        household_small_own_home_debt_deduction = round_up_euro(
            household_eigenwoningforfait * SMALL_OWN_HOME_DEBT_DEDUCTION_RATE
        )

        household_box3 = data.get("box3_household") or {}
        use_household_box3 = bool(household_box3)
        total_green_investments = Decimal("0")

        if use_household_box3:
            savings_accounts = household_box3.get("savings_accounts", [])
            investment_accounts = household_box3.get("investment_accounts", [])
            other_assets_items = household_box3.get("other_assets_items", [])
            debt_items = household_box3.get("debt_items", [])

            accounts_savings_total = sum(
                (
                    round_down_euro(dec(account.get("amount")))
                    for account in savings_accounts
                    if not bool(account.get("is_green", account.get("isGreen", False)))
                ),
                Decimal("0"),
            )
            accounts_investments_total = sum(
                (
                    round_down_euro(dec(account.get("amount", account.get("value"))))
                    for account in investment_accounts
                    if not bool(account.get("is_green", account.get("isGreen", False)))
                ),
                Decimal("0"),
            )
            accounts_green_investments_total = sum(
                (
                    round_down_euro(dec(account.get("amount", account.get("value"))))
                    for account in investment_accounts
                    if bool(account.get("is_green", account.get("isGreen", False)))
                ),
                Decimal("0"),
            )
            items_other_assets_total = sum(
                (round_down_euro(dec(item.get("amount"))) for item in other_assets_items),
                Decimal("0"),
            )
            items_debt_total = sum(
                (round_up_euro(abs(dec(item.get("amount")))) for item in debt_items),
                Decimal("0"),
            )

            total_savings = (
                accounts_savings_total
                if savings_accounts
                else round_down_euro(dec(household_box3.get("savings")))
            )
            total_investments = (
                accounts_investments_total
                if investment_accounts
                else round_down_euro(dec(household_box3.get("investments")))
            )
            total_other_assets = (
                items_other_assets_total
                if other_assets_items
                else round_down_euro(dec(household_box3.get("other_assets")))
            )
            total_debts = (
                items_debt_total
                if debt_items
                else round_up_euro(dec(household_box3.get("debts")))
            )
            total_green_investments = accounts_green_investments_total

            household_dividend_withholding_total = round_up_euro(dec(
                data.get(
                    "dividend_withholding_total",
                    household_box3.get("total_dividend_withholding", "0"),
                )
            ))
            household_foreign_dividend_withholding_total = round_up_euro(dec(
                data.get(
                    "foreign_dividend_withholding_total",
                    household_box3.get("total_foreign_dividend_withholding", "0"),
                )
            ))
            if not household_dividend_withholding_total and investment_accounts:
                household_dividend_withholding_total = sum(
                    (round_up_euro(dec(account.get("dividend_withholding"))) for account in investment_accounts),
                    Decimal("0"),
                )
            if not household_foreign_dividend_withholding_total and investment_accounts:
                household_foreign_dividend_withholding_total = sum(
                    (round_up_euro(dec(account.get("foreign_dividend_withholding"))) for account in investment_accounts),
                    Decimal("0"),
                )
        else:
            total_savings = sum((m["savings"] for m in member_box3_inputs), Decimal("0"))
            total_investments = sum((m["investments"] for m in member_box3_inputs), Decimal("0"))
            total_other_assets = sum((m["other_assets"] for m in member_box3_inputs), Decimal("0"))
            total_debts = sum((m["debts"] for m in member_box3_inputs), Decimal("0"))
            total_green_investments = sum((m["green_investments"] for m in member_box3_inputs), Decimal("0"))
            household_dividend_withholding_total = sum(
                (m["direct_dividend_withholding"] for m in member_box3_inputs),
                Decimal("0"),
            )
            household_foreign_dividend_withholding_total = sum(
                (m["direct_foreign_dividend_withholding"] for m in member_box3_inputs),
                Decimal("0"),
            )

        gross_assets = total_savings + total_investments + total_other_assets
        total_net_assets = max(Decimal("0"), gross_assets - total_debts)
        tax_free_assets = config.box3_tax_free_assets_single * Decimal(len(members))
        net_asset_factor = (total_net_assets / gross_assets) if gross_assets > 0 else Decimal("0")
        net_savings = total_savings * net_asset_factor
        net_non_savings = (total_investments + total_other_assets) * net_asset_factor
        deemed_return_savings = round_down_euro(net_savings * config.box3_savings_return_rate)
        deemed_return_non_savings = round_down_euro(net_non_savings * config.box3_investment_return_rate)
        deemed_return_total = deemed_return_savings + deemed_return_non_savings
        corrected_assets = max(Decimal("0"), total_net_assets - tax_free_assets)
        correction_factor = (corrected_assets / total_net_assets) if total_net_assets > 0 else Decimal("0")
        deemed_box3_income = round_down_euro(deemed_return_total * correction_factor)
        debt_negative_income_post = -total_debts
        box3_income = round_down_euro(deemed_box3_income + debt_negative_income_post)
        box3_taxable_income = max(Decimal("0"), box3_income)

        grondslag_sparen_beleggen = max(
            Decimal("0"),
            (total_savings + total_investments) - tax_free_assets,
        )

        shared_totals = {
            "eigenwoningforfait": household_eigenwoningforfait,
            "aftrek_geen_of_kleine_eigenwoningschuld": household_small_own_home_debt_deduction,
            "grondslag_voordeel_sparen_beleggen": grondslag_sparen_beleggen,
            "vrijstelling_groene_beleggingen": total_green_investments,
            "ingehouden_dividendbelasting": household_dividend_withholding_total,
            "ingehouden_buitenlandse_dividendbelasting": household_foreign_dividend_withholding_total,
        }

        return jsonify(
            {
                "success": True,
                "member_ids": member_ids,
                "member_labels": member_labels,
                "joint_distribution_totals": {k: float(v) for k, v in shared_totals.items()},
            }
        )
    except Exception as exc:
        return jsonify({"error": f"Preview error: {str(exc)}"}), 500


@app.route("/api/calculate", methods=["POST"])
def calculate_tax():
    try:
        data = request.get_json() or {}
        saved_file = save_input_data_to_json(data)
        config = get_latest_tax_config()

        members = data.get("members", [])
        if not members:
            return jsonify({"error": "Minimaal 1 persoon is verplicht."}), 400

        fiscal_partner = bool(data.get("fiscal_partner", len(members) > 1))
        allocation_strategy = data.get("allocation_strategy", "PROPORTIONAL")

        household_box1 = data.get("household_box1") or {}
        household_own_home = household_box1.get("own_home", data.get("own_home", {}))
        household_woz_value = round_down_euro(dec(household_own_home.get("woz_value", "0")))
        household_period_fraction = float(household_own_home.get("period_fraction", 1) or 1)
        household_has_own_home = bool(household_own_home.get("has_own_home", False)) and household_woz_value > 0
        household_eigenwoningforfait = (
            round_down_euro(dec(calculate_eigenwoningforfait(float(household_woz_value), household_period_fraction)))
            if household_has_own_home
            else Decimal("0")
        )
        # This deduction is taxpayer-favorable and should round up to whole euros.
        household_small_own_home_debt_deduction = round_up_euro(
            household_eigenwoningforfait * SMALL_OWN_HOME_DEBT_DEDUCTION_RATE
        )

        household_box3 = data.get("box3_household") or {}
        use_household_box3 = bool(household_box3)

        member_inputs: list[dict] = []
        member_ids: list[str] = []

        for idx, member in enumerate(members, start=1):
            member_id = member.get("member_id") or member.get("bsn") or f"member_{idx}"
            full_name = member.get("full_name", f"Persoon {idx}")
            member_ids.append(member_id)

            incomes = member.get("box1", {}).get("incomes", member.get("incomes", []))
            deductions = member.get("box1", {}).get("deductions", member.get("deductions", []))
            has_aow = bool(member.get("box1", {}).get("has_aow", member.get("has_aow", False)))
            tax_credits = member.get("box1", {}).get("tax_credits", member.get("tax_credits", []))

            box2_data = member.get("box2", {})
            has_substantial_interest = bool(box2_data.get("has_substantial_interest", False))
            box3_data = member.get("box3", {})
            member_investment_accounts = box3_data.get("investment_accounts", [])
            accounts_investments_total = sum(
                (
                    round_down_euro(dec(account.get("amount", account.get("value"))))
                    for account in member_investment_accounts
                    if not bool(account.get("is_green", account.get("isGreen", False)))
                ),
                Decimal("0"),
            )
            accounts_green_investments_total = sum(
                (
                    round_down_euro(dec(account.get("amount", account.get("value"))))
                    for account in member_investment_accounts
                    if bool(account.get("is_green", account.get("isGreen", False)))
                ),
                Decimal("0"),
            )
            account_dividend_withholding_total = sum(
                (round_up_euro(dec(account.get("dividend_withholding"))) for account in member_investment_accounts),
                Decimal("0"),
            )
            account_foreign_dividend_withholding_total = sum(
                (round_up_euro(dec(account.get("foreign_dividend_withholding"))) for account in member_investment_accounts),
                Decimal("0"),
            )

            member_inputs.append(
                {
                    "member_id": member_id,
                    "full_name": full_name,
                    "incomes": incomes,
                    "deductions": deductions,
                    "has_aow": has_aow,
                    "tax_credits": tax_credits,
                    "wage_withholding": round_up_euro(dec(member.get("wage_withholding", member.get("withheld_tax", "0")))),
                    "other_prepaid_taxes": round_up_euro(dec(member.get("other_prepaid_taxes", "0"))),
                    "box2": {
                        "has_substantial_interest": has_substantial_interest,
                        "dividend_income": round_down_euro(dec(box2_data.get("dividend_income"))),
                        "sale_gain": round_down_euro(dec(box2_data.get("sale_gain"))),
                        "acquisition_price": round_up_euro(dec(box2_data.get("acquisition_price"))),
                    },
                    "box3_input": {
                        "savings": round_down_euro(dec(box3_data.get("savings"))),
                        "investments": (
                            accounts_investments_total
                            if member_investment_accounts
                            else round_down_euro(dec(box3_data.get("investments")))
                        ),
                        "other_assets": round_down_euro(dec(box3_data.get("other_assets"))),
                        "debts": round_up_euro(dec(box3_data.get("debts"))),
                        "green_investments": accounts_green_investments_total,
                        "direct_dividend_withholding": (
                            account_dividend_withholding_total
                            if member_investment_accounts
                            else round_up_euro(
                                dec(member.get("dividend_withholding", box2_data.get("withheld_dividend_tax", "0")))
                            )
                        ),
                        "direct_foreign_dividend_withholding": (
                            account_foreign_dividend_withholding_total
                            if member_investment_accounts
                            else round_up_euro(dec(member.get("foreign_dividend_withholding", "0")))
                        ),
                    },
                }
            )

        total_green_investments = Decimal("0")

        if use_household_box3:
            savings_accounts = household_box3.get("savings_accounts", [])
            investment_accounts = household_box3.get("investment_accounts", [])
            other_assets_items = household_box3.get("other_assets_items", [])
            debt_items = household_box3.get("debt_items", [])

            accounts_savings_total = sum(
                (
                    round_down_euro(dec(account.get("amount")))
                    for account in savings_accounts
                    if not bool(account.get("is_green", account.get("isGreen", False)))
                ),
                Decimal("0"),
            )
            accounts_investments_total = sum(
                (
                    round_down_euro(dec(account.get("amount", account.get("value"))))
                    for account in investment_accounts
                    if not bool(account.get("is_green", account.get("isGreen", False)))
                ),
                Decimal("0"),
            )
            accounts_green_investments_total = sum(
                (
                    round_down_euro(dec(account.get("amount", account.get("value"))))
                    for account in investment_accounts
                    if bool(account.get("is_green", account.get("isGreen", False)))
                ),
                Decimal("0"),
            )
            items_other_assets_total = sum(
                (round_down_euro(dec(item.get("amount"))) for item in other_assets_items),
                Decimal("0"),
            )
            items_debt_total = sum(
                (round_up_euro(abs(dec(item.get("amount")))) for item in debt_items),
                Decimal("0"),
            )

            total_savings = (
                accounts_savings_total
                if savings_accounts
                else round_down_euro(dec(household_box3.get("savings")))
            )
            total_investments = (
                accounts_investments_total
                if investment_accounts
                else round_down_euro(dec(household_box3.get("investments")))
            )
            total_other_assets = (
                items_other_assets_total
                if other_assets_items
                else round_down_euro(dec(household_box3.get("other_assets")))
            )
            total_debts = (
                items_debt_total
                if debt_items
                else round_up_euro(dec(household_box3.get("debts")))
            )
            total_green_investments = accounts_green_investments_total

            household_dividend_withholding_total = round_up_euro(dec(
                data.get(
                    "dividend_withholding_total",
                    household_box3.get("total_dividend_withholding", "0"),
                )
            ))
            household_foreign_dividend_withholding_total = round_up_euro(dec(
                data.get(
                    "foreign_dividend_withholding_total",
                    household_box3.get("total_foreign_dividend_withholding", "0"),
                )
            ))
            if not household_dividend_withholding_total and investment_accounts:
                household_dividend_withholding_total = sum(
                    (round_up_euro(dec(account.get("dividend_withholding"))) for account in investment_accounts),
                    Decimal("0"),
                )
            if not household_foreign_dividend_withholding_total and investment_accounts:
                household_foreign_dividend_withholding_total = sum(
                    (round_up_euro(dec(account.get("foreign_dividend_withholding"))) for account in investment_accounts),
                    Decimal("0"),
                )
        else:
            total_savings = sum((m["box3_input"]["savings"] for m in member_inputs), Decimal("0"))
            total_investments = sum((m["box3_input"]["investments"] for m in member_inputs), Decimal("0"))
            total_other_assets = sum((m["box3_input"]["other_assets"] for m in member_inputs), Decimal("0"))
            total_debts = sum((m["box3_input"]["debts"] for m in member_inputs), Decimal("0"))
            total_green_investments = sum((m["box3_input"]["green_investments"] for m in member_inputs), Decimal("0"))
            household_dividend_withholding_total = sum(
                (m["box3_input"]["direct_dividend_withholding"] for m in member_inputs),
                Decimal("0"),
            )
            household_foreign_dividend_withholding_total = sum(
                (m["box3_input"]["direct_foreign_dividend_withholding"] for m in member_inputs),
                Decimal("0"),
            )

        gross_assets = total_savings + total_investments + total_other_assets
        total_net_assets = max(Decimal("0"), gross_assets - total_debts)

        # Afstemmen op aantal personen: heffingsvrij vermogen schaalt met huishoudgrootte.
        tax_free_assets = config.box3_tax_free_assets_single * Decimal(len(members))

        net_asset_factor = (total_net_assets / gross_assets) if gross_assets > 0 else Decimal("0")
        net_savings = total_savings * net_asset_factor
        net_non_savings = (total_investments + total_other_assets) * net_asset_factor

        deemed_return_savings = round_down_euro(net_savings * config.box3_savings_return_rate)
        deemed_return_non_savings = round_down_euro(net_non_savings * config.box3_investment_return_rate)
        deemed_return_total = deemed_return_savings + deemed_return_non_savings

        corrected_assets = max(Decimal("0"), total_net_assets - tax_free_assets)
        correction_factor = (corrected_assets / total_net_assets) if total_net_assets > 0 else Decimal("0")
        deemed_box3_income = round_down_euro(deemed_return_total * correction_factor)
        debt_negative_income_post = -total_debts
        box3_income = round_down_euro(deemed_box3_income + debt_negative_income_post)
        box3_taxable_income = max(Decimal("0"), box3_income)

        grondslag_sparen_beleggen = max(
            Decimal("0"),
            (total_savings + total_investments) - tax_free_assets,
        )

        shared_totals = {
            "eigenwoningforfait": household_eigenwoningforfait,
            "aftrek_geen_of_kleine_eigenwoningschuld": household_small_own_home_debt_deduction,
            "grondslag_voordeel_sparen_beleggen": grondslag_sparen_beleggen,
            "vrijstelling_groene_beleggingen": total_green_investments,
            "ingehouden_dividendbelasting": household_dividend_withholding_total,
            "ingehouden_buitenlandse_dividendbelasting": household_foreign_dividend_withholding_total,
        }
        joint_distribution_raw = data.get("joint_distribution", {})
        requires_distribution = fiscal_partner and len(member_ids) >= 2
        joint_distribution, distribution_errors = normalize_joint_distribution(
            member_ids,
            shared_totals,
            joint_distribution_raw,
            requires_distribution,
        )
        if distribution_errors:
            return jsonify({"error": " ".join(distribution_errors)}), 400

        taxable_grondslag_by_member: dict[str, Decimal] = {}
        taxable_grondslag_total = Decimal("0")
        for member_id in member_ids:
            grondslag_share = joint_distribution["grondslag_voordeel_sparen_beleggen"].get(member_id, Decimal("0"))
            # Groene beleggingen zijn eerder in de grondslag verwerkt en worden hier niet nogmaals afgetrokken.
            taxable_grondslag_share = max(Decimal("0"), grondslag_share)
            taxable_grondslag_by_member[member_id] = taxable_grondslag_share
            taxable_grondslag_total += taxable_grondslag_share

        box3_taxable_income_allocated: dict[str, Decimal] = {}
        gross_rendementsberekening = total_savings + total_investments
        if box3_taxable_income <= 0:
            box3_taxable_income_allocated = {member_id: Decimal("0") for member_id in member_ids}
        elif len(member_ids) <= 1:
            # Enkele belastingplichtige: het volledige belastbare inkomen wordt toegewezen.
            box3_taxable_income_allocated = {member_ids[0]: box3_taxable_income} if member_ids else {}
        elif taxable_grondslag_total <= 0 or gross_rendementsberekening <= 0:
            box3_taxable_income_allocated = split_equal(member_ids, box3_taxable_income)
        else:
            # Per belastingplichtige: aandeel = afgerond-naar-beneden(grondslag_partner /
            # grondslag_rendementsberekening, 4 decimalen) × fictief_rendement_totaal.
            # Dit volgt de berekeningsmethode van de Belastingdienst waarbij het percentage
            # op 2 decimalen (4 decimalen als breuk) naar beneden wordt afgerond.
            for member_id in member_ids:
                partner_grondslag = taxable_grondslag_by_member.get(member_id, Decimal("0"))
                ratio = (partner_grondslag / gross_rendementsberekening).quantize(
                    Decimal("0.0001"), rounding=ROUND_FLOOR
                )
                allocated_income = round_down_euro(ratio * deemed_return_total)
                box3_taxable_income_allocated[member_id] = allocated_income

        total_partner_wealth = sum(
            (joint_distribution["grondslag_voordeel_sparen_beleggen"].get(member_id, Decimal("0")) for member_id in member_ids),
            Decimal("0"),
        )
        partner_wealth_weights = {
            member_id: joint_distribution["grondslag_voordeel_sparen_beleggen"].get(member_id, Decimal("0"))
            for member_id in member_ids
        }
        if total_partner_wealth <= 0:
            partner_share_pct = {
                member_id: (Decimal("100") / Decimal(len(member_ids)) if member_ids else Decimal("0"))
                for member_id in member_ids
            }
        else:
            partner_share_pct = {
                member_id: (partner_wealth_weights[member_id] / total_partner_wealth) * Decimal("100")
                for member_id in member_ids
            }

        grondslag_rendementsberekening_total = total_savings + total_investments
        grondslag_rendementsberekening_partner = allocate_by_weights(
            member_ids,
            grondslag_rendementsberekening_total,
            partner_wealth_weights,
        )
        grondslag_sparen_beleggen_partner = allocate_by_weights(
            member_ids,
            grondslag_sparen_beleggen,
            partner_wealth_weights,
        )
        fictief_rendement_partner = allocate_by_weights(
            member_ids,
            deemed_return_total,
            partner_wealth_weights,
        )

        member_results: list[dict] = []
        box1_total = Decimal("0")
        box2_total = Decimal("0")
        box3_total = Decimal("0")
        total_tax_credits = Decimal("0")
        total_prepaid_taxes = Decimal("0")
        box1_brackets_applied_totals: dict[str, dict] = {}
        premium_aow_total = Decimal("0")
        premium_anw_total = Decimal("0")
        premium_wlz_total = Decimal("0")
        premium_basis_total = Decimal("0")
        box1_taxable_income_total = Decimal("0")
        box2_taxable_income_total = Decimal("0")
        box3_taxable_income_total = Decimal("0")
        total_gross_income = Decimal("0")
        total_member_net_settlement = Decimal("0")

        for member in member_inputs:
            member_id = member["member_id"]

            gross_income = Decimal("0")
            total_arbeidskorting = Decimal("0")
            for item in member["incomes"]:
                line_income = round_down_euro(dec(item.get("amount", item.get("gross_amount"))))
                labor_credit = round_up_euro(dec(item.get("labor_credit", item.get("arbeidskorting", "0"))))
                gross_income += line_income
                total_arbeidskorting += labor_credit
            total_gross_income += gross_income

            total_deductions = sum((round_up_euro(dec(item.get("amount"))) for item in member["deductions"]), Decimal("0"))
            eigenwoningforfait_share = joint_distribution["eigenwoningforfait"].get(member_id, Decimal("0"))
            small_own_home_debt_deduction_share = joint_distribution[
                "aftrek_geen_of_kleine_eigenwoningschuld"
            ].get(member_id, Decimal("0"))
            box1_taxable_income = round_down_euro(
                max(
                    Decimal("0"),
                    gross_income
                    + eigenwoningforfait_share
                    - small_own_home_debt_deduction_share
                    - total_deductions,
                )
            )
            box1_taxable_income_total += box1_taxable_income

            box1_brackets = compute_box1_bracket_breakdown(box1_taxable_income, config.box1_brackets)
            box1_tax = round_down_euro(sum((dec(row["tax_amount"]) for row in box1_brackets), Decimal("0")))
            box1_total += box1_tax

            premium_basis_member = min(box1_taxable_income, config.premium_income_cap)
            premium_basis_total += premium_basis_member
            premium_aow_member = Decimal("0") if member["has_aow"] else premium_basis_member * config.premium_aow_rate
            premium_anw_member = premium_basis_member * config.premium_anw_rate
            premium_wlz_member = premium_basis_member * config.premium_wlz_rate
            premium_member_total = round_down_euro(premium_aow_member + premium_anw_member + premium_wlz_member)
            premium_aow_total += premium_aow_member
            premium_anw_total += premium_anw_member
            premium_wlz_total += premium_wlz_member

            for row in box1_brackets:
                desc = row["description"]
                if desc not in box1_brackets_applied_totals:
                    box1_brackets_applied_totals[desc] = {
                        "description": desc,
                        "rate": row["rate"],
                        "taxable_amount": Decimal("0"),
                        "tax_amount": Decimal("0"),
                    }
                box1_brackets_applied_totals[desc]["taxable_amount"] += dec(row["taxable_amount"])
                box1_brackets_applied_totals[desc]["tax_amount"] += dec(row["tax_amount"])

            manual_credit_items = [
                {
                    "name": c.get("name", "Heffingskorting"),
                    "amount": round_up_euro(dec(c.get("amount"))),
                }
                for c in member["tax_credits"]
            ]
            total_member_credits = sum((item["amount"] for item in manual_credit_items), Decimal("0"))

            green_exemption_share = joint_distribution["vrijstelling_groene_beleggingen"].get(member_id, Decimal("0"))
            green_investment_credit = compute_green_investment_credit(green_exemption_share, config)
            if green_investment_credit > 0:
                manual_credit_items.append(
                    {
                        "name": "Heffingskorting groene beleggingen",
                        "amount": green_investment_credit,
                    }
                )
            total_member_credits += green_investment_credit
            total_tax_credits += total_member_credits

            box2_data = member["box2"]
            box2_taxable_income = (
                max(Decimal("0"), box2_data["dividend_income"] + box2_data["sale_gain"] - box2_data["acquisition_price"])
                if box2_data["has_substantial_interest"]
                else Decimal("0")
            )
            box2_taxable_income = round_down_euro(box2_taxable_income)
            box2_taxable_income_total += box2_taxable_income
            box2_tax = round_down_euro(box2_taxable_income * BOX2_RATE_2025)
            box2_total += box2_tax

            grondslag_share = joint_distribution["grondslag_voordeel_sparen_beleggen"].get(member_id, Decimal("0"))
            box3_taxable_member = box3_taxable_income_allocated.get(member_id, Decimal("0"))
            box3_taxable_income_total += box3_taxable_member
            box3_tax_before_foreign_dividend = round_down_euro(box3_taxable_member * config.box3_rate)
            foreign_dividend_withholding = joint_distribution["ingehouden_buitenlandse_dividendbelasting"].get(
                member_id,
                Decimal("0"),
            )
            foreign_dividend_offset = min(box3_tax_before_foreign_dividend, round_up_euro(foreign_dividend_withholding))
            box3_tax_member = max(Decimal("0"), box3_tax_before_foreign_dividend - foreign_dividend_offset)
            box3_total += box3_tax_member

            dividend_withholding = joint_distribution["ingehouden_dividendbelasting"].get(member_id, Decimal("0"))
            wage_withholding = member["wage_withholding"]
            other_prepaid = member["other_prepaid_taxes"]
            prepaid_taxes = wage_withholding + dividend_withholding + other_prepaid
            total_prepaid_taxes += prepaid_taxes

            gross_member_tax = round_down_euro(box1_tax + box2_tax + box3_tax_member + premium_member_total)
            net_member_settlement_before_threshold = round_down_euro(
                gross_member_tax - total_member_credits - prepaid_taxes
            )
            net_member_settlement, threshold_applied = apply_small_payable_threshold(
                net_member_settlement_before_threshold
            )
            total_member_net_settlement += net_member_settlement

            member_results.append(
                {
                    "member_id": member_id,
                    "full_name": member["full_name"],
                    "box1": {
                        "gross_income": float(gross_income),
                        "labor_credit_total": float(total_arbeidskorting),
                        "has_aow": member["has_aow"],
                        "eigenwoningforfait": float(eigenwoningforfait_share),
                        "aftrek_geen_of_kleine_eigenwoningschuld": float(small_own_home_debt_deduction_share),
                        "deductions": float(total_deductions),
                        "taxable_income": float(box1_taxable_income),
                        "tax": float(box1_tax),
                        "brackets": box1_brackets,
                        "credits": {
                            "items": [
                                {
                                    "name": c["name"],
                                    "amount": float(c["amount"]),
                                }
                                for c in manual_credit_items
                            ],
                            "total": float(total_member_credits),
                        },
                    },
                    "box2": {
                        "has_substantial_interest": box2_data["has_substantial_interest"],
                        "taxable_income": float(box2_taxable_income),
                        "tax_rate": float(BOX2_RATE_2025 * 100),
                        "tax": float(box2_tax),
                    },
                    "box3": {
                        "grondslag_rendementsberekening": float(
                            grondslag_rendementsberekening_partner.get(member_id, Decimal("0"))
                        ),
                        "grondslag_sparen_beleggen": float(
                            grondslag_sparen_beleggen_partner.get(member_id, Decimal("0"))
                        ),
                        "fictief_rendement_totaal": float(deemed_return_total),
                        "partner_share_percentage": float(partner_share_pct.get(member_id, Decimal("0"))),
                        "fictief_rendement_partner": float(
                            fictief_rendement_partner.get(member_id, Decimal("0"))
                        ),
                        "grondslag_voordeel_sparen_beleggen": float(grondslag_share),
                        "vrijstelling_groene_beleggingen": float(green_exemption_share),
                        "taxable_income": float(box3_taxable_member),
                        "tax_before_foreign_dividend": float(box3_tax_before_foreign_dividend),
                        "foreign_dividend_withholding": float(foreign_dividend_withholding),
                        "foreign_dividend_tax_credit_applied": float(foreign_dividend_offset),
                        "tax": float(box3_tax_member),
                    },
                    "prepayments": {
                        "wage_withholding": float(wage_withholding),
                        "dividend_withholding": float(dividend_withholding),
                        "other_prepaid_taxes": float(other_prepaid),
                        "total": float(prepaid_taxes),
                    },
                    "premiums": {
                        "aow": float(premium_aow_member),
                        "anw": float(premium_anw_member),
                        "wlz": float(premium_wlz_member),
                        "total": float(premium_member_total),
                    },
                    "settlement": {
                        "gross_income_tax": float(gross_member_tax),
                        "tax_credits": float(total_member_credits),
                        "prepaid_taxes": float(prepaid_taxes),
                        "net_settlement_before_assessment_threshold": float(net_member_settlement_before_threshold),
                        "assessment_threshold_applied": threshold_applied,
                        "net_settlement": float(net_member_settlement),
                        "result_type": settlement_result_type(net_member_settlement),
                    },
                    "joint_allocation": {
                        "eigenwoningforfait": float(eigenwoningforfait_share),
                        "aftrek_geen_of_kleine_eigenwoningschuld": float(small_own_home_debt_deduction_share),
                        "grondslag_voordeel_sparen_beleggen": float(grondslag_share),
                        "vrijstelling_groene_beleggingen": float(green_exemption_share),
                        "ingehouden_dividendbelasting": float(dividend_withholding),
                        "ingehouden_buitenlandse_dividendbelasting": float(foreign_dividend_withholding),
                    },
                }
            )

        verzamelinkomen = box1_taxable_income_total + box2_taxable_income_total + box3_taxable_income_total

        premium_basis = premium_basis_total
        premium_aow = premium_aow_total
        premium_anw = premium_anw_total
        premium_wlz = premium_wlz_total
        unrounded_premiums_sum = premium_aow + premium_anw + premium_wlz
        total_premiums = round_down_euro(unrounded_premiums_sum)

        box1_box3_tax = box1_total + box3_total
        gross_income_tax = round_down_euro(box1_box3_tax + total_premiums + box2_total)
        net_settlement_before_assessment_threshold = round_down_euro(
            gross_income_tax - total_tax_credits - total_prepaid_taxes
        )
        net_settlement = round_down_euro(total_member_net_settlement)
        effective_rate = (
            float((gross_income_tax / total_gross_income) * Decimal("100"))
            if total_gross_income > 0
            else 0.0
        )

        return jsonify(
            {
                "success": True,
                "tax_year": config.year,
                "input_saved_to": saved_file,
                "fiscal_partner": fiscal_partner,
                "allocation_strategy": allocation_strategy,
                "members": member_results,
                "joint_distribution": {
                    item: {member_id: float(amount) for member_id, amount in values.items()}
                    for item, values in joint_distribution.items()
                },
                "joint_distribution_totals": {k: float(v) for k, v in shared_totals.items()},
                "box1": {
                    "total_taxable_income": float(box1_taxable_income_total),
                    "total_tax": float(box1_total),
                    "brackets_applied": [
                        {
                            "description": row["description"],
                            "rate": row["rate"],
                            "taxable_amount": float(row["taxable_amount"]),
                            "tax_amount": float(row["tax_amount"]),
                        }
                        for row in sorted(
                            box1_brackets_applied_totals.values(), key=lambda x: x["rate"]
                        )
                    ],
                },
                "box2": {
                    "total_taxable_income": float(box2_taxable_income_total),
                    "tax_rate": float(BOX2_RATE_2025 * 100),
                    "total_tax": float(box2_total),
                },
                "box3": {
                    "tax_rate": float(config.box3_rate * 100),
                    "tax_free_assets": float(tax_free_assets),
                    "savings_return_rate": float(config.box3_savings_return_rate * 100),
                    "investment_return_rate": float(config.box3_investment_return_rate * 100),
                    "total_savings": float(total_savings),
                    "total_investments": float(total_investments),
                    "total_other_assets": float(total_other_assets),
                    "total_debts": float(total_debts),
                    "total_net_assets": float(total_net_assets),
                    "deemed_return_savings": float(deemed_return_savings),
                    "deemed_return_non_savings": float(deemed_return_non_savings),
                    "deemed_return_total": float(deemed_return_total),
                    "correction_factor": float(correction_factor),
                    "deemed_income_before_debts": float(deemed_box3_income),
                    "debt_negative_income_post": float(debt_negative_income_post),
                    "corrected_deemed_return": float(box3_income),
                    "taxable_income": float(box3_taxable_income),
                    "total_tax": float(box3_total),
                    "allocation": {
                        member_id: float(
                            joint_distribution["grondslag_voordeel_sparen_beleggen"].get(member_id, Decimal("0"))
                        )
                        for member_id in member_ids
                    },
                    "green_investments_total": float(total_green_investments),
                    "green_exemption_total": float(shared_totals["vrijstelling_groene_beleggingen"]),
                    "foreign_dividend_withholding_total": float(household_foreign_dividend_withholding_total),
                },
                "settlement": {
                    "box1_box3_tax": float(box1_box3_tax),
                    "box2_tax": float(box2_total),
                    "premiums": {
                            "basis": float(premium_basis),
                            "aow": float(premium_aow),
                            "anw": float(premium_anw),
                            "wlz": float(premium_wlz),
                            "total": int(total_premiums),
                    },
                    "gross_income_tax": float(gross_income_tax),
                    "total_tax_credits": float(total_tax_credits),
                    "total_prepaid_taxes": float(total_prepaid_taxes),
                    "net_settlement_before_assessment_threshold": float(net_settlement_before_assessment_threshold),
                    "net_settlement": float(net_settlement),
                    "result_type": settlement_result_type(net_settlement),
                    "effective_rate": round(effective_rate, 2),
                },
                "verzamelinkomen": float(verzamelinkomen),
            }
        )
    except Exception as exc:
        return jsonify({"error": f"Calculation error: {str(exc)}"}), 500


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Page not found"}), 404


@app.errorhandler(500)
def server_error(_error):
    return jsonify({"error": "Server error"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=8000)
