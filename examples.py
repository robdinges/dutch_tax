"""
Quick Examples - Using Tax Configurations

Demonstrates how to use the tax_brackets module in your code.
"""

from decimal import Decimal
from object_model import (
    Person, Household, IncomeSource, Asset, Deduction, TaxCredit,
    IncomeSourceType, AssetType, ResidencyStatus, AllocationStrategy
)
from tax_brackets import get_tax_config, get_latest_tax_config, TAX_CONFIGS


# ============================================================================
# EXAMPLE 1: Use Latest Tax Configuration (2025)
# ============================================================================

def example_1_latest_config():
    """Get and use the latest available tax year."""
    print("=" * 70)
    print("EXAMPLE 1: Using Latest Tax Configuration")
    print("=" * 70)
    
    config = get_latest_tax_config()
    print(f"Using tax year: {config.year}")
    print(f"General tax credit: € {config.general_tax_credit:,.2f}")
    print(f"Box3 rate: {float(config.box3_rate) * 100}%")
    print(f"Number of tax brackets: {len(config.box1_brackets)}")
    print()
    
    # Create a simple person
    person = Person(
        name="Alice Johnson",
        bsn="123456789",
        residency_status=ResidencyStatus.RESIDENT,
        income_sources=[
            IncomeSource(
                name="Employment",
                source_type=IncomeSourceType.EMPLOYMENT,
                gross_amount=Decimal(50_000)
            ),
        ],
        tax_credits=[
            TaxCredit(
                name="General Tax Credit",
                amount=config.general_tax_credit
            ),
        ],
    )
    
    # Calculate tax
    tax = person.compute_box1_tax(config.box1_brackets)
    net_tax = person.compute_net_tax_liability(config.box1_brackets)
    
    print(f"Gross income: € {person.total_gross_income():,.2f}")
    print(f"Taxable income: € {person.compute_taxable_income():,.2f}")
    print(f"Box1 tax (before credits): € {tax:,.2f}")
    print(f"Net tax liability: € {net_tax:,.2f}")
    print()


# ============================================================================
# EXAMPLE 2: Use Specific Tax Year (2024)
# ============================================================================

def example_2_specific_year():
    """Get tax configuration for a specific year."""
    print("=" * 70)
    print("EXAMPLE 2: Using Specific Tax Year (2024)")
    print("=" * 70)
    
    config_2024 = get_tax_config(2024)
    config_2025 = get_tax_config(2025)
    
    print(f"2024 General tax credit: € {config_2024.general_tax_credit:,.2f}")
    print(f"2025 General tax credit: € {config_2025.general_tax_credit:,.2f}")
    print(f"Increase: € {config_2025.general_tax_credit - config_2024.general_tax_credit:,.2f}")
    print()
    
    # Compare tax brackets
    print("2024 First bracket:")
    b1_2024 = config_2024.box1_brackets[0]
    print(f"  Range: € {b1_2024.lower_bound:,.0f} - € {b1_2024.upper_bound:,.0f}")
    print(f"  Rate: {float(b1_2024.rate) * 100}%")
    print()
    
    print("2025 First bracket:")
    b1_2025 = config_2025.box1_brackets[0]
    print(f"  Range: € {b1_2025.lower_bound:,.0f} - € {b1_2025.upper_bound:,.0f}")
    print(f"  Rate: {float(b1_2025.rate) * 100}%")
    print()


# ============================================================================
# EXAMPLE 3: Compare Multiple Years
# ============================================================================

