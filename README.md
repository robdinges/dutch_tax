# Dutch Tax System - Interactive Tax Calculator

A production-ready Python domain model and interactive form for the Dutch tax system (Box1 income tax and Box3 wealth tax).

## Features

✅ **Clean Domain Model** - Pure Python dataclasses with type hints  
✅ **Realistic Tax Rates** - 2023-2025 Dutch tax brackets from Belastingdienst  
✅ **Interactive Tax Form** - User-friendly command-line form  
✅ **Multiple Income Sources** - Support for employment, self-employment, rental, pension, etc.  
✅ **Eigenwoningforfait 2025** - Automatic Box1 addition for owner-occupied homes (WOZ-based)  
✅ **JSON Input Logging** - Web API stores one JSON file per `household_id` in `submissions/`  
✅ **Box3 Deemed Return Model** - Savings/investments split with tax-free-assets correction  
✅ **End Settlement** - Offsets tax with withheld wage tax, dividend tax, and heffingskortingen  
✅ **Comprehensive Examples** - Demos for different scenarios  
✅ **Easy to Extend** - Add new tax years with minimal code  
✅ **No Dependencies** - Pure Python, standard library only  

## Files Structure

```
object_model.py          # Core domain model (Person, Household, TaxBracket, etc.)
tax_brackets.py          # Tax configurations for 2023-2025
tax_form.py              # Interactive command-line form
form_demo.py             # Pre-populated form demonstrations
examples.py              # Usage examples for all features
test_eigenwoningforfait.py  # Unit and integration tests for eigenwoningforfait
test_box3_deemed_return.py  # Box3 savings/investments deemed return tests
test_income_tax_approach.py # Combined Box1/Box3 and settlement flow tests
CONFIGURATION_GUIDE.md   # How to maintain and update tax rates
FUNCTIONEEL_EN_OBJECTMODEL_PYTHON_NL.md  # Functioneel ontwerp en objectmodel (Python)
```

## Quick Start

### 1. Run the Interactive Form

```bash
python3 tax_form.py
```

Voor de webinterface (`python3 app.py`) kun je ook eerder opgeslagen invoer opnieuw laden:
1. Kies een JSON-bestand uit `submissions/` bij **Load Saved Input (JSON)**.
2. Klik op **Load JSON Into Form** om het formulier automatisch te vullen.

De web-GUI volgt nu de procesflow in 3 tabs:
1. `Huishouden`
2. `Personen`
3. `Importeren & Berekenen`

En toont in de resultaten expliciet:
- Box1 belastbaar inkomen
- Box3 fictief rendement en correctie met heffingsvrij vermogen
- verzamelinkomen
- voorheffingen en heffingskortingen
- eindafrekening (te betalen/te ontvangen)

This launches an interactive form that guides you through:
- Creating household members
- Entering income sources
- Adding deductions
- Recording assets
- Calculating total tax liability

### 2. View Form Demonstrations

```bash
python3 form_demo.py
```

Shows three realistic scenarios:
- **Simple single-person** tax calculation
- **Household with Box3** allocation strategies
- **Self-employed person** with business expenses

### 3. Run Usage Examples

```bash
python3 examples.py
```

Demonstrates:
- Latest tax configuration
- Year-to-year comparison
- Household Box3 allocation
- Edge cases and validation

### 4. Run Default Example

```bash
python3 object_model.py
```

Shows a household of two earners with full tax calculation.

## Usage Examples

### Basic Tax Calculation

```python
from decimal import Decimal
from object_model import Person, IncomeSource, IncomeSourceType, ResidencyStatus
from tax_brackets import get_latest_tax_config

# Get current tax configuration
config = get_latest_tax_config()

# Create a person
person = Person(
    name="Alice Smith",
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

# Calculate taxes
taxable_income = person.compute_taxable_income()
box1_tax = person.compute_box1_tax(config.box1_brackets)
net_tax = person.compute_net_tax_liability(config.box1_brackets)

print(f"Taxable: € {taxable_income:,.2f}")
print(f"Tax: € {net_tax:,.2f}")
```

