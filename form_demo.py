"""
Tax Form Demo - Automated Example

Demonstrates the tax form functionality with pre-populated data.
Useful for testing and understanding form workflow.
"""

from decimal import Decimal
from object_model import (
    Person, Household, IncomeSource, Asset, Deduction, TaxCredit,
    IncomeSourceType, AssetType, ResidencyStatus, AllocationStrategy
)
from tax_brackets import get_latest_tax_config


def demo_simple_tax_form():
    """Demo: Simple single-person tax form."""
    print("=" * 70)
    print("DEMO 1: Simple Single-Person Tax Form")
    print("=" * 70)
    print()
    
    config = get_latest_tax_config()
    
    # Create a simple person
    john = Person(
        name="John Anderson",
        bsn="123456789",
        residency_status=ResidencyStatus.RESIDENT,
        income_sources=[
            IncomeSource(
                name="Employment",
                source_type=IncomeSourceType.EMPLOYMENT,
                gross_amount=config.box1_brackets[1].upper_bound,  # Example: use bracket upper bound
                description="Full-time software engineer"
            ),
        ],
        deductions=[
            Deduction(
                name="Mortgage Interest",
                amount=config.box3_tax_free_assets_single,  # Example: use config value
                deduction_type="professional"
            ),
        ],
        assets=[
            Asset(
                name="Savings Account",
                asset_type=AssetType.SAVINGS,
                value=config.box3_tax_free_assets_partner  # Example: use config value
            ),
        ],
        tax_credits=[
            TaxCredit(
                name="General Tax Credit",
                amount=config.general_tax_credit
            ),
        ],
        withheld_tax=config.general_tax_credit  # Example: use config value
    )
    
    # Print form results
    print(f"Name: {john.name}")
    print(f"BSN: {john.bsn}")
    print()
    
    print("INCOME:")
    for source in john.income_sources:
        print(f"  • {source.name}: € {source.gross_amount:,.2f}")
    print(f"  Total Gross Income: € {john.total_gross_income():,.2f}")
    print()
    
    print("DEDUCTIONS:")
    for deduction in john.deductions:
        print(f"  • {deduction.name}: € {deduction.amount:,.2f}")
    print(f"  Total Deductions: € {john.total_deductions():,.2f}")
    print()
    
    print("TAX CALCULATION:")
    taxable = john.compute_taxable_income()
    box1_tax = john.compute_box1_tax(config.box1_brackets)
    net_tax = john.compute_net_tax_liability(config.box1_brackets)
    
    print(f"  Taxable Income: € {taxable:,.2f}")
    print(f"  Box1 Tax (before credits): € {box1_tax:,.2f}")
    print(f"  Tax Credits: € {john.total_tax_credits():,.2f}")
    print(f"  Withheld Tax: € {john.withheld_tax:,.2f}")
    print(f"  Net Tax Liability: € {net_tax:,.2f}")
    print()
    
    print("ASSETS:")
    for asset in john.assets:
        print(f"  • {asset.name} ({asset.asset_type.name}): € {asset.value:,.2f}")
    print(f"  Total Assets: € {john.total_asset_value():,.2f}")
    print()


