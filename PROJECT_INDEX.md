"""
PROJECT INDEX - Dutch Tax System Calculator

Complete file structure and usage guide.
"""

# ============================================================================
# PROJECT STRUCTURE
# ============================================================================

"""
Dutch Tax System - Interactive Tax Calculator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 PROJECT FILES:

CORE FILES:
  ├─ object_model.py          (19 KB) Core domain model & tax calculations
  ├─ tax_brackets.py          (7.1 KB) Tax year configurations (2023-2025)
  │
INTERACTIVE FORMS:
  ├─ tax_form.py              (12 KB) Interactive command-line form
  ├─ form_demo.py             (13 KB) Pre-populated form demonstrations
  │
EXAMPLES & DOCS:
  ├─ examples.py              (11 KB) 6 usage examples & test cases
  ├─ README.md                (8.1 KB) Complete project documentation
  ├─ CONFIGURATION_GUIDE.md   (6.8 KB) How to maintain tax rates
  ├─ QUICK_REFERENCE.md       (10 KB) Cheat sheet & common patterns
  └─ PROJECT_INDEX.md         (this file) Navigation guide

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


# ============================================================================
# QUICK START - CHOOSE YOUR TASK
# ============================================================================

"""
I want to...                           Then run...
────────────────────────────────────────────────────────────────────────────
✓ Use the interactive form             python3 tax_form.py
✓ See form examples with real data     python3 form_demo.py
✓ Learn how to use the code            python3 examples.py
✓ See default example                  python3 object_model.py
✓ Add a new tax year                   Edit tax_brackets.py
✓ Understand the domain model          Read object_model.py
✓ Learn API syntax                     Read QUICK_REFERENCE.md
✓ Understand tax calculations          Read README.md
✓ Maintain tax rates                   Read CONFIGURATION_GUIDE.md
"""


# ============================================================================
# FILE DESCRIPTIONS
# ============================================================================

"""
┌─ CORE DOMAIN MODEL ────────────────────────────────────────────────────────┐
│                                                                             │
│ object_model.py (19 KB)                                                    │
│ ──────────────────────                                                     │
│ Main domain model with:                                                    │
│  • Core classes: Person, Household, IncomeSource, Asset, etc.            │
│  • Enums: ResidencyStatus, IncomeSourceType, AssetType, etc.             │
│  • TaxBracket class with progressive tax calculation                       │
│  • TaxYearConfig for flexible tax year configuration                       │
│  • Calculation methods: compute_box1_tax(), compute_box3_tax(), etc.      │
│  • Full docstrings and type hints                                         │
│  • Example at bottom showing complete household calculation                │
│                                                                             │
│ Key Classes:                                                               │
│  - Person: Individual with income, assets, deductions, credits            │
│  - Household: Multiple persons, joint Box3 allocation                     │
│  - TaxBracket: Progressive tax bracket definition                         │
│  - TaxYearConfig: Configuration for specific tax year                     │
│                                                                             │
│ Key Methods:                                                               │
│  - person.compute_taxable_income()                                        │
│  - person.compute_box1_tax(brackets)                                      │
│  - person.compute_net_tax_liability(brackets)                             │
│  - household.compute_box3_tax(rate)                                       │
│  - household.allocate_box3_between_partners(strategy)                     │
│  - household.compute_total_tax(brackets, rate, strategy)                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ TAX CONFIGURATION ────────────────────────────────────────────────────────┐
│                                                                             │
│ tax_brackets.py (7.1 KB)                                                  │
│ ────────────────────────                                                  │
│ Separate tax rate configuration file with:                                │
│  • Realistic Dutch tax rates for 2023, 2024, 2025                         │
│  • create_XXXX_brackets() functions for each year                         │
│  • TAX_CONFIG_XXXX instances for each year                                │
│  • TAX_CONFIGS registry for easy access                                   │
│  • get_tax_config(year) to retrieve specific year                         │
│  • get_latest_tax_config() to get current year                            │
│  • Detailed comments about Dutch tax system                               │
│                                                                             │
│ Tax Years Available:                                                       │
│  - 2023: General tax credit €2,713                                        │
│  - 2024: General tax credit €2,813                                        │
│  - 2025: General tax credit €2,917                                        │
│                                                                             │
│ Box1 Brackets (4 brackets with progressive rates)                         │
│ Box3 Rate (36% on assets)                                                 │
│                                                                             │
│ Easy to maintain: Just add new year functions and register them           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ INTERACTIVE FORM ─────────────────────────────────────────────────────────┐
│                                                                             │
│ tax_form.py (12 KB)                                                       │
│ ──────────────                                                             │
│ User-friendly interactive command-line form that guides through:          │
│  • Creating household members                                             │
│  • Entering income sources (employment, self-employment, rental, etc.)   │
│  • Adding deductions (mortgage, professional expenses, etc.)              │
│  • Recording assets (savings, stocks, bonds, real estate, crypto, etc.)  │
│  • Setting withheld tax amounts                                          │
│  • Calculating and displaying total tax liability                        │
│                                                                             │
│ Features:                                                                  │
│  • Input validation and error handling                                    │
│  • Formatted output with sections and headers                             │
│  • Automatic general tax credit application                               │
│  • Box3 allocation options (equal/proportional)                          │
│  • Results per member and household summary                              │
│                                                                             │
│ Run it:                                                                    │
│  $ python3 tax_form.py                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ FORM DEMONSTRATIONS ──────────────────────────────────────────────────────┐
│                                                                             │
│ form_demo.py (13 KB)                                                      │
│ ────────────────────                                                      │
│ Three realistic pre-populated demonstrations:                             │
│                                                                             │
│  1. Simple Single-Person Form                                             │
│     - Employee with one income source                                     │
│     - Single deduction                                                    │
│     - Assets and complete tax calculation                                │
│                                                                             │
│  2. Household Tax Form with Box3                                          │
│     - Two spouses with different income sources                          │
│     - Multiple deductions per person                                     │
│     - Household assets                                                   │
│     - Box3 allocation (equal vs proportional)                           │
│     - Combined household tax liability                                  │
│                                                                             │
│  3. Self-Employed Person Form                                             │
│     - Self-employment income                                             │
│     - Multiple business deductions                                       │
│     - Quarterly tax payments (withheld)                                 │
│     - Effective tax rate calculation                                    │
│                                                                             │
│ Use for:                                                                   │
│  • Understanding the form workflow                                        │
│  • Learning how to structure data                                         │
│  • Testing complex scenarios                                              │
│                                                                             │
│ Run it:                                                                    │
│  $ python3 form_demo.py                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ USAGE EXAMPLES ──────────────────────────────────────────────────────────┐
│                                                                             │
│ examples.py (11 KB)                                                       │
│ ───────────────────                                                       │
│ Six detailed usage examples with explanations:                            │
│                                                                             │
│  1. Latest Tax Configuration                                              │
│     - Get current year config                                             │
│     - Calculate tax for single person                                     │
│                                                                             │
│  2. Specific Tax Year (2024)                                              │
│     - Compare rates across years                                          │
│     - Access specific year configuration                                  │
│                                                                             │
│  3. Tax Liability Comparison                                              │
│     - Same income/deductions across multiple years                        │
│     - See how rates and credits change                                    │
│                                                                             │
│  4. Household Box3 Tax Allocation                                         │
│     - Equal allocation strategy                                           │
│     - Proportional allocation strategy (by wealth)                       │
│                                                                             │
│  5. Available Tax Years                                                   │
│     - List all configured years                                          │
│     - Show details for each year                                         │
│                                                                             │
│  6. Edge Cases                                                             │
│     - Zero income                                                         │
│     - Very high income                                                    │
│     - Withheld tax refund scenario                                       │
│                                                                             │
│ Run it:                                                                    │
│  $ python3 examples.py                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
"""


# ============================================================================
# DOCUMENTATION FILES
# ============================================================================

"""
┌─ README.md ────────────────────────────────────────────────────────────────┐
│ Complete project documentation with:                                      │
│  • Features overview                                                      │
│  • Quick start guide                                                      │
│  • Usage examples (code samples)                                          │
│  • Tax year rates tables                                                  │
│  • Domain model class reference                                           │
│  • How to add new tax years                                              │
│  • Design principles                                                      │
│  • References and sources                                                 │
│                                                                             │
│ Start here if you're new to the project!                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ CONFIGURATION_GUIDE.md ──────────────────────────────────────────────────┐
│ Guide for maintaining tax bracket configurations:                         │
│  • File structure explanation                                             │
│  • Realistic rates explanation                                            │
│  • Step-by-step: How to add a new tax year                              │
│  • How to use tax configurations                                          │
│  • Dutch tax authority references                                         │
│  • Annual maintenance checklist                                           │
│  • Notes on realistic rates                                              │
│                                                                             │
│ Read this when updating for new tax year!                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ QUICK_REFERENCE.md ──────────────────────────────────────────────────────┐
│ Cheat sheet for common operations:                                        │
│  • 14 quick recipes/examples                                              │
│  • Common patterns and usage                                              │
│  • Common queries (Q&A format)                                            │
│  • Validation & error handling                                            │
│  • Tips & tricks                                                          │
│  • How to run each file                                                  │
│                                                                             │
│ Keep this open while coding!                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ PROJECT_INDEX.md (this file) ────────────────────────────────────────────┐
│ Navigation guide for the entire project                                   │
│  • File descriptions                                                      │
│  • Quick start checklist                                                  │
│  • API reference                                                          │
│  • Common tasks guide                                                     │
│                                                                             │
│ Use this to find what you need!                                          │
└─────────────────────────────────────────────────────────────────────────────┘
"""


# ============================================================================
# GETTING STARTED CHECKLIST
# ============================================================================

"""
BEGINNER CHECKLIST:

