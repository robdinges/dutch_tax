"""Dutch Tax Calculator web application (procesflow versie)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import re

from flask import Flask, jsonify, render_template, request

from object_model import calculate_eigenwoningforfait
from tax_brackets import get_latest_tax_config

app = Flask(__name__)
app.config["SECRET_KEY"] = "dutch-tax-calculator-secret"


BOX2_RATE_2025 = Decimal("0.269")
PREMIUM_BASE_CAP = Decimal("19832")
PREMIUM_AOW_RATE = Decimal("0.0000")
PREMIUM_ANW_RATE = Decimal("0.0010")
PREMIUM_WLZ_RATE = Decimal("0.0965")


def dec(value: object, default: str = "0") -> Decimal:
    """Convert value to Decimal safely."""
    if value in (None, ""):
        return Decimal(default)
    return Decimal(str(value))


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
        tax_in_bracket = taxable_in_bracket * bracket.rate
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
        custom_allocation = data.get("custom_allocation", {})

        household_box3 = data.get("box3_household") or {}
        use_household_box3 = bool(household_box3)

        member_results: list[dict] = []
        box1_total = Decimal("0")
        box2_total = Decimal("0")
        total_tax_credits = Decimal("0")
        total_prepaid_taxes = Decimal("0")
        box1_brackets_applied_totals: dict[str, dict] = {}

        member_net_assets: dict[str, Decimal] = {}
        member_savings: dict[str, Decimal] = {}
        member_investments: dict[str, Decimal] = {}
        member_other_assets: dict[str, Decimal] = {}
        member_debts: dict[str, Decimal] = {}

        for idx, member in enumerate(members, start=1):
            member_id = member.get("member_id") or member.get("bsn") or f"member_{idx}"
            full_name = member.get("full_name", f"Persoon {idx}")

            incomes = member.get("box1", {}).get("incomes", member.get("incomes", []))
            deductions = member.get("box1", {}).get("deductions", member.get("deductions", []))
            own_home = member.get("box1", {}).get("own_home", member.get("own_home", {}))
            tax_credits = member.get("box1", {}).get("tax_credits", member.get("tax_credits", []))

            gross_income = sum((dec(item.get("amount")) for item in incomes), Decimal("0"))
            total_deductions = sum((dec(item.get("amount")) for item in deductions), Decimal("0"))

            woz_value = dec(own_home.get("woz_value", "0"))
            period_fraction = float(own_home.get("period_fraction", 1) or 1)
            has_own_home = bool(own_home.get("has_own_home", False)) and woz_value > 0
            eigenwoningforfait = (
                dec(calculate_eigenwoningforfait(float(woz_value), period_fraction))
                if has_own_home
                else Decimal("0")
            )

            box1_taxable_income = max(Decimal("0"), gross_income + eigenwoningforfait - total_deductions)
            box1_brackets = compute_box1_bracket_breakdown(box1_taxable_income, config.box1_brackets)
            box1_tax = sum((dec(row["tax_amount"]) for row in box1_brackets), Decimal("0"))
            box1_total += box1_tax

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

            total_member_credits = sum((dec(c.get("amount")) for c in tax_credits), Decimal("0"))
            total_tax_credits += total_member_credits

            box2_data = member.get("box2", {})
            has_substantial_interest = bool(box2_data.get("has_substantial_interest", False))
            dividend_income = dec(box2_data.get("dividend_income"))
            sale_gain = dec(box2_data.get("sale_gain"))
            acquisition_price = dec(box2_data.get("acquisition_price"))
            box2_taxable_income = (
                max(Decimal("0"), dividend_income + sale_gain - acquisition_price)
                if has_substantial_interest
                else Decimal("0")
            )
            box2_tax = box2_taxable_income * BOX2_RATE_2025
            box2_total += box2_tax

            if use_household_box3:
                savings = Decimal("0")
                investments = Decimal("0")
                other_assets = Decimal("0")
                debts = Decimal("0")
                net_assets = Decimal("0")
                investment_accounts = []
                member_net_assets[member_id] = Decimal("0")
                member_savings[member_id] = Decimal("0")
                member_investments[member_id] = Decimal("0")
                member_other_assets[member_id] = Decimal("0")
                member_debts[member_id] = Decimal("0")
            else:
                box3_data = member.get("box3", {})
                savings = dec(box3_data.get("savings"))
                investment_accounts = box3_data.get("investment_accounts", [])
                accounts_investments_total = sum(
                    (dec(account.get("value")) for account in investment_accounts),
                    Decimal("0"),
                )
                investments = (
                    accounts_investments_total
                    if investment_accounts
                    else dec(box3_data.get("investments"))
                )
                other_assets = dec(box3_data.get("other_assets"))
                debts = dec(box3_data.get("debts"))

                gross_assets = savings + investments + other_assets
                net_assets = max(Decimal("0"), gross_assets - debts)
                member_net_assets[member_id] = net_assets
                member_savings[member_id] = savings
                member_investments[member_id] = investments
                member_other_assets[member_id] = other_assets
                member_debts[member_id] = debts

            wage_withholding = dec(member.get("wage_withholding", member.get("withheld_tax", "0")))
            account_dividend_withholding_total = sum(
                (dec(account.get("dividend_withholding")) for account in investment_accounts),
                Decimal("0"),
            )
            dividend_withholding = (
                Decimal("0")
                if use_household_box3
                else (
                    account_dividend_withholding_total
                    if investment_accounts
                    else dec(member.get("dividend_withholding", box2_data.get("withheld_dividend_tax", "0")))
                )
            )
            other_prepaid = dec(member.get("other_prepaid_taxes", "0"))
            prepaid_taxes = wage_withholding + dividend_withholding + other_prepaid
            total_prepaid_taxes += prepaid_taxes

            member_results.append(
                {
                    "member_id": member_id,
                    "full_name": full_name,
                    "box1": {
                        "gross_income": float(gross_income),
                        "eigenwoningforfait": float(eigenwoningforfait),
                        "deductions": float(total_deductions),
                        "taxable_income": float(box1_taxable_income),
                        "tax": float(box1_tax),
                        "brackets": box1_brackets,
                        "credits": {
                            "items": [
                                {
                                    "name": c.get("name", "Heffingskorting"),
                                    "amount": float(dec(c.get("amount"))),
                                }
                                for c in tax_credits
                            ],
                            "total": float(total_member_credits),
                        },
                    },
                    "box2": {
                        "has_substantial_interest": has_substantial_interest,
                        "taxable_income": float(box2_taxable_income),
                        "tax_rate": float(BOX2_RATE_2025 * 100),
                        "tax": float(box2_tax),
                    },
                    "box3": {
                        "savings": float(savings),
                        "investments": float(investments),
                        "other_assets": float(other_assets),
                        "debts": float(debts),
                        "net_assets": float(net_assets),
                    },
                    "prepayments": {
                        "wage_withholding": float(wage_withholding),
                        "dividend_withholding": float(dividend_withholding),
                        "other_prepaid_taxes": float(other_prepaid),
                        "total": float(prepaid_taxes),
                    },
                }
            )

        member_ids = [m["member_id"] for m in member_results]

        if use_household_box3:
            savings_accounts = household_box3.get("savings_accounts", [])
            investment_accounts = household_box3.get("investment_accounts", [])
            other_assets_items = household_box3.get("other_assets_items", [])
            debt_items = household_box3.get("debt_items", [])

            accounts_savings_total = sum(
                (dec(account.get("amount")) for account in savings_accounts),
                Decimal("0"),
            )
            accounts_investments_total = sum(
                (dec(account.get("amount", account.get("value"))) for account in investment_accounts),
                Decimal("0"),
            )
            items_other_assets_total = sum(
                (dec(item.get("amount")) for item in other_assets_items),
                Decimal("0"),
            )
            items_debt_total = sum(
                (dec(item.get("amount")) for item in debt_items),
                Decimal("0"),
            )

            total_savings = (
                accounts_savings_total
                if savings_accounts
                else dec(household_box3.get("savings"))
            )
            total_investments = (
                accounts_investments_total
                if investment_accounts
                else dec(household_box3.get("investments"))
            )
            total_other_assets = (
                items_other_assets_total
                if other_assets_items
                else dec(household_box3.get("other_assets"))
            )
            total_debts = (
                items_debt_total
                if debt_items
                else dec(household_box3.get("debts"))
            )

            household_dividend_withholding_total = dec(
                data.get(
                    "dividend_withholding_total",
                    household_box3.get("total_dividend_withholding", "0"),
                )
            )
            if not household_dividend_withholding_total and investment_accounts:
                household_dividend_withholding_total = sum(
                    (dec(account.get("dividend_withholding")) for account in investment_accounts),
                    Decimal("0"),
                )
            total_prepaid_taxes += household_dividend_withholding_total
        else:
            total_savings = sum(member_savings.values(), Decimal("0"))
            total_investments = sum(member_investments.values(), Decimal("0"))
            total_other_assets = sum(member_other_assets.values(), Decimal("0"))
            total_debts = sum(member_debts.values(), Decimal("0"))

        gross_assets = total_savings + total_investments + total_other_assets
        total_net_assets = max(Decimal("0"), gross_assets - total_debts)

        if use_household_box3 and member_ids:
            equal_share = total_net_assets / Decimal(len(member_ids)) if member_ids else Decimal("0")
            member_net_assets = {member_id: equal_share for member_id in member_ids}

        # Afstemmen op aantal personen: heffingsvrij vermogen schaalt met huishoudgrootte.
        tax_free_assets = config.box3_tax_free_assets_single * Decimal(len(members))

        net_asset_factor = (total_net_assets / gross_assets) if gross_assets > 0 else Decimal("0")
        net_savings = total_savings * net_asset_factor
        net_non_savings = (total_investments + total_other_assets) * net_asset_factor

        deemed_return_savings = net_savings * config.box3_savings_return_rate
        deemed_return_non_savings = net_non_savings * config.box3_investment_return_rate
        deemed_return_total = deemed_return_savings + deemed_return_non_savings

        corrected_assets = max(Decimal("0"), total_net_assets - tax_free_assets)
        correction_factor = (corrected_assets / total_net_assets) if total_net_assets > 0 else Decimal("0")
        box3_income = deemed_return_total * correction_factor
        box3_tax = box3_income * config.box3_rate

        custom_pct_map = {
            member_id: dec(value)
            for member_id, value in custom_allocation.items()
            if member_id in member_ids
        }
        box3_allocation = compute_box3_allocation(
            member_ids,
            member_net_assets,
            allocation_strategy,
            box3_tax,
            custom_pct_map,
        )

        for row in member_results:
            allocated = box3_allocation.get(row["member_id"], Decimal("0"))
            row["box3"]["allocated_tax"] = float(allocated)

        box1_taxable_income_total = sum(
            (dec(m["box1"]["taxable_income"]) for m in member_results),
            Decimal("0"),
        )
        box2_taxable_income_total = sum(
            (dec(m["box2"]["taxable_income"]) for m in member_results),
            Decimal("0"),
        )
        verzamelinkomen = box1_taxable_income_total + box2_taxable_income_total + box3_income

        premium_basis = min(box1_taxable_income_total, PREMIUM_BASE_CAP)
        premium_aow = premium_basis * PREMIUM_AOW_RATE
        premium_anw = premium_basis * PREMIUM_ANW_RATE
        premium_wlz = premium_basis * PREMIUM_WLZ_RATE
        total_premiums = premium_aow + premium_anw + premium_wlz

        box1_box3_tax = box1_total + box3_tax
        gross_income_tax = box1_box3_tax + total_premiums + box2_total
        net_settlement = gross_income_tax - total_tax_credits - total_prepaid_taxes
        total_gross_income = sum((dec(m["box1"]["gross_income"]) for m in member_results), Decimal("0"))
        effective_rate = (
            float((gross_income_tax / total_gross_income) * Decimal("100"))
            if total_gross_income > 0
            else 0.0
        )

        filing_steps = [
            "Persoonsgegevens controleren",
            "Inkomsten invoeren",
            "Woning en hypotheek invoeren",
            "Vermogen invoeren",
            "Aftrekposten invoeren",
            "Partnerverdeling optimaliseren",
            "Controle",
            "Indienen",
        ]

        return jsonify(
            {
                "success": True,
                "tax_year": config.year,
                "input_saved_to": saved_file,
                "fiscal_partner": fiscal_partner,
                "allocation_strategy": allocation_strategy,
                "members": member_results,
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
                    "corrected_deemed_return": float(box3_income),
                    "total_tax": float(box3_tax),
                    "allocation": {member_id: float(value) for member_id, value in box3_allocation.items()},
                },
                "settlement": {
                    "box1_box3_tax": float(box1_box3_tax),
                    "box2_tax": float(box2_total),
                    "premiums": {
                        "basis": float(premium_basis),
                        "aow": float(premium_aow),
                        "anw": float(premium_anw),
                        "wlz": float(premium_wlz),
                        "total": float(total_premiums),
                    },
                    "gross_income_tax": float(gross_income_tax),
                    "total_tax_credits": float(total_tax_credits),
                    "total_prepaid_taxes": float(total_prepaid_taxes),
                    "net_settlement": float(net_settlement),
                    "result_type": "TE_BETALEN" if net_settlement >= 0 else "TERUGGAAF",
                    "effective_rate": round(effective_rate, 2),
                },
                "verzamelinkomen": float(verzamelinkomen),
                "filing_steps": filing_steps,
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
