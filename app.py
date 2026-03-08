"""
Dutch Tax Calculator - Web GUI

A Flask-based web application for calculating Dutch income and wealth taxes.
"""

from flask import Flask, render_template, request, jsonify
from decimal import Decimal
from datetime import datetime
import json
from pathlib import Path
import traceback

from object_model import (
    Person, Household, IncomeSource, Asset, Deduction, TaxCredit, OwnHome,
    IncomeSourceType, AssetType, ResidencyStatus, AllocationStrategy
)
from tax_brackets import get_latest_tax_config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dutch-tax-calculator-secret'


def save_input_data_to_json(data: dict) -> str:
    """Persist submitted form data to a timestamped JSON file."""
    submissions_dir = Path(__file__).parent / "submissions"
    submissions_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    file_path = submissions_dir / f"input_{timestamp}.json"

    payload = {
        "saved_at": datetime.now().isoformat(),
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
            {'id': 'EMPLOYMENT', 'label': 'Employment (W-2/salary)'},
            {'id': 'SELF_EMPLOYMENT', 'label': 'Self-Employment (business)'},
            {'id': 'RENTAL', 'label': 'Rental (property income)'},
            {'id': 'PENSION', 'label': 'Pension (retirement)'},
            {'id': 'INVESTMENT', 'label': 'Investment (dividends, interest)'},
            {'id': 'OTHER', 'label': 'Other'},
        ]
    })


@app.route('/api/asset-types')
def get_asset_types():
    """Get available asset types."""
    return jsonify({
        'types': [
            {'id': 'SAVINGS', 'label': 'Savings Account'},
            {'id': 'INVESTMENT', 'label': 'Investment Portfolio'},
            {'id': 'REAL_ESTATE', 'label': 'Real Estate (primary residence excluded)'},
            {'id': 'BUSINESS', 'label': 'Business Assets'},
            {'id': 'OTHER', 'label': 'Other Assets'},
        ]
    })


@app.route('/api/allocation-strategies')
def get_allocation_strategies():
    """Get available Box3 allocation strategies."""
    return jsonify({
        'strategies': [
            {'id': 'EQUAL', 'label': 'Equal (50-50 split)'},
            {'id': 'PROPORTIONAL', 'label': 'Proportional (by income)'},
            {'id': 'CUSTOM', 'label': 'Custom percentages'},
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
                
                # Add assets
                for asset in member_data.get('assets', []):
                    asset_type = AssetType[asset.get('type', 'SAVINGS')]
                    # Asset expects: name, asset_type, value, description
                    person.assets.append(
                        Asset(
                            name=asset.get('description', asset.get('type', 'Asset')),
                            asset_type=asset_type,
                            value=Decimal(str(asset.get('value', 0))),
                            description=asset.get('description', '')
                        )
                    )
                
                household.add_member(person)
                
            except Exception as e:
                return jsonify({'error': f'Error processing member: {str(e)}'}), 400
        
        # Calculate taxes
        box1_breakdown = {}
        total_box1 = Decimal('0')
        
        for person in household.members:
            box1_tax = person.compute_box1_tax(config.box1_brackets)
            box1_breakdown[person.name] = {
                'gross_income': float(person.total_gross_income()),
                'deductions': float(person.total_deductions()),
                'taxable_income': float(person.compute_taxable_income()),
                'box1_tax': float(box1_tax),
                'tax_credits': float(person.total_tax_credits()),
                'withheld_tax': float(person.withheld_tax),
                'net_liability': float(person.compute_net_tax_liability(config.box1_brackets)),
                'assets': float(person.total_asset_value()),
            }
            total_box1 += box1_tax
        
        # Calculate Box3
        strategy = AllocationStrategy[data.get('allocation_strategy', 'EQUAL')]
        box3_tax = household.compute_box3_tax(config.box3_rate)
        allocation = household.allocate_box3_between_partners(config.box3_rate, strategy)
        
        # Total calculation
        total_tax_per_member = household.compute_total_tax(config.box1_brackets, config.box3_rate, strategy)
        total_tax = sum(total_tax_per_member.values(), Decimal('0'))
        total_assets = household.total_asset_value()
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
            'box3_tax': float(box3_tax),
            'box3_rate': float(config.box3_rate * 100),
            'box3_allocation': {
                name: float(amount) 
                for name, amount in allocation.items()
            },
            'total_tax': float(total_tax),
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