def demo_household_tax_form():
    """Demo: Household with multiple persons and Box3 allocation."""
    print("=" * 70)
    print("DEMO 2: Household Tax Form with Box3 Allocation")
    print("=" * 70)
    print()
    
    config = get_latest_tax_config()
    
    # Create household
    household = Household(household_id="DEMO_HH002")
    
    # Add spouse 1
    spouse1 = Person(
        name="Maria Garcia",
        bsn="111111111",
        residency_status=ResidencyStatus.RESIDENT,
        income_sources=[
            IncomeSource(
                name="Employment",
                source_type=IncomeSourceType.EMPLOYMENT,
                gross_amount=Decimal(65_000),
                description="Senior Manager"
            ),
        ],
        deductions=[
            Deduction(
                name="Professional Expenses",
                amount=Decimal(4_000),
                deduction_type="professional"
            ),
        ],
        assets=[
            Asset(
                name="Savings Account",
                asset_type=AssetType.SAVINGS,
                value=Decimal(80_000)
            ),
            Asset(
                name="Investment Portfolio",
                asset_type=AssetType.STOCKS,
                value=Decimal(100_000)
            ),
        ],
        tax_credits=[
            TaxCredit(
                name="General Tax Credit",
                amount=config.general_tax_credit
            ),
        ],
        withheld_tax=Decimal(18_500)
    )
    
    # Add spouse 2
    spouse2 = Person(
        name="Carlos Garcia",
        bsn="222222222",
        residency_status=ResidencyStatus.RESIDENT,
        income_sources=[
            IncomeSource(
                name="Self-Employment",
                source_type=IncomeSourceType.SELF_EMPLOYMENT,
                gross_amount=Decimal(55_000),
                description="Freelance consultant"
            ),
            IncomeSource(
                name="Rental Income",
                source_type=IncomeSourceType.RENTAL,
                gross_amount=Decimal(18_000),
                description="Property rental"
            ),
        ],
        deductions=[
            Deduction(
                name="Business Expenses",
                amount=Decimal(8_000),
                deduction_type="professional"
            ),
            Deduction(
                name="Rental Maintenance",
                amount=Decimal(3_000),
                deduction_type="professional"
            ),
        ],
        assets=[
            Asset(
                name="Savings Account",
                asset_type=AssetType.SAVINGS,
                value=Decimal(50_000)
            ),
            Asset(
                name="Rental Property",
                asset_type=AssetType.REAL_ESTATE,
                value=Decimal(400_000)
            ),
        ],
        tax_credits=[
            TaxCredit(
                name="General Tax Credit",
                amount=config.general_tax_credit
            ),
        ],
        withheld_tax=Decimal(12_000)
    )
    
    household.add_member(spouse1)
    household.add_member(spouse2)
    
    # Display household form
    print(f"Household ID: {household.household_id}")
    print(f"Tax Year: {config.year}")
    print(f"Members: {len(household.members)}")
    print()
    
    # Individual results
    for member in household.members:
        print(f"\n{'=' * 70}")
        print(f"Member: {member.name} (BSN: {member.bsn})")
        print(f"{'=' * 70}")
        
        print(f"\nINCOME:")
        for source in member.income_sources:
            print(f"  • {source.name}: € {source.gross_amount:,.2f}")
        print(f"  Total: € {member.total_gross_income():,.2f}")
        
        print(f"\nDEDUCTIONS:")
        for deduction in member.deductions:
            print(f"  • {deduction.name}: € {deduction.amount:,.2f}")
        print(f"  Total: € {member.total_deductions():,.2f}")
        
        taxable = member.compute_taxable_income()
        box1_tax = member.compute_box1_tax(config.box1_brackets)
        net_tax = member.compute_net_tax_liability(config.box1_brackets)
        
        print(f"\nTAX:")
        print(f"  Taxable Income: € {taxable:,.2f}")
        print(f"  Box1 Tax (before credits): € {box1_tax:,.2f}")
        print(f"  Net Liability: € {net_tax:,.2f}")
        
        print(f"\nASSETS:")
        for asset in member.assets:
            print(f"  • {asset.name}: € {asset.value:,.2f}")
        print(f"  Total: € {member.total_asset_value():,.2f}")
    
    # Household summary
    print(f"\n{'=' * 70}")
    print("HOUSEHOLD SUMMARY")
    print(f"{'=' * 70}")
    print(f"\nTotal Household Income: € {household.total_gross_income():,.2f}")
    print(f"Total Household Assets: € {household.total_asset_value():,.2f}")
    print()
    
    # Box3 allocation
    tax_free_assets = config.box3_tax_free_assets_partner
    total_assets = household.total_asset_value()
    corrected_assets = max(Decimal(0), total_assets - tax_free_assets)
    correction_factor = (corrected_assets / total_assets) if total_assets > 0 else Decimal(0)
    savings_assets = household.total_savings_assets()
    investment_assets = household.total_investment_assets()
    savings_deemed_return = savings_assets * config.box3_savings_return_rate
    investment_deemed_return = investment_assets * config.box3_investment_return_rate
    corrected_deemed_return = (savings_deemed_return + investment_deemed_return) * correction_factor

    total_box3 = household.compute_box3_tax(
        config.box3_rate,
        config.box3_savings_return_rate,
        config.box3_investment_return_rate,
        tax_free_assets,
    )
    print(f"Heffingsvrij vermogen (partners): € {tax_free_assets:,.2f}")
    print(f"Gecorrigeerd vermogen: € {corrected_assets:,.2f}")
    print(f"Correctiefactor: {float(correction_factor) * 100:.2f}%")
    print(f"Fictief rendement spaargeld ({float(config.box3_savings_return_rate) * 100:.2f}%): € {savings_deemed_return:,.2f}")
    print(f"Fictief rendement beleggingen ({float(config.box3_investment_return_rate) * 100:.2f}%): € {investment_deemed_return:,.2f}")
    print(
        "Gecorrigeerd fictief rendement ((gecorrigeerd_vermogen / totaal_vermogen) * fictief_rendement): "
        f"€ {corrected_deemed_return:,.2f}"
    )
    print(f"Total Box3 Tax ({float(config.box3_rate) * 100:.2f}%): € {total_box3:,.2f}")
    print()
    
    allocation_equal = household.allocate_box3_between_partners(
        config.box3_rate,
        AllocationStrategy.EQUAL,
        savings_return_rate=config.box3_savings_return_rate,
        investment_return_rate=config.box3_investment_return_rate,
        tax_free_assets=tax_free_assets,
    )
    allocation_proportional = household.allocate_box3_between_partners(
        config.box3_rate,
        AllocationStrategy.PROPORTIONAL,
        savings_return_rate=config.box3_savings_return_rate,
        investment_return_rate=config.box3_investment_return_rate,
        tax_free_assets=tax_free_assets,
    )
    
    print("Box3 Allocation (Equal Strategy):")
    for bsn, tax in allocation_equal.items():
        member = next(m for m in household.members if m.bsn == bsn)
        print(f"  • {member.name}: € {tax:,.2f}")
    
    print("\nBox3 Allocation (Proportional Strategy - based on fictief rendement):")
    for bsn, tax in allocation_proportional.items():
        member = next(m for m in household.members if m.bsn == bsn)
        wealth_pct = (member.total_asset_value() / household.total_asset_value()) * 100
        print(f"  • {member.name}: € {tax:,.2f} ({wealth_pct:.1f}% of assets)")
    
    # Total tax liability
    print(f"\n{'=' * 70}")
    print("TOTAL TAX LIABILITY")
    print(f"{'=' * 70}")
    print()
    
    total_tax = household.compute_total_tax(
        config.box1_brackets,
        config.box3_rate,
        AllocationStrategy.EQUAL
    )
    
    total_all = Decimal(0)
    for bsn, tax in total_tax.items():
        member = next(m for m in household.members if m.bsn == bsn)
        print(f"{member.name}: € {tax:,.2f}")
        total_all += tax
    
    print(f"\nTotal Household Tax: € {total_all:,.2f}")
    print()