### Household with Box3

```python
from object_model import Household, AllocationStrategy

# Create household with two members
household = Household(household_id="HH001")
household.add_member(person1)
household.add_member(person2)

# Calculate total tax with Box3 allocation
total_tax = household.compute_total_tax(
    config.box1_brackets,
    config.box3_rate,
    AllocationStrategy.PROPORTIONAL  # Based on deemed return ratio
)
```

### Access Tax Year Configurations

```python
from tax_brackets import get_tax_config, get_latest_tax_config, TAX_CONFIGS

# Get latest (2025)
config = get_latest_tax_config()

# Get specific year
config_2024 = get_tax_config(2024)

# List all years
for year in sorted(TAX_CONFIGS.keys()):
    config = TAX_CONFIGS[year]
    print(f"{year}: {config.description}")
```

## Tax Year Rates (2025)

### Box1 (Income Tax) - Progressive Brackets

| Range | Rate |
|-------|------|
| € 0 - € 37,895 | 19.06% |
| € 37,895 - € 75,790 | 28.43% |
| € 75,790 - € 1,011,724 | 37.05% |
| € 1,011,724+ | 49.49% |

### Box3 (Wealth Tax)

- Rate: **36%** on deemed return of assets
- Applies to: Savings, stocks, bonds, real estate, crypto, etc.

### Tax Credits & Deductions

- **General Tax Credit**: € 2,917 (2025)
- **Deductible**: Mortgage interest, professional expenses, charitable donations
- **Withheld Tax**: Employer/bank withholding reconciled at year-end

## Domain Model Classes

### Core Entities

- **Person**: Individual with income, assets, deductions, credits
- **Household**: Multiple persons, joint Box3 allocation
- **IncomeSource**: Employment, self-employment, rental, pension, investment
- **Asset**: Savings, stocks, bonds, real estate, crypto
- **Deduction**: Tax deductible expenses
- **TaxCredit**: Tax credits (reduces tax liability)
- **TaxBracket**: Progressive tax bracket definition
- **OwnHome**: Primary residence data used for eigenwoningforfait in Box1
- **TaxYearConfig**: Complete tax configuration for a year

### Enums

- **ResidencyStatus**: RESIDENT, NON_RESIDENT
- **IncomeSourceType**: EMPLOYMENT, SELF_EMPLOYMENT, RENTAL, PENSION, INVESTMENT, OTHER
- **AssetType**: SAVINGS, STOCKS, BONDS, REAL_ESTATE, CRYPTO, OTHER
- **AllocationStrategy**: EQUAL, PROPORTIONAL, CUSTOM

## Tax Calculations

### Box1 (Income Tax)

```
Taxable Income = Gross Income - Deductions
Box1 Tax = Sum of (income in bracket × bracket rate)
Tax After Credits = Box1 Tax - Tax Credits
Net Tax Liability = Tax After Credits - Withheld Tax
```

### Eigenwoningforfait (2025)

For owner-occupied homes (eigen woning), the model supports the 2025 Box1 addition:

- Thresholds: `[0, 12_500, 25_000, 50_000, 75_000, 1_330_000]`
- Percentages: `[0.0, 0.0010, 0.0020, 0.0025, 0.0035]`
- Above €1,330,000: `4,655 + 2.35% * (WOZ - 1,330,000)`
- Optional partial-year ownership via `period_fraction` (`0.0` to `1.0`)

Implementation is available through:
- `OwnHome` on `Person`
- `calculate_eigenwoningforfait(woz_value, period_fraction=1)`

In Box1, taxable income becomes:

```text
Taxable Income = Gross Income + Eigenwoningforfait - Deductions
```

### Box3 (Wealth Tax)

