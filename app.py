"""
Dutch Tax Calculator - Web GUI

A Flask-based web application for calculating Dutch income and wealth taxes.
"""

from flask import Flask, render_template, request, jsonify
from decimal import Decimal
from datetime import datetime
import json
from pathlib import Path
import re
import traceback

from object_model import (
    Person, Household, IncomeSource, Asset, Deduction, TaxCredit, OwnHome,
    IncomeSourceType, AssetType, ResidencyStatus, AllocationStrategy
)
from tax_brackets import get_latest_tax_config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dutch-tax-calculator-secret'


def compute_box1_bracket_breakdown(taxable_income: Decimal, brackets: list) -> list[dict]:
    """Return per-bracket tax application details for Box1."""
    breakdown = []
    for bracket in sorted(brackets, key=lambda b: b.lower_bound):
        taxable_in_bracket = bracket.taxable_amount(taxable_income)
        if taxable_in_bracket <= 0:
            continue
        tax_in_bracket = taxable_in_bracket * bracket.rate
        breakdown.append({
            'description': bracket.description,
            'lower_bound': float(bracket.lower_bound),
            'upper_bound': float(bracket.upper_bound) if bracket.upper_bound is not None else None,
            'rate': float(bracket.rate),
            'taxable_amount': float(taxable_in_bracket),
            'tax_amount': float(tax_in_bracket),
        })
    return breakdown


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


@app.route('/')
def index():
    """Home page with tax form."""
    return render_template('index.html')


@app.route('/api/income-types')
def get_income_types():
    """Get available income source types."""
    return jsonify({
        'types': [
            {'id': 'EMPLOYMENT', 'label': 'Loon uit dienstverband'},
            {'id': 'SELF_EMPLOYMENT', 'label': 'Winst uit onderneming'},
            {'id': 'RENTAL', 'label': 'Huurinkomsten'},
            {'id': 'PENSION', 'label': 'Pensioenuitkering'},
            {'id': 'INVESTMENT', 'label': 'Beleggingsinkomsten (dividend/rente)'},
            {'id': 'OTHER', 'label': 'Overig'},
        ]
    })


@app.route('/api/asset-types')
def get_asset_types():
    """Get available asset types."""
    return jsonify({
        'types': [
            {'id': 'SAVINGS', 'label': 'Spaarrekening'},
            {'id': 'INVESTMENT', 'label': 'Beleggingsportefeuille'},
            {'id': 'REAL_ESTATE', 'label': 'Onroerend goed (excl. eigen woning)'},
            {'id': 'BUSINESS', 'label': 'Ondernemingsvermogen'},
            {'id': 'OTHER', 'label': 'Overig vermogen'},
        ]
    })


@app.route('/api/allocation-strategies')
def get_allocation_strategies():
    """Get available Box3 allocation strategies."""
    return jsonify({
        'strategies': [
            {'id': 'EQUAL', 'label': 'Gelijk (50-50)'},
            {'id': 'PROPORTIONAL', 'label': 'Proportioneel (op fictief rendement)'},
            {'id': 'CUSTOM', 'label': 'Aangepaste percentages'},
        ]
    })