def example_3_compare_years():
    """Compare tax liability across multiple years for the same person."""
    print("=" * 70)
    print("EXAMPLE 3: Tax Liability Comparison (2023-2025)")
    print("=" * 70)
    
    income = Decimal(60_000)
    deductions = Decimal(5_000)
    
    print(f"Scenario: € {income:,.0f} income, € {deductions:,.0f} deductions")
    print()
    
    for year in sorted(TAX_CONFIGS.keys()):
        config = get_tax_config(year)
        
        person = Person(
            name="Bob Smith",
            bsn="987654321",
            income_sources=[
                IncomeSource(
                    name="Employment",
                    source_type=IncomeSourceType.EMPLOYMENT,
                    gross_amount=income
                ),
            ],
            deductions=[
                Deduction(
                    name="Professional",
                    amount=deductions,
                    deduction_type="professional"
                ),
            ],
            tax_credits=[
                TaxCredit(name="General", amount=config.general_tax_credit),
            ],
        )
        
        tax = person.compute_box1_tax(config.box1_brackets)
        net_tax = person.compute_net_tax_liability(config.box1_brackets)
        
        print(f"{year}:")
        print(f"  Tax (before credits): € {tax:,.2f}")
        print(f"  Net tax: € {net_tax:,.2f}")
        print()


# ============================================================================
# EXAMPLE 4: Household with Box3 Allocation
# ============================================================================

def example_4_household_box3():
    """Calculate Box3 tax for household with allocation strategies."""
    print("=" * 70)
    print("EXAMPLE 4: Household Box3 Tax Allocation")
    print("=" * 70)
    
    config = get_latest_tax_config()
    
    # Create household members
    spouse1 = Person(
        name="Peter",
        bsn="111111111",
        assets=[
            Asset(
                name="Savings",
                asset_type=AssetType.SAVINGS,
                value=Decimal(100_000)
            ),
        ],
    )
    
    spouse2 = Person(
        name="Paula",
        bsn="222222222",
        assets=[
            Asset(
                name="Stocks",
                asset_type=AssetType.STOCKS,
                value=Decimal(50_000)
            ),
        ],
    )
    
    household = Household(household_id="HH001")
    household.add_member(spouse1)
    household.add_member(spouse2)
    
    tax_free_assets = config.box3_tax_free_assets_partner
    deemed_return = household.compute_box3_deemed_return(
        config.box3_savings_return_rate,
        config.box3_investment_return_rate,
    )
    corrected_deemed_return = household.compute_box3_corrected_deemed_return(
        config.box3_savings_return_rate,
        config.box3_investment_return_rate,
        tax_free_assets,
    )
    total_box3 = household.compute_box3_tax(
        config.box3_rate,
        config.box3_savings_return_rate,
        config.box3_investment_return_rate,
        tax_free_assets,
    )
    print(f"Total household assets: € {household.total_asset_value():,.2f}")
    print(f"Heffingsvrij vermogen (partners): € {tax_free_assets:,.2f}")
    print(f"Fictief rendement totaal: € {deemed_return:,.2f}")
    print(
        "Gecorrigeerd fictief rendement ((gecorrigeerd_vermogen / totaal_vermogen) * fictief_rendement): "
        f"€ {corrected_deemed_return:,.2f}"
    )
    print(f"Total Box3 tax ({float(config.box3_rate) * 100:.2f}%): € {total_box3:,.2f}")
    print()
    
    # Equal allocation
    print("EQUAL allocation:")
    equal = household.allocate_box3_between_partners(
        config.box3_rate,
        AllocationStrategy.EQUAL,
        savings_return_rate=config.box3_savings_return_rate,
        investment_return_rate=config.box3_investment_return_rate,
        tax_free_assets=tax_free_assets,
    )
    for bsn, tax in equal.items():
        member = next(m for m in household.members if m.bsn == bsn)
        print(f"  {member.name}: € {tax:,.2f}")
    print()
    
    # Proportional allocation
    print("PROPORTIONAL allocation (based on wealth):")
    proportional = household.allocate_box3_between_partners(
        config.box3_rate,
        AllocationStrategy.PROPORTIONAL,
        savings_return_rate=config.box3_savings_return_rate,
        investment_return_rate=config.box3_investment_return_rate,
        tax_free_assets=tax_free_assets,
    )
    for bsn, tax in proportional.items():
        member = next(m for m in household.members if m.bsn == bsn)
        wealth_pct = (member.total_asset_value() / household.total_asset_value()) * 100
        print(f"  {member.name}: € {tax:,.2f} ({wealth_pct:.1f}% of assets)")
    print()


