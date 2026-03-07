"""
QUICK REFERENCE - Tax Form and Calculator

A cheat sheet for common tasks and quick syntax.
"""

# ============================================================================
# IMPORT EVERYTHING YOU NEED
# ============================================================================

from decimal import Decimal
from object_model import (
    Person, Household, IncomeSource, Asset, Deduction, TaxCredit,
    IncomeSourceType, AssetType, ResidencyStatus, AllocationStrategy
)
from tax_brackets import get_tax_config, get_latest_tax_config, TAX_CONFIGS


# ============================================================================
# QUICK RECIPES
# ============================================================================

# ---- 1. Create a simple person ----
person = Person(
    name="John Doe",
    bsn="123456789"
)

# ---- 2. Add income ----
person.income_sources.append(
    IncomeSource(
        name="Salary",
        source_type=IncomeSourceType.EMPLOYMENT,
        gross_amount=Decimal(50_000)
    )
)

# ---- 3. Add deduction ----
person.deductions.append(
    Deduction(
        name="Mortgage Interest",
        amount=Decimal(8_000),
        deduction_type="professional"
    )
)

# ---- 4. Add assets ----
person.assets.append(
    Asset(
        name="Savings",
        asset_type=AssetType.SAVINGS,
        value=Decimal(100_000)
    )
)

# ---- 5. Add tax credit ----
config = get_latest_tax_config()
person.tax_credits.append(
    TaxCredit(
        name="General Credit",
        amount=config.general_tax_credit
    )
)

# ---- 6. Get tax configuration for specific year ----
config_2024 = get_tax_config(2024)
config_2025 = get_tax_config(2025)
config_latest = get_latest_tax_config()

# ---- 7. Calculate taxable income ----
taxable = person.compute_taxable_income()
print(f"Taxable: € {taxable:,.2f}")

# ---- 8. Calculate Box1 tax ----
tax = person.compute_box1_tax(config.box1_brackets)
print(f"Tax: € {tax:,.2f}")

# ---- 9. Calculate net tax after credits and withholding ----
net_tax = person.compute_net_tax_liability(config.box1_brackets)
print(f"Net Tax: € {net_tax:,.2f}")

# ---- 10. Create household ----
household = Household(household_id="HH001")
household.add_member(person1)
household.add_member(person2)

# ---- 11. Calculate household Box3 ----
box3_tax = household.compute_box3_tax(config.box3_rate)
print(f"Box3 Tax: € {box3_tax:,.2f}")

# ---- 12. Allocate Box3 equally ----
allocation = household.allocate_box3_between_partners(
    config.box3_rate,
    AllocationStrategy.EQUAL
)
for bsn, tax_amount in allocation.items():
    print(f"BSN {bsn}: € {tax_amount:,.2f}")

# ---- 13. Allocate Box3 proportionally (by wealth) ----
allocation = household.allocate_box3_between_partners(
    config.box3_rate,
    AllocationStrategy.PROPORTIONAL
)

# ---- 14. Calculate total household tax ----
total = household.compute_total_tax(
    config.box1_brackets,
    config.box3_rate,
    AllocationStrategy.EQUAL
)
for bsn, tax_amount in total.items():
    print(f"BSN {bsn}: € {tax_amount:,.2f}")


# ============================================================================
# COMMON PATTERNS
# ============================================================================

# Pattern 1: Create person with all data at once
def create_person_complete():
    config = get_latest_tax_config()
    
    person = Person(
        name="Alice",
        bsn="987654321",
        residency_status=ResidencyStatus.RESIDENT,
        income_sources=[
            IncomeSource(
                name="Job",
                source_type=IncomeSourceType.EMPLOYMENT,
                gross_amount=Decimal(60_000)
            ),
        ],
        deductions=[
            Deduction(
                name="Mortgage",
                amount=Decimal(10_000),
                deduction_type="professional"
            ),
        ],
        assets=[
            Asset(
                name="Savings",
                asset_type=AssetType.SAVINGS,
                value=Decimal(50_000)
            ),
        ],
        tax_credits=[
            TaxCredit(
                name="General",
                amount=config.general_tax_credit
            ),
        ],
        withheld_tax=Decimal(15_000)
    )
    
    return person


# Pattern 2: Compare tax across multiple years
def compare_tax_years(gross_income):
    results = {}
    
    for year in sorted(TAX_CONFIGS.keys()):
        config = TAX_CONFIGS[year]
        person = Person(
            name="Test",
            bsn="000000000",
            income_sources=[
                IncomeSource(
                    name="Income",
                    source_type=IncomeSourceType.EMPLOYMENT,
                    gross_amount=gross_income
                ),
            ],
            tax_credits=[
                TaxCredit(
                    name="General",
                    amount=config.general_tax_credit
                ),
            ],
        )
        
        tax = person.compute_box1_tax(config.box1_brackets)
        results[year] = tax
    
    return results


# Pattern 3: Calculate effective tax rate
def effective_tax_rate(person, config):
    gross = person.total_gross_income()
    tax = person.compute_box1_tax(config.box1_brackets)
    
    if gross == 0:
        return Decimal(0)
    
    rate = (tax / gross) * 100
    return rate


