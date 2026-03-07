"""
Dutch Tax Brackets and Rates Configuration

This module contains all tax year configurations with realistic Dutch tax rates.
Source: Belastingdienst (Dutch Tax Authority)
https://www.belastingdienst.nl/

Separation of concerns:
- Tax rates are defined here, not in the domain model
- Easy to update rates for new tax years
- Centralized configuration for maintenance
"""

from decimal import Decimal
from typing import Dict

# Import after ensuring object_model is available
# Avoid circular imports by importing at function level if needed
try:
    from object_model import TaxYearConfig, TaxBracket
except ImportError:
    # For testing tax_brackets.py standalone
    pass


# ============================================================================
# TAX YEAR 2025 - REALISTIC DUTCH RATES
# ============================================================================

def create_2025_brackets() -> list[TaxBracket]:
    """
    Create Box1 (income tax) brackets for 2025.
    
    Source: Belastingdienst 2025 rates
    Rates include both national income tax and employee social contributions.
    """
    return [
        TaxBracket(
            lower_bound=Decimal(0),
            upper_bound=Decimal(37_895),
            rate=Decimal("0.1906"),
            description="First bracket (19.06%)"
        ),
        TaxBracket(
            lower_bound=Decimal(37_895),
            upper_bound=Decimal(75_790),
            rate=Decimal("0.2843"),
            description="Second bracket (28.43%)"
        ),
        TaxBracket(
            lower_bound=Decimal(75_790),
            upper_bound=Decimal(1_011_724),
            rate=Decimal("0.3705"),
            description="Third bracket (37.05%)"
        ),
        TaxBracket(
            lower_bound=Decimal(1_011_724),
            upper_bound=None,
            rate=Decimal("0.4949"),
            description="Fourth bracket (49.49%)"
        ),
    ]


TAX_CONFIG_2025 = TaxYearConfig(
    year=2025,
    box1_brackets=create_2025_brackets(),
    box3_rate=Decimal("0.3600"),  # 36% wealth tax on assets
    general_tax_credit=Decimal(2_917),  # 2025 general tax credit
    description="Dutch tax year 2025 - Realistic rates"
)


# ============================================================================
# TAX YEAR 2024 - REALISTIC DUTCH RATES
# ============================================================================

def create_2024_brackets() -> list[TaxBracket]:
    """
    Create Box1 (income tax) brackets for 2024.
    
    Source: Belastingdienst 2024 rates
    """
    return [
        TaxBracket(
            lower_bound=Decimal(0),
            upper_bound=Decimal(37_150),
            rate=Decimal("0.1895"),
            description="First bracket (18.95%)"
        ),
        TaxBracket(
            lower_bound=Decimal(37_150),
            upper_bound=Decimal(74_301),
            rate=Decimal("0.2809"),
            description="Second bracket (28.09%)"
        ),
        TaxBracket(
            lower_bound=Decimal(74_301),
            upper_bound=Decimal(991_472),
            rate=Decimal("0.3635"),
            description="Third bracket (36.35%)"
        ),
        TaxBracket(
            lower_bound=Decimal(991_472),
            upper_bound=None,
            rate=Decimal("0.4950"),
            description="Fourth bracket (49.50%)"
        ),
    ]


TAX_CONFIG_2024 = TaxYearConfig(
    year=2024,
    box1_brackets=create_2024_brackets(),
    box3_rate=Decimal("0.3600"),  # 36% wealth tax on assets
    general_tax_credit=Decimal(2_813),  # 2024 general tax credit
    description="Dutch tax year 2024 - Realistic rates"
)


# ============================================================================
# TAX YEAR 2023 - REALISTIC DUTCH RATES
# ============================================================================

def create_2023_brackets() -> list[TaxBracket]:
    """
    Create Box1 (income tax) brackets for 2023.
    
    Source: Belastingdienst 2023 rates
    """
    return [
        TaxBracket(
            lower_bound=Decimal(0),
            upper_bound=Decimal(36_092),
            rate=Decimal("0.1893"),
            description="First bracket (18.93%)"
        ),
        TaxBracket(
            lower_bound=Decimal(36_092),
            upper_bound=Decimal(72_185),
            rate=Decimal("0.2809"),
            description="Second bracket (28.09%)"
        ),
        TaxBracket(
            lower_bound=Decimal(72_185),
            upper_bound=Decimal(962_500),
            rate=Decimal("0.3635"),
            description="Third bracket (36.35%)"
        ),
        TaxBracket(
            lower_bound=Decimal(962_500),
            upper_bound=None,
            rate=Decimal("0.4950"),
            description="Fourth bracket (49.50%)"
        ),
    ]


TAX_CONFIG_2023 = TaxYearConfig(
    year=2023,
    box1_brackets=create_2023_brackets(),
    box3_rate=Decimal("0.3600"),  # 36% wealth tax on assets
    general_tax_credit=Decimal(2_713),  # 2023 general tax credit
    description="Dutch tax year 2023 - Realistic rates"
)


# ============================================================================
# TAX REGISTRY - Access tax configs by year
# ============================================================================

TAX_CONFIGS: Dict[int, TaxYearConfig] = {
    2023: TAX_CONFIG_2023,
    2024: TAX_CONFIG_2024,
    2025: TAX_CONFIG_2025,
}


def get_tax_config(year: int) -> TaxYearConfig:
    """
    Get tax configuration for a specific year.
    
    Args:
        year: Tax year (e.g., 2025)
        
    Returns:
        TaxYearConfig for the specified year
        
    Raises:
        ValueError: If year is not found in configuration
    """
    if year not in TAX_CONFIGS:
        available = sorted(TAX_CONFIGS.keys())
        raise ValueError(
            f"Tax year {year} not configured. Available years: {available}"
        )
    return TAX_CONFIGS[year]


def get_latest_tax_config() -> TaxYearConfig:
    """Get the most recent tax year configuration."""
    latest_year = max(TAX_CONFIGS.keys())
    return TAX_CONFIGS[latest_year]


# ============================================================================
# DETAILED INFORMATION ABOUT DUTCH TAX BRACKETS
# ============================================================================

"""
DUTCH TAX SYSTEM OVERVIEW:

Box1 (Inkomstenbelasting - Income Tax):
  - Progressive tax on wages, salaries, and business income
  - Four tax brackets for residents
  - Rates include national income tax + employee social contributions
  
Box3 (Belasting op Vermogen - Wealth Tax):
  - Tax on assets/wealth above certain threshold
  - Standard rate: 36% of deemed return on assets
  - Applies to savings, investments, real estate, etc.
  
Key Concepts:
  - Taxable income = Gross income - Deductions
  - Progressive brackets: higher income taxed at higher rates
  - General tax credit: standard tax reduction for residents
  - Withheld tax: employer/bank already withholds provisional tax
  - Tax deductions: mortgage interest, professional expenses, etc.

2025 Changes:
  - Bracket thresholds indexed for inflation
  - General tax credit increased to €2,917
  - Box3 rate remains at 36%
  - Top marginal rate: 49.49% (on income above €1,011,724)
"""