# ============================================================================
# EXAMPLE 5: Available Tax Years
# ============================================================================

def example_5_list_available_years():
    """Show all available tax year configurations."""
    print("=" * 70)
    print("EXAMPLE 5: Available Tax Year Configurations")
    print("=" * 70)
    
    for year in sorted(TAX_CONFIGS.keys()):
        config = get_tax_config(year)
        print(f"\nYear {year}:")
        print(f"  {config.description}")
        print(f"  General tax credit: € {config.general_tax_credit:,.2f}")
        print(f"  Box3 rate: {float(config.box3_rate) * 100}%")
        print(f"  Tax brackets:")
        for bracket in config.box1_brackets:
            upper = f"€ {bracket.upper_bound:,.0f}" if bracket.upper_bound else "unlimited"
            print(f"    € {bracket.lower_bound:,.0f} - {upper}: {float(bracket.rate) * 100:.2f}%")
    print()


# ============================================================================
# EXAMPLE 6: Edge Cases and Validation
# ============================================================================

def example_6_edge_cases():
    """Demonstrate edge cases and validation."""
    print("=" * 70)
    print("EXAMPLE 6: Edge Cases")
    print("=" * 70)
    
    config = get_latest_tax_config()
    
    # Case 1: Zero income
    print("Case 1: Person with zero income")
    person_zero = Person(
        name="Zero Income",
        bsn="000000000",
    )
    tax = person_zero.compute_box1_tax(config.box1_brackets)
    print(f"  Tax: € {tax:,.2f}")
    print()
    
    # Case 2: Very high income
    print("Case 2: Person with very high income (€2M)")
    person_high = Person(
        name="High Earner",
        bsn="999999999",
        income_sources=[
            IncomeSource(
                name="Investment Income",
                source_type=IncomeSourceType.INVESTMENT,
                gross_amount=Decimal(2_000_000)
            ),
        ],
        tax_credits=[
            TaxCredit(name="General", amount=config.general_tax_credit),
        ],
    )
    tax = person_high.compute_box1_tax(config.box1_brackets)
    effective_rate = (tax / person_high.total_gross_income()) * 100
    print(f"  Gross: € {person_high.total_gross_income():,.2f}")
    print(f"  Tax: € {tax:,.2f}")
    print(f"  Effective rate: {effective_rate:.2f}%")
    print()
    
    # Case 3: Withheld tax refund
    print("Case 3: Withheld tax refund scenario")
    person_refund = Person(
        name="Refund Case",
        bsn="111111111",
        income_sources=[
            IncomeSource(
                name="Employment",
                source_type=IncomeSourceType.EMPLOYMENT,
                gross_amount=Decimal(40_000)
            ),
        ],
        tax_credits=[
            TaxCredit(name="General", amount=config.general_tax_credit),
        ],
        withheld_tax=Decimal(12_000)  # High withholding
    )
    tax = person_refund.compute_box1_tax(config.box1_brackets)
    net = person_refund.compute_net_tax_liability(config.box1_brackets)
    refund = -net if net < 0 else Decimal(0)
    print(f"  Tax before credits: € {tax:,.2f}")
    print(f"  Withheld: € {person_refund.withheld_tax:,.2f}")
    print(f"  Net liability: € {max(net, 0):,.2f}")
    print(f"  Refund due: € {person_refund.withheld_tax - person_refund.compute_box1_tax(config.box1_brackets) + config.general_tax_credit:,.2f}")
    print()


# ============================================================================
# RUN EXAMPLES
# ============================================================================

if __name__ == "__main__":
    example_1_latest_config()
    example_2_specific_year()
    example_3_compare_years()
    example_4_household_box3()
    example_5_list_available_years()
    example_6_edge_cases()
    
    print("=" * 70)
    print("All examples completed!")
    print("=" * 70)