```
Deemed Return = (Savings × savings fictive return) + (Investments × investment fictive return)
Corrected Deemed Return = ((Total Assets - Tax-Free Assets) / Total Assets) × Deemed Return
Box3 Tax = Corrected Deemed Return × Tax Rate
```

For 2025 in this project:
- Box3 tax rate: `36%`
- Savings fictive return rate: `1.44%`
- Investment fictive return rate: `5.88%`
- Tax-free assets (single): `€57,000`
- Tax-free assets (fiscal partners): `€114,000`

Allocation strategies:
- **EQUAL**: Each person pays equal share
- **PROPORTIONAL**: Based on individual deemed return ratio
- **CUSTOM**: Manual allocation per person

### Verzamelinkomen And Final Settlement

```text
Verzamelinkomen = Box1 Taxable Income (Work & Home) + Corrected Box3 Deemed Return
Gross Income Tax = Box1 Tax + Box3 Tax
Net Settlement = Gross Income Tax - Heffingskortingen - Prepaid Taxes
Prepaid Taxes = Withheld Wage Tax + Paid Dividend Tax
```

## Adding a New Tax Year

1. Open `tax_brackets.py`
2. Add new bracket configuration function (copy previous year, update values)
3. Create new `TAX_CONFIG_XXXX` instance
4. Add to `TAX_CONFIGS` dictionary
5. Done! No changes to domain model needed

Example:

```python
def create_2026_brackets() -> list[TaxBracket]:
    """Create Box1 brackets for 2026."""
    return [
        TaxBracket(
            lower_bound=Decimal(0),
            upper_bound=Decimal(38_500),  # Updated
            rate=Decimal("0.1920"),  # Updated
            description="First bracket (19.20%)"
        ),
        # ... more brackets ...
    ]

TAX_CONFIG_2026 = TaxYearConfig(
    year=2026,
    box1_brackets=create_2026_brackets(),
    box3_rate=Decimal("0.3600"),
    box3_savings_return_rate=Decimal("0.0140"),
    box3_investment_return_rate=Decimal("0.0580"),
    box3_tax_free_assets_single=Decimal("58000"),
    box3_tax_free_assets_partner=Decimal("116000"),
    general_tax_credit=Decimal(3_000),  # Updated
    description="Dutch tax year 2026"
)

TAX_CONFIGS[2026] = TAX_CONFIG_2026
```

## Design Principles

✨ **Single Responsibility** - Each class has one clear purpose  
✨ **Composition over Inheritance** - Tax rules are composed, not inherited  
✨ **Separation of Concerns** - Data model separate from calculations  
✨ **Type Safety** - Full type hints for IDE support  
✨ **Extensibility** - Easy to add new years and features  
✨ **Testability** - Pure functions, no side effects  
✨ **Realistic** - Actual Dutch tax rates and rules  

## Testing

The codebase is structured for easy unit testing:

```python
def test_box1_calculation():
    config = get_tax_config(2025)
    person = Person(
        name="Test",
        bsn="000000000",
        income_sources=[
            IncomeSource(
                name="Test",
                source_type=IncomeSourceType.EMPLOYMENT,
                gross_amount=Decimal(50_000)
            )
        ]
    )
    tax = person.compute_box1_tax(config.box1_brackets)
    assert tax > 0
    assert tax < Decimal(50_000)  # Tax less than income
```

## References

- **Belastingdienst** (Dutch Tax Authority): https://www.belastingdienst.nl/
- **Tax Rates 2025**: https://www.belastingdienst.nl/inkomstenbelasting-1
- **Box3 Information**: https://www.belastingdienst.nl/box-3-inkomstenbelasting

## Requirements

- Python 3.9+
- No external dependencies (standard library only)

## License

This code is provided as-is for educational and reference purposes.

## Notes

- All rates are realistic but simplified for clarity
- Actual tax calculations may require professional tax advisor
- This tool is not a substitute for official tax filing
- Always verify with official Belastingdienst sources

---

Built with ❤️ for Dutch taxpayers