[ ] 1. Read README.md to understand the project
[ ] 2. Run: python3 object_model.py
     - See a complete household tax calculation
[ ] 3. Run: python3 form_demo.py
     - See 3 realistic scenarios
[ ] 4. Run: python3 examples.py
     - See 6 different usage patterns
[ ] 5. Read QUICK_REFERENCE.md
     - Understand common API usage
[ ] 6. Try: python3 tax_form.py
     - Use the interactive form

DEVELOPER CHECKLIST:

[ ] 1. Read object_model.py completely
     - Understand all domain classes
     - Review all calculation methods
[ ] 2. Review tax_brackets.py
     - See how configurations work
[ ] 3. Study examples.py
     - Understand various use cases
[ ] 4. Create your own person/household
     - Test calculations
[ ] 5. Try adding a new tax year
     - Follow CONFIGURATION_GUIDE.md
[ ] 6. Plan unit tests
     - Use patterns from examples.py
"""


# ============================================================================
# API QUICK REFERENCE
# ============================================================================

"""
CREATING ENTITIES:

Person(name, bsn, residency_status=RESIDENT)
  Add: income_sources, assets, deductions, tax_credits
  Method: add via .append() to lists

Household(household_id)
  Add members: .add_member(person)
  Remove: .remove_member(bsn)