def demo_self_employed_tax_form():
    """Demo: Self-employed person with business expenses."""
    print("=" * 70)
    print("DEMO 3: Self-Employed Person Tax Form")
    print("=" * 70)
    print()
    
    config = get_latest_tax_config()
    
    # Create self-employed person
    entrepreneur = Person(
        name="Sophie Müller",
        bsn="333333333",
        residency_status=ResidencyStatus.RESIDENT,
        income_sources=[
            IncomeSource(
                name="Freelance Income",
                source_type=IncomeSourceType.SELF_EMPLOYMENT,
                gross_amount=Decimal(85_000),
                description="IT Consulting"
            ),
        ],
        deductions=[
            Deduction(
                name="Office Rent",
                amount=Decimal(12_000),
                deduction_type="professional"
            ),
            Deduction(
                name="Equipment & Software",
                amount=Decimal(5_000),
                deduction_type="professional"
            ),
            Deduction(
                name="Travel Expenses",
                amount=Decimal(3_500),
                deduction_type="professional"
            ),
            Deduction(
                name="Professional Development",
                amount=Decimal(2_000),
                deduction_type="professional"
            ),
        ],
        assets=[
            Asset(
                name="Business Savings",
                asset_type=AssetType.SAVINGS,
                value=Decimal(120_000)
            ),
        ],
        tax_credits=[
            TaxCredit(
                name="General Tax Credit",
                amount=config.general_tax_credit
            ),
        ],
        withheld_tax=Decimal(8_000)  # Quarterly tax payments
    )
    
    print(f"Name: {entrepreneur.name} (BSN: {entrepreneur.bsn})")
    print(f"Status: Self-Employed")
    print()
    
    print("INCOME:")
    for source in entrepreneur.income_sources:
        print(f"  • {source.name}: € {source.gross_amount:,.2f}")
    print(f"  Gross Income: € {entrepreneur.total_gross_income():,.2f}")
    print()
    
    print("BUSINESS DEDUCTIONS:")
    for deduction in entrepreneur.deductions:
        print(f"  • {deduction.name}: € {deduction.amount:,.2f}")
    print(f"  Total Deductions: € {entrepreneur.total_deductions():,.2f}")
    print()
    
    taxable = entrepreneur.compute_taxable_income()
    gross = entrepreneur.total_gross_income()
    deductions = entrepreneur.total_deductions()
    
    print("CALCULATION:")
    print(f"  Gross Income:        € {gross:>12,.2f}")
    print(f"  Less: Deductions:    € {deductions:>12,.2f}")
    print(f"  Taxable Income:      € {taxable:>12,.2f}")
    print()
    
    box1_tax = entrepreneur.compute_box1_tax(config.box1_brackets)
    credits = entrepreneur.total_tax_credits()
    tax_after_credits = max(Decimal(0), box1_tax - credits)
    withheld = entrepreneur.withheld_tax
    net_tax = entrepreneur.compute_net_tax_liability(config.box1_brackets)
    
    print("TAX LIABILITY:")
    print(f"  Box1 Tax (before credits): € {box1_tax:>12,.2f}")
    print(f"  Less: Tax Credits:         € {credits:>12,.2f}")
    print(f"  Tax after credits:         € {tax_after_credits:>12,.2f}")
    print(f"  Less: Withheld Tax:        € {withheld:>12,.2f}")
    print(f"  Amount Due/(Refund):       € {net_tax:>12,.2f}")
    print()
    
    effective_rate = (box1_tax / taxable * 100) if taxable > 0 else 0
    print(f"Effective Tax Rate: {effective_rate:.2f}%")
    print()


if __name__ == "__main__":
    demo_simple_tax_form()
    print("\n" * 2)
    demo_household_tax_form()
    print("\n" * 2)
    demo_self_employed_tax_form()