# Pattern 4: Household summary report
def household_summary_report(household, config):
    print(f"Household: {household.household_id}")
    print(f"Members: {len(household.members)}")
    print(f"Total Income: € {household.total_gross_income():,.2f}")
    print(f"Total Assets: € {household.total_asset_value():,.2f}")
    
    total_box3 = household.compute_box3_tax(config.box3_rate)
    print(f"Box3 Tax: € {total_box3:,.2f}")
    
    total_tax = household.compute_total_tax(
        config.box1_brackets,
        config.box3_rate
    )
    
    print(f"Total Tax: € {sum(total_tax.values()):,.2f}")


# Pattern 5: Custom Box3 allocation
def custom_allocation_example(household, config, custom_amounts):
    # custom_amounts: dict of {bsn: Decimal(amount)}
    
    allocation = household.allocate_box3_between_partners(
        config.box3_rate,
        AllocationStrategy.CUSTOM,
        custom_allocation=custom_amounts
    )
    
    return allocation


# ============================================================================
# COMMON QUERIES
# ============================================================================

# Q: How do I get the tax credit amount for current year?
A1 = get_latest_tax_config().general_tax_credit
print(f"2025 Tax Credit: € {A1:,.2f}")

# Q: How do I calculate taxable income?
person = Person(name="Test", bsn="000")
taxable = person.compute_taxable_income()

# Q: How do I check Box1 tax before credits?
config = get_latest_tax_config()
box1_before_credits = person.compute_box1_tax(config.box1_brackets)

# Q: How do I check net tax after everything?
net_tax_due = person.compute_net_tax_liability(config.box1_brackets)

# Q: What are the tax brackets for 2025?
for bracket in config.box1_brackets:
    print(f"€{bracket.lower_bound:,} - €{bracket.upper_bound or 'unlimited':,}: {float(bracket.rate)*100:.2f}%")

# Q: What's the Box3 rate?
box3_rate = config.box3_rate
print(f"Box3 Rate: {float(box3_rate)*100}%")

# Q: How do I calculate household assets?
total_assets = sum(member.total_asset_value() for member in household.members)

# Q: How do I calculate household income?
total_income = sum(member.total_gross_income() for member in household.members)

# Q: What years are available?
available_years = sorted(TAX_CONFIGS.keys())
print(f"Available: {available_years}")

# Q: How do I add a new person to household?
household.add_member(person)

# Q: How do I remove a person from household?
household.remove_member(bsn="123456789")

# Q: How many members in household?
count = len(household.members)

# Q: How do I list all members?
for member in household.members:
    print(f"{member.name} (BSN: {member.bsn})")


# ============================================================================
# VALIDATION & ERROR HANDLING
# ============================================================================

# Don't do this:
person = Person(name="", bsn="")  # ❌ ValueError

# Do this:
try:
    person = Person(name="John", bsn="123456789")
except ValueError as e:
    print(f"Error: {e}")

# Decimal vs float:
amount = Decimal("12345.67")  # ✓ Correct (precise)
amount = 12345.67  # ✗ Avoid (floating point errors)

# Income validation:
if income < 0:  # ❌ ValueError in IncomeSource.__post_init__
    pass


# ============================================================================
# TIPS & TRICKS
# ============================================================================

# 1. Use Decimal for all money amounts
from decimal import Decimal
amount = Decimal("10000.50")  # ✓
amount = 10000.50  # ✗ (float precision issues)

# 2. Always provide config when calculating tax
config = get_latest_tax_config()  # Get current year
tax = person.compute_box1_tax(config.box1_brackets)  # Use brackets from config

# 3. Don't modify brackets directly - create new configs
# Instead of modifying: config.box1_brackets[0].rate = Decimal("0.20")
# Do this: create a new TaxYearConfig with custom brackets

# 4. Tax credits reduce tax liability (not income)
# Not: "€1000 credit means €1000 less income"
# Rather: "€1000 credit means €1000 less tax owed"

# 5. Withheld tax is reconciled against final tax owed
net = max(Decimal(0), tax_owed - withheld_tax)  # Amount due
refund = max(Decimal(0), withheld_tax - tax_owed)  # Refund due

# 6. Box3 applies to total household assets, not individual
# Calculate at household level, then allocate
total_box3 = household.compute_box3_tax(config.box3_rate)

# 7. Use AllocationStrategy to choose how to split Box3
# EQUAL: Same amount per person
# PROPORTIONAL: Based on individual wealth
# CUSTOM: Manual amounts

# 8. Effective tax rate = tax / gross income
effective_rate = (tax / gross) * 100

# 9. Marginal vs effective rate
marginal = config.box1_brackets[-1].rate  # Top bracket
effective = (total_tax / total_income) * 100  # Average across all income


# ============================================================================
# RUNNING THE FORM
# ============================================================================

# Interactive form:
# $ python3 tax_form.py

# Demo with pre-filled data:
# $ python3 form_demo.py

# All examples:
# $ python3 examples.py

# Main example:
# $ python3 object_model.py