IncomeSource(name, source_type, gross_amount, description="")
IncomeSourceType: EMPLOYMENT, SELF_EMPLOYMENT, RENTAL, PENSION, INVESTMENT, OTHER

Asset(name, asset_type, value, description="")
AssetType: SAVINGS, STOCKS, BONDS, REAL_ESTATE, CRYPTO, OTHER

Deduction(name, amount, deduction_type, description="")

TaxCredit(name, amount, description="")

TaxBracket(lower_bound, upper_bound, rate, description="")

TaxYearConfig(year, box1_brackets, box3_rate, general_tax_credit, description="")


CALCULATIONS:

person.compute_taxable_income() -> Decimal
person.compute_box1_tax(brackets) -> Decimal
person.compute_net_tax_liability(brackets) -> Decimal
person.total_gross_income() -> Decimal
person.total_asset_value() -> Decimal
person.total_deductions() -> Decimal
person.total_tax_credits() -> Decimal

household.compute_box3_tax(tax_rate) -> Decimal
household.allocate_box3_between_partners(rate, strategy, custom_allocation=None) -> Dict[str, Decimal]
household.compute_total_tax(brackets, box3_rate, box3_strategy) -> Dict[str, Decimal]
household.total_gross_income() -> Decimal
household.total_asset_value() -> Decimal


CONFIGURATION ACCESS:

get_latest_tax_config() -> TaxYearConfig
get_tax_config(year: int) -> TaxYearConfig
TAX_CONFIGS -> Dict[int, TaxYearConfig]


ENUMS:

ResidencyStatus: RESIDENT, NON_RESIDENT
IncomeSourceType: EMPLOYMENT, SELF_EMPLOYMENT, RENTAL, PENSION, INVESTMENT, OTHER
AssetType: SAVINGS, STOCKS, BONDS, REAL_ESTATE, CRYPTO, OTHER
AllocationStrategy: EQUAL, PROPORTIONAL, CUSTOM
"""


# ============================================================================
# COMMON TASKS GUIDE
# ============================================================================

"""
TASK 1: Calculate tax for single person
──────────────────────────────────────
1. Import: from object_model import Person, IncomeSource, TaxCredit
2. Import config: from tax_brackets import get_latest_tax_config
3. Create person with income_sources and tax_credits
4. Call: person.compute_net_tax_liability(config.box1_brackets)
See: examples.py (Example 1)


TASK 2: Calculate household Box3 tax
────────────────────────────────────
1. Create household and add members
2. Call: household.compute_box3_tax(config.box3_rate)
3. For allocation: household.allocate_box3_between_partners(rate, strategy)
See: form_demo.py (Demo 2)


