"""
DUTCH TAX SYSTEM - CONFIGURATION GUIDE

This document explains the structure and how to maintain tax brackets and rates.
"""

# ============================================================================
# FILE STRUCTURE
# ============================================================================

"""
object_model.py
  - Core domain model classes (Person, Household, etc.)
  - Tax calculation logic
  - TaxYearConfig and TaxBracket data classes
  - No hardcoded rates or tax year data

tax_brackets.py
  - All tax bracket definitions for different years
  - Realistic Dutch tax rates from Belastingdienst
  - Easy to maintain and update annually
  - Registry of tax configurations by year
"""


# ============================================================================
# REALISTIC DUTCH RATES - 2025
# ============================================================================

"""
BOX1 TAX BRACKETS (2025):
  Bracket 1: €0 - €37,895      @ 19.06%
  Bracket 2: €37,895 - €75,790 @ 28.43%
  Bracket 3: €75,790 - €1,011,724 @ 37.05%
  Bracket 4: €1,011,724+       @ 49.49%

BOX3 WEALTH TAX:
  Rate: 36% on deemed return of assets
  Applies to: Savings, stocks, bonds, real estate, crypto, etc.

TAX CREDITS & DEDUCTIONS:
  General tax credit: €2,917 (2025)
  Deductible items: Mortgage interest, professional expenses, charitable donations
  
WITHHELD TAX:
  Employers withhold provisional income tax
  Banks withhold savings tax
  Reconciliation done at year-end via tax return
"""


# ============================================================================
# HOW TO ADD A NEW TAX YEAR
# ============================================================================

"""
STEP 1: Add new tax year configuration in tax_brackets.py

Example for 2026:

    def create_2026_brackets() -> list[TaxBracket]:
        \"\"\"Create Box1 (income tax) brackets for 2026.\"\"\"
        return [
            TaxBracket(
                lower_bound=Decimal(0),
                upper_bound=Decimal(38_500),  # Updated threshold
                rate=Decimal("0.1920"),  # Updated rate
                description="First bracket (19.20%)"
            ),
            # ... more brackets ...
        ]

    TAX_CONFIG_2026 = TaxYearConfig(
        year=2026,
        box1_brackets=create_2026_brackets(),
        box3_rate=Decimal("0.3600"),
        general_tax_credit=Decimal(3_000),  # Updated
        description="Dutch tax year 2026 - Realistic rates"
    )

STEP 2: Register in TAX_CONFIGS dictionary

    TAX_CONFIGS: Dict[int, TaxYearConfig] = {
        2023: TAX_CONFIG_2023,
        2024: TAX_CONFIG_2024,
        2025: TAX_CONFIG_2025,
        2026: TAX_CONFIG_2026,  # ADD HERE
    }

STEP 3: Verify via API

    from tax_brackets import get_tax_config
    config_2026 = get_tax_config(2026)
"""


# ============================================================================
# USING TAX CONFIGURATIONS
# ============================================================================

"""
EXAMPLE 1: Get latest tax year config

    from tax_brackets import get_latest_tax_config
    config = get_latest_tax_config()
    print(f"Using tax year {config.year}")

EXAMPLE 2: Get specific year config

    from tax_brackets import get_tax_config
    config_2024 = get_tax_config(2024)
    
    person = Person(...)
    tax = person.compute_box1_tax(config_2024.box1_brackets)

EXAMPLE 3: Create custom bracket configuration

    from decimal import Decimal
    from object_model import TaxBracket, TaxYearConfig
    
    custom_brackets = [
        TaxBracket(Decimal(0), Decimal(50_000), Decimal("0.20")),
        TaxBracket(Decimal(50_000), None, Decimal("0.30")),
    ]
    
    custom_config = TaxYearConfig(
        year=2025,
        box1_brackets=custom_brackets,
        box3_rate=Decimal("0.36"),
        general_tax_credit=Decimal(2_917)
    )
"""


# ============================================================================
# DUTCH TAX AUTHORITY REFERENCES
# ============================================================================

"""
PRIMARY SOURCE:
  https://www.belastingdienst.nl/

KEY PAGES:
  - 2025 Tax brackets: https://www.belastingdienst.nl/inkomstenbelasting-1
  - Box3 rates: https://www.belastingdienst.nl/box-3-inkomstenbelasting
  - General tax credit: https://www.belastingdienst.nl/algemene-heffingskorting
  - Deduction rules: https://www.belastingdienst.nl/aftrekposten

ANNUAL UPDATES:
  - Tax brackets are indexed for inflation each January
  - General tax credit adjusted annually
  - Box3 rate remains constant at 36%
  - Subscribe to Belastingdienst newsletter for updates
"""


# ============================================================================
# MAINTENANCE CHECKLIST
# ============================================================================

"""
ANNUAL MAINTENANCE (Usually December-January):

  ☐ Check Belastingdienst website for new tax year rates
  ☐ Update bracket thresholds (inflation adjustment)
  ☐ Update bracket rates if changed
  ☐ Update general tax credit amount
  ☐ Create new create_YYYY_brackets() function
  ☐ Create new TAX_CONFIG_YYYY instance
  ☐ Add to TAX_CONFIGS dictionary
  ☐ Run example to verify calculations
  ☐ Update documentation with new rates
  ☐ Commit to version control with meaningful message

TESTING:
  ☐ Run unit tests if available
  ☐ Verify example output matches expected results
  ☐ Test edge cases (zero income, very high income)
  ☐ Verify Box3 allocation strategies work correctly
"""


# ============================================================================
# NOTES ON REALISTIC RATES
# ============================================================================

"""
Why these rates are realistic:

1. BOX1 BRACKETS:
   - Rates include both national income tax and employee social contributions
   - Progressive system: higher income taxed at higher marginal rates
   - Top rate (49.49%) reflects combined income tax + contributions
   - Brackets are indexed annually for inflation
   
2. BOX3 WEALTH TAX:
   - Applies to net assets after debt reduction
   - 36% rate on deemed return (not actual return on assets)
   - Deemed return calculation: typical investment return applied
   - Tax avoidance: some wealth may be shifted to lower-tax countries

3. GENERAL TAX CREDIT:
   - Reduces tax liability for all residents
   - Amount varies based on income level
   - Higher income = lower credit amount
   - Essentially negative tax for low earners

4. DEDUCTIONS:
   - Mortgage interest remains deductible
   - Professional expenses for self-employed
   - Some charitable donations
   - Healthcare expenses above threshold
   - Student loan interest

5. POLICY CHANGES OVER TIME:
   - 2024-2025: Threshold increases (~2-3% inflation)
   - General tax credit increased to support cost of living
   - Box3 rates relatively stable
   - Tax brackets gradually adjusted for wages/prices
"""


if __name__ == "__main__":
    print(__doc__)