@app.route('/api/calculate', methods=['POST'])
def calculate_tax():
    """Calculate tax based on form submission."""
    try:
        data = request.get_json()
        saved_file = save_input_data_to_json(data)
        
        # Get tax configuration for 2025
        config = get_latest_tax_config()
        
        # Create household
        household = Household(household_id=data.get('household_id', 'WEB_001'))
        
        # Process members
        for member_data in data.get('members', []):
            try:
                # Create person - use 'name' not 'full_name'
                person = Person(
                    name=member_data.get('full_name', ''),
                    bsn=member_data.get('bsn', ''),
                    residency_status=ResidencyStatus[member_data.get('residency_status', 'RESIDENT')]
                )

                own_home = member_data.get('own_home')
                if own_home:
                    person.own_home = OwnHome(
                        woz_value=float(own_home.get('woz_value', 0)),
                        period_fraction=float(own_home.get('period_fraction', 1)),
                    )
                
                # Add income sources
                for income in member_data.get('incomes', []):
                    income_type = IncomeSourceType[income.get('type', 'EMPLOYMENT')]
                    # IncomeSource expects: name, source_type, gross_amount, description
                    person.income_sources.append(
                        IncomeSource(
                            name=income.get('description', income.get('type', 'Income')),
                            source_type=income_type,
                            gross_amount=Decimal(str(income.get('amount', 0))),
                            description=income.get('description', '')
                        )
                    )
                
                # Add deductions
                for deduction in member_data.get('deductions', []):
                    # Deduction expects: name, amount, deduction_type, description
                    person.deductions.append(
                        Deduction(
                            name=deduction.get('description', 'Deduction'),
                            amount=Decimal(str(deduction.get('amount', 0))),
                            deduction_type='personal',
                            description=deduction.get('description', '')
                        )
                    )
                
                # Add withheld tax
                if member_data.get('withheld_tax'):
                    person.withheld_tax = Decimal(str(member_data.get('withheld_tax')))

                # Backward compatibility for older payloads where dividend tax was person-level.
                if member_data.get('dividend_tax_paid'):
                    person.dividend_tax_paid = Decimal(str(member_data.get('dividend_tax_paid')))

                # Add explicit tax credits/heffingskortingen (optional)
                for credit in member_data.get('tax_credits', []):
                    person.tax_credits.append(
                        TaxCredit(
                            name=credit.get('name', 'Tax Credit'),
                            amount=Decimal(str(credit.get('amount', 0))),
                            description=credit.get('description', ''),
                        )
                    )
                
                # Add assets
                for asset in member_data.get('assets', []):
                    asset_type = AssetType[asset.get('type', 'SAVINGS')]
                    # Asset expects: name, asset_type, value, description
                    person.assets.append(
                        Asset(
                            name=asset.get('description', asset.get('type', 'Asset')),
                            asset_type=asset_type,
                            value=Decimal(str(asset.get('value', 0))),
                            dividend_tax_paid=Decimal(str(asset.get('dividend_tax_paid', 0))),
                            description=asset.get('description', '')
                        )
                    )
                
                household.add_member(person)
                
            except Exception as e:
                return jsonify({'error': f'Error processing member: {str(e)}'}), 400
        
        # Calculate taxes
        box1_breakdown = {}
        box1_brackets_applied_totals = {}
        total_box1 = Decimal('0')
        
        for person in household.members:
            taxable_income = person.compute_taxable_income()
            box1_tax = person.compute_box1_tax(config.box1_brackets)
            bracket_breakdown = compute_box1_bracket_breakdown(taxable_income, config.box1_brackets)

            for row in bracket_breakdown:
                key = row['description']
                if key not in box1_brackets_applied_totals:
                    box1_brackets_applied_totals[key] = {
                        'description': row['description'],
                        'rate': row['rate'],
                        'taxable_amount': Decimal('0'),
                        'tax_amount': Decimal('0'),
                    }
                box1_brackets_applied_totals[key]['taxable_amount'] += Decimal(str(row['taxable_amount']))
                box1_brackets_applied_totals[key]['tax_amount'] += Decimal(str(row['tax_amount']))

            box1_breakdown[person.name] = {
                'gross_income': float(person.total_gross_income()),
                'deductions': float(person.total_deductions()),
                'taxable_income': float(taxable_income),
                'box1_tax': float(box1_tax),
                'box1_brackets': bracket_breakdown,
                'tax_credits': float(person.total_tax_credits()),
                'withheld_tax': float(person.withheld_tax),
                'dividend_tax_paid': float(person.total_dividend_tax_paid()),
                'prepaid_taxes': float(person.compute_prepaid_taxes()),
                'net_liability': float(person.compute_net_tax_liability(config.box1_brackets)),
                'assets': float(person.total_asset_value()),
            }
            total_box1 += box1_tax
        
        # Calculate Box3
        strategy = AllocationStrategy[data.get('allocation_strategy', 'EQUAL')]
        tax_free_assets = (
            config.box3_tax_free_assets_partner
            if len(household.members) > 1
            else config.box3_tax_free_assets_single
        )

        box3_deemed_return = household.compute_box3_deemed_return(
            config.box3_savings_return_rate,
            config.box3_investment_return_rate,
        )

        savings_assets = household.total_savings_assets()
        investment_assets = household.total_investment_assets()
        savings_deemed_return = savings_assets * config.box3_savings_return_rate
        investment_deemed_return = investment_assets * config.box3_investment_return_rate
        total_assets = household.total_asset_value()
        corrected_assets = max(Decimal('0'), total_assets - tax_free_assets)
        correction_factor = (corrected_assets / total_assets) if total_assets > 0 else Decimal('0')

        box3_corrected_deemed_return = household.compute_box3_corrected_deemed_return(
            config.box3_savings_return_rate,
            config.box3_investment_return_rate,
            tax_free_assets,
        )
        box3_tax = household.compute_box3_tax(
            config.box3_rate,
            config.box3_savings_return_rate,
            config.box3_investment_return_rate,
            tax_free_assets,
        )
        allocation = household.allocate_box3_between_partners(
            config.box3_rate,
            strategy,
            savings_return_rate=config.box3_savings_return_rate,
            investment_return_rate=config.box3_investment_return_rate,
            tax_free_assets=tax_free_assets,
        )

        # Box1, verzamelinkomen, and settlement
        total_box1_taxable_income = sum(
            (member.compute_taxable_income() for member in household.members),
            Decimal('0')
        )
        verzamelinkomen = household.compute_verzamelinkomen(
            config.box3_savings_return_rate,
            config.box3_investment_return_rate,
            tax_free_assets,
        )
        total_tax_credits = sum((member.total_tax_credits() for member in household.members), Decimal('0'))
        total_prepaid_taxes = sum((member.compute_prepaid_taxes() for member in household.members), Decimal('0'))
        gross_income_tax = total_box1 + box3_tax
        net_settlement = gross_income_tax - total_tax_credits - total_prepaid_taxes
        
        # Total calculation
        total_tax_per_member = household.compute_total_tax(
            config.box1_brackets,
            config.box3_rate,
            strategy,
            box3_savings_return_rate=config.box3_savings_return_rate,
            box3_investment_return_rate=config.box3_investment_return_rate,
            box3_tax_free_assets=tax_free_assets,
        )
        total_tax = sum(total_tax_per_member.values(), Decimal('0'))
        box1_brackets_applied = sorted(
            [
                {
                    'description': row['description'],
                    'rate': row['rate'],
                    'taxable_amount': float(row['taxable_amount']),
                    'tax_amount': float(row['tax_amount']),
                }
                for row in box1_brackets_applied_totals.values()
            ],
            key=lambda item: item['rate']
        )
        total_income = household.total_gross_income()
        
        # Calculate effective tax rate
        if total_income > 0:
            effective_rate = (float(total_tax) / float(total_income)) * 100
        else:
            effective_rate = 0
        
        return jsonify({
            'success': True,
            'box1_breakdown': box1_breakdown,
            'box1_total': float(total_box1),
            'box1_taxable_income_total': float(total_box1_taxable_income),
            'box3_tax': float(box3_tax),
            'box3_rate': float(config.box3_rate * 100),
            'box1_brackets_applied': box1_brackets_applied,
            'box3_savings_return_rate': float(config.box3_savings_return_rate * 100),
            'box3_investment_return_rate': float(config.box3_investment_return_rate * 100),
            'box3_savings_assets': float(savings_assets),
            'box3_investment_assets': float(investment_assets),
            'box3_savings_deemed_return': float(savings_deemed_return),
            'box3_investment_deemed_return': float(investment_deemed_return),
            'box3_correction_factor': float(correction_factor),
            'box3_corrected_savings_deemed_return': float(savings_deemed_return * correction_factor),
            'box3_corrected_investment_deemed_return': float(investment_deemed_return * correction_factor),
            'box3_deemed_return': float(box3_deemed_return),
            'box3_corrected_deemed_return': float(box3_corrected_deemed_return),
            'box3_tax_free_assets': float(tax_free_assets),
            'box3_allocation': {
                name: float(amount) 
                for name, amount in allocation.items()
            },
            'total_tax': float(total_tax),
            'gross_income_tax': float(gross_income_tax),
            'verzamelinkomen': float(verzamelinkomen),
            'total_prepaid_taxes': float(total_prepaid_taxes),
            'total_tax_credits': float(total_tax_credits),
            'net_settlement': float(net_settlement),
            'total_assets': float(total_assets),
            'total_income': float(total_income),
            'effective_tax_rate': round(effective_rate, 2),
            'general_tax_credit': float(config.general_tax_credit),
            'tax_year': config.year,
            'input_saved_to': saved_file,
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Calculation error: {str(e)}'}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Page not found'}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Server error'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8000)