TASK 3: Compare tax across years
────────────────────────────────
1. Loop: for year in TAX_CONFIGS.keys()
2. Get config: config = TAX_CONFIGS[year]
3. Create person with same data
4. Calculate: tax = person.compute_box1_tax(config.box1_brackets)
See: examples.py (Example 3)


TASK 4: Use the interactive form
────────────────────────────────
$ python3 tax_form.py
Follow prompts to enter household data
Results calculated automatically
See: tax_form.py


TASK 5: Add a new tax year (2026)
────────────────────────────────
1. Open: tax_brackets.py
2. Add: create_2026_brackets() function
3. Add: TAX_CONFIG_2026 instance
4. Register: TAX_CONFIGS[2026] = TAX_CONFIG_2026
5. Done! Use: get_tax_config(2026)
See: CONFIGURATION_GUIDE.md


TASK 6: Validate person/household data
──────────────────────────────────────
Uses @dataclass validation in __post_init__
Raises: ValueError with meaningful message
Catch with: try/except ValueError
Example: person = Person(name="", bsn="")  # Raises ValueError
See: QUICK_REFERENCE.md


TASK 7: Create unit tests
──────────────────────────
1. Use patterns from examples.py
2. Verify calculations with known values
3. Test edge cases (zero income, high income, etc.)
4. Test different allocation strategies
See: examples.py (Example 6)
"""


# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
PROBLEM: "ImportError: cannot import name X"
SOLUTION: Make sure you're in the correct directory with all .py files

PROBLEM: "ValueError: Income amount cannot be negative"
SOLUTION: Check that you're using Decimal() not negative numbers
EXAMPLE: Decimal("1000")  # Correct
         -Decimal("1000")  # Wrong

PROBLEM: Tax calculation seems wrong
SOLUTION: Make sure you're using config from tax_brackets.py
EXAMPLE: config = get_latest_tax_config()
         tax = person.compute_box1_tax(config.box1_brackets)

PROBLEM: Box3 allocation not working
SOLUTION: Check that household has members
SOLUTION: Make sure you're using correct AllocationStrategy enum

PROBLEM: "tax_year not configured"
SOLUTION: Only 2023, 2024, 2025 are configured
SOLUTION: Add new year to tax_brackets.py following CONFIGURATION_GUIDE.md

PROBLEM: Form input validation failing
SOLUTION: Follow input type prompts (Decimal for money, int for counts)
SOLUTION: Check QUICK_REFERENCE.md for correct input format
"""


# ============================================================================
# TECHNICAL DETAILS
# ============================================================================

"""
TECHNOLOGY STACK:
  • Python 3.9+
  • Standard library only (no external dependencies)
  • dataclasses for clean domain models
  • Decimal for precise financial calculations
  • Enums for type-safe constants

DESIGN PATTERNS USED:
  • Domain-Driven Design: Clear separation of domain model
  • Value Objects: Decimal, Enums for type safety
  • Strategy Pattern: AllocationStrategy for flexible behavior
  • Repository Pattern: TAX_CONFIGS registry
  • Factory Pattern: create_YYYY_brackets() functions

KEY PRINCIPLES:
  ✓ Single Responsibility: Each class has one purpose
  ✓ Composition > Inheritance: Flexible composition of features
  ✓ Immutability: Dataclasses with default immutability
  ✓ Type Safety: Full type hints throughout
  ✓ Validation: Input validation in __post_init__
  ✓ No Side Effects: Pure calculation functions

PERFORMANCE:
  • All calculations O(n) where n = number of income sources/assets
  • Household calculations O(m*n) where m = members
  • Suitable for real-time calculations and forms

TESTING STRATEGY:
  • No mocking needed (no dependencies)
  • Test cases can be simple and focused
  • Use predefined configurations for reproducibility
  • Test edge cases: zero income, high income, etc.
"""


# ============================================================================
# NEXT STEPS
# ============================================================================

"""
FOR LEARNING:
  1. Start: README.md
  2. Run: python3 form_demo.py
  3. Study: QUICK_REFERENCE.md
  4. Code: Create your first person and calculate tax

FOR USING THE FORM:
  1. Run: python3 tax_form.py
  2. Follow interactive prompts
  3. Review calculated results

FOR EXTENDING:
  1. Add new tax year: Follow CONFIGURATION_GUIDE.md
  2. Create unit tests: Study examples.py patterns
  3. Build features: Use domain classes from object_model.py

FOR PRODUCTION USE:
  1. Review tax_brackets.py for current rates
  2. Verify calculations with official sources
  3. Test thoroughly with real data
  4. Consult tax professional for compliance
"""

if __name__ == "__main__":
    print(__doc__)
