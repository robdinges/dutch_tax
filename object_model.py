"""
Dutch Tax System Domain Model

A clean, extensible domain model for the Dutch income tax system.
Supports Box1 (income tax), Box3 (wealth tax), and flexible tax bracket configuration.

Design Principles:
- Single responsibility: entities hold data, services handle calculations
- Composition over inheritance: tax rules are composed, not inherited
- No framework dependencies: pure Python with standard library
- Extensible: easy to add new tax years and rules
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from abc import ABC, abstractmethod


# 2025 Eigenwoningforfait (Belastingdienst) parameters.
EIGENWONINGFORFAIT_THRESHOLDS = [0, 12_500, 25_000, 50_000, 75_000, 1_330_000]
EIGENWONINGFORFAIT_PERCENTS = [0.0, 0.0010, 0.0020, 0.0025, 0.0035]
EIGENWONINGFORFAIT_UPPER_BASE_FIXED = 4655
EIGENWONINGFORFAIT_UPPER_RATE = 0.0235

# Explicit 2025 aliases for clarity in multi-year extensions.
EIGENWONINGFORFAIT_THRESHOLDS_2025 = EIGENWONINGFORFAIT_THRESHOLDS
EIGENWONINGFORFAIT_PERCENTS_2025 = EIGENWONINGFORFAIT_PERCENTS
EIGENWONINGFORFAIT_UPPER_BASE_FIXED_2025 = EIGENWONINGFORFAIT_UPPER_BASE_FIXED
EIGENWONINGFORFAIT_UPPER_RATE_2025 = EIGENWONINGFORFAIT_UPPER_RATE


def calculate_eigenwoningforfait(woz_value: float, period_fraction: float = 1) -> float:
    """
    Calculate the 2025 eigenwoningforfait amount for Box1.

    Args:
        woz_value: WOZ value of the primary residence.
        period_fraction: Fraction of the year the home was owned (0.0 - 1.0).

    Returns:
        Eigenwoningforfait amount as float.
    """
    if woz_value < 0:
        raise ValueError("WOZ value cannot be negative")
    if period_fraction < 0 or period_fraction > 1:
        raise ValueError("period_fraction must be between 0.0 and 1.0")

    thresholds = EIGENWONINGFORFAIT_THRESHOLDS
    percents = EIGENWONINGFORFAIT_PERCENTS

    if woz_value <= thresholds[-1]:
        band_index = 0
        for index, lower_bound in enumerate(thresholds[:-1]):
            if woz_value >= lower_bound:
                band_index = index
            else:
                break
        forfait = woz_value * percents[band_index]
    else:
        forfait = (
            EIGENWONINGFORFAIT_UPPER_BASE_FIXED
            + EIGENWONINGFORFAIT_UPPER_RATE * (woz_value - thresholds[-1])
        )

    return forfait * period_fraction


# ============================================================================
# ENUMS
# ============================================================================

class ResidencyStatus(Enum):
    """Residency status for tax purposes."""
    RESIDENT = auto()
    NON_RESIDENT = auto()


class AllocationStrategy(Enum):
    """Strategy for allocating Box3 tax burden between household members."""
    EQUAL = auto()  # Each person pays equal share
    PROPORTIONAL = auto()  # Allocation based on wealth ratio
    CUSTOM = auto()  # Custom allocation per person


class IncomeSourceType(Enum):
    """Types of income sources."""
    EMPLOYMENT = auto()
    SELF_EMPLOYMENT = auto()
    RENTAL = auto()
    PENSION = auto()
    INVESTMENT = auto()
    OTHER = auto()


class AssetType(Enum):
    """Types of assets for Box3 wealth tax."""
    SAVINGS = auto()
    STOCKS = auto()
    BONDS = auto()
    REAL_ESTATE = auto()
    CRYPTO = auto()
    OTHER = auto()


# ============================================================================
# DATA CLASSES - Core Domain
# ============================================================================

@dataclass
class IncomeSource:
    """Represents a source of income."""
    name: str
    source_type: IncomeSourceType
    gross_amount: Decimal
    description: str = ""
    
    def __post_init__(self):
        if self.gross_amount < 0:
            raise ValueError("Income amount cannot be negative")


@dataclass
class Asset:
    """Represents an asset for wealth tax purposes."""
    name: str
    asset_type: AssetType
    value: Decimal
    description: str = ""
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Asset value cannot be negative")


@dataclass
class Deduction:
    """Represents a tax deduction."""
    name: str
    amount: Decimal
    deduction_type: str  # e.g., "personal", "professional", "charitable"
    description: str = ""
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Deduction amount cannot be negative")


@dataclass
class TaxCredit:
    """Represents a tax credit (reduces tax liability)."""
    name: str
    amount: Decimal
    description: str = ""
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Tax credit amount cannot be negative")


@dataclass
class OwnHome:
    """Represents a primary residence for eigenwoningforfait purposes."""
    woz_value: float
    period_fraction: float = 1.0

    def __post_init__(self):
        if self.woz_value < 0:
            raise ValueError("WOZ value cannot be negative")
        if self.period_fraction < 0 or self.period_fraction > 1:
            raise ValueError("period_fraction must be between 0.0 and 1.0")


@dataclass
class TaxBracket:
    """Represents a tax bracket for progressive taxation."""
    lower_bound: Decimal  # Income threshold where this bracket starts
    upper_bound: Optional[Decimal]  # None means no upper limit
    rate: Decimal  # Tax rate as decimal (e.g., 0.19 for 19%)
    description: str = ""  # e.g., "First bracket (19.06%)"
    
    def __post_init__(self):
        if self.lower_bound < 0:
            raise ValueError("Lower bound cannot be negative")
        if self.rate < 0 or self.rate > 1:
            raise ValueError("Tax rate must be between 0 and 1")
        if self.upper_bound is not None and self.upper_bound < self.lower_bound:
            raise ValueError("Upper bound must be greater than lower bound")
    
    def applies_to(self, income: Decimal) -> bool:
        """Check if this bracket applies to the given income."""
        if income < self.lower_bound:
            return False
        if self.upper_bound is not None and income > self.upper_bound:
            return False
        return True
    
    def taxable_amount(self, income: Decimal) -> Decimal:
        """Calculate the amount of income subject to this bracket."""
        if income <= self.lower_bound:
            return Decimal(0)
        
        lower = self.lower_bound
        if self.upper_bound is not None:
            upper = min(income, self.upper_bound)
        else:
            upper = income
        
        return max(Decimal(0), upper - lower)


@dataclass
class Person:
    """Represents a person in the tax system."""
    name: str
    bsn: str  # Dutch citizen service number (burgerservicenummer)
    residency_status: ResidencyStatus = ResidencyStatus.RESIDENT
    income_sources: List[IncomeSource] = field(default_factory=list)
    assets: List[Asset] = field(default_factory=list)
    deductions: List[Deduction] = field(default_factory=list)
    tax_credits: List[TaxCredit] = field(default_factory=list)
    own_home: Optional[OwnHome] = None
    withheld_tax: Decimal = Decimal(0)
    
    def __post_init__(self):
        if not self.name or not self.bsn:
            raise ValueError("Name and BSN are required")
        if self.withheld_tax < 0:
            raise ValueError("Withheld tax cannot be negative")
    
    # ========================================================================
    # Income Calculations
    # ========================================================================
    
    def total_gross_income(self) -> Decimal:
        """Calculate total gross income from all sources."""
        return sum((source.gross_amount for source in self.income_sources), Decimal(0))
    
    def total_asset_value(self) -> Decimal:
        """Calculate total asset value."""
        return sum((asset.value for asset in self.assets), Decimal(0))
    
    def total_deductions(self) -> Decimal:
        """Calculate total deductions."""
        return sum((deduction.amount for deduction in self.deductions), Decimal(0))
    
    def total_tax_credits(self) -> Decimal:
        """Calculate total tax credits."""
        return sum((credit.amount for credit in self.tax_credits), Decimal(0))
    
    def compute_taxable_income(self) -> Decimal:
        """
        Compute taxable income for Box1 (income tax).
        
        Formula: Gross Income + Eigenwoningforfait - Deductions = Taxable Income
        """
        gross = self.total_gross_income()
        eigenwoningforfait = Decimal(0)
        if self.own_home is not None:
            eigenwoningforfait = Decimal(
                str(
                    calculate_eigenwoningforfait(
                        self.own_home.woz_value,
                        self.own_home.period_fraction,
                    )
                )
            )
        deductions = self.total_deductions()
        taxable = max(Decimal(0), gross + eigenwoningforfait - deductions)
        return taxable
    
    def compute_box1_tax(self, brackets: List[TaxBracket]) -> Decimal:
        """
        Compute Box1 tax (income tax) using provided tax brackets.
        
        Args:
            brackets: List of tax brackets in ascending order by lower_bound
            
        Returns:
            Total tax before credits
        """
        taxable_income = self.compute_taxable_income()
        
        if taxable_income == 0:
            return Decimal(0)
        
        # Sort brackets to ensure correct order
        sorted_brackets = sorted(brackets, key=lambda b: b.lower_bound)
        
        total_tax = Decimal(0)
        for bracket in sorted_brackets:
            taxable_in_bracket = bracket.taxable_amount(taxable_income)
            if taxable_in_bracket > 0:
                total_tax += taxable_in_bracket * bracket.rate
        
        return total_tax
    
    def compute_withheld_tax(self) -> Decimal:
        """Return the amount of tax already withheld (e.g., employer withholding)."""
        return self.withheld_tax
    
    def compute_net_tax_liability(self, brackets: List[TaxBracket]) -> Decimal:
        """
        Compute net tax liability after credits and withheld tax.
        
        Formula: Box1 Tax - Tax Credits - Withheld Tax
        """
        box1_tax = self.compute_box1_tax(brackets)
        tax_after_credits = max(Decimal(0), box1_tax - self.total_tax_credits())
        net_liability = max(Decimal(0), tax_after_credits - self.withheld_tax)
        return net_liability


@dataclass
class Household:
    """
    Represents a household for tax purposes (may contain multiple persons).
    Handles joint taxation concepts like Box3 allocation.
    """
    household_id: str
    members: List[Person] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.household_id:
            raise ValueError("Household ID is required")
    
    # ========================================================================
    # Household Income and Assets
    # ========================================================================
    
    def total_gross_income(self) -> Decimal:
        """Calculate combined gross income of all members."""
        return sum((member.total_gross_income() for member in self.members), Decimal(0))
    
    def total_asset_value(self) -> Decimal:
        """Calculate combined asset value of all members."""
        return sum((member.total_asset_value() for member in self.members), Decimal(0))
    
    def add_member(self, person: Person) -> None:
        """Add a person to the household."""
        if any(m.bsn == person.bsn for m in self.members):
            raise ValueError(f"Person with BSN {person.bsn} already in household")
        self.members.append(person)
    
    def remove_member(self, bsn: str) -> None:
        """Remove a person from the household by BSN."""
        self.members = [m for m in self.members if m.bsn != bsn]
    
    # ========================================================================
    # Box3 Wealth Tax Calculations
    # ========================================================================
    
    def compute_box3_tax(self, tax_rate: Decimal) -> Decimal:
        """
        Compute total Box3 tax (wealth tax) for the household.
        
        Args:
            tax_rate: Tax rate for wealth tax as decimal (e.g., 0.32 for 32%)
            
        Returns:
            Total Box3 tax liability
        """
        total_wealth = self.total_asset_value()
        return total_wealth * tax_rate
    
    def allocate_box3_between_partners(
        self,
        tax_rate: Decimal,
        strategy: AllocationStrategy = AllocationStrategy.EQUAL,
        custom_allocation: Optional[Dict[str, Decimal]] = None
    ) -> Dict[str, Decimal]:
        """
        Allocate Box3 tax burden between household members.
        
        Args:
            tax_rate: Tax rate for wealth tax
            strategy: Allocation strategy to use
            custom_allocation: Optional custom allocation per BSN
            
        Returns:
            Dictionary mapping BSN to allocated tax amount
        """
        total_tax = self.compute_box3_tax(tax_rate)
        allocation = {}
        
        if strategy == AllocationStrategy.EQUAL:
            per_person = total_tax / len(self.members) if self.members else Decimal(0)
            for member in self.members:
                allocation[member.bsn] = per_person
        
        elif strategy == AllocationStrategy.PROPORTIONAL:
            total_wealth = self.total_asset_value()
            if total_wealth == 0:
                per_person = total_tax / len(self.members) if self.members else Decimal(0)
                for member in self.members:
                    allocation[member.bsn] = per_person
            else:
                for member in self.members:
                    wealth_ratio = member.total_asset_value() / total_wealth
                    allocation[member.bsn] = total_tax * wealth_ratio
        
        elif strategy == AllocationStrategy.CUSTOM:
            if not custom_allocation:
                raise ValueError("Custom allocation dictionary required for CUSTOM strategy")
            allocation = custom_allocation.copy()
        
        else:
            raise ValueError(f"Unknown allocation strategy: {strategy}")
        
        return allocation
    
    # ========================================================================
    # Combined Tax Calculations
    # ========================================================================
    
    def compute_total_tax(
        self,
        brackets: List[TaxBracket],
        box3_rate: Decimal,
        box3_strategy: AllocationStrategy = AllocationStrategy.EQUAL
    ) -> Dict[str, Decimal]:
        """
        Compute total tax liability for all household members.
        
        Returns:
            Dictionary mapping BSN to net tax liability (Box1 + Box3 share)
        """
        # Compute Box3 allocation
        box3_allocation = self.allocate_box3_between_partners(box3_rate, box3_strategy)
        
        result = {}
        for member in self.members:
            box1_tax = member.compute_net_tax_liability(brackets)
            box3_tax = box3_allocation.get(member.bsn, Decimal(0))
            total_tax = box1_tax + box3_tax
            result[member.bsn] = total_tax
        
        return result


# ============================================================================
# TAX YEAR CONFIGURATION
# ============================================================================

@dataclass
class TaxYearConfig:
    """Configuration for a specific tax year."""
    year: int
    box1_brackets: List[TaxBracket]
    box3_rate: Decimal
    general_tax_credit: Decimal  # Standard tax credit for residents
    description: str = ""


# ============================================================================
# NOTE: Tax configurations are now in tax_brackets.py for easier maintenance
# ============================================================================


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Import tax configuration from tax_brackets.py
    from tax_brackets import get_latest_tax_config
    
    # Create tax configuration for 2025
    tax_config = get_latest_tax_config()
    
    # Create household members
    john = Person(
        name="John Doe",
        bsn="123456789",
        residency_status=ResidencyStatus.RESIDENT,
        income_sources=[
            IncomeSource(
                name="Employment",
                source_type=IncomeSourceType.EMPLOYMENT,
                gross_amount=Decimal(60_000),
                description="Full-time employment"
            ),
            IncomeSource(
                name="Rental Income",
                source_type=IncomeSourceType.RENTAL,
                gross_amount=Decimal(12_000),
                description="Apartment rental"
            ),
        ],
        assets=[
            Asset(
                name="Savings Account",
                asset_type=AssetType.SAVINGS,
                value=Decimal(50_000),
                description="Regular savings"
            ),
            Asset(
                name="Stock Portfolio",
                asset_type=AssetType.STOCKS,
                value=Decimal(75_000),
                description="Diversified stocks"
            ),
        ],
        deductions=[
            Deduction(
                name="Mortgage Interest",
                amount=Decimal(8_000),
                deduction_type="professional"
            ),
            Deduction(
                name="Professional Expenses",
                amount=Decimal(2_500),
                deduction_type="professional"
            ),
        ],
        tax_credits=[
            TaxCredit(
                name="General Tax Credit",
                amount=tax_config.general_tax_credit,
                description="Standard resident tax credit"
            ),
        ],
        withheld_tax=Decimal(15_000)
    )
    
    jane = Person(
        name="Jane Doe",
        bsn="987654321",
        residency_status=ResidencyStatus.RESIDENT,
        income_sources=[
            IncomeSource(
                name="Employment",
                source_type=IncomeSourceType.EMPLOYMENT,
                gross_amount=Decimal(65_000),
                description="Full-time employment"
            ),
        ],
        assets=[
            Asset(
                name="Savings Account",
                asset_type=AssetType.SAVINGS,
                value=Decimal(40_000),
                description="Joint savings"
            ),
        ],
        deductions=[
            Deduction(
                name="Professional Expenses",
                amount=Decimal(3_000),
                deduction_type="professional"
            ),
        ],
        tax_credits=[
            TaxCredit(
                name="General Tax Credit",
                amount=tax_config.general_tax_credit,
                description="Standard resident tax credit"
            ),
        ],
        withheld_tax=Decimal(18_000)
    )
    
    # Create household
    household = Household(household_id="HH001")
    household.add_member(john)
    household.add_member(jane)
    
    # ========================================================================
    # CALCULATIONS
    # ========================================================================
    
    print("=" * 70)
    print("DUTCH TAX SYSTEM - DOMAIN MODEL EXAMPLE")
    print(f"Tax Year: {tax_config.year}")
    print("=" * 70)
    print()
    
    # Individual calculations
    for member in household.members:
        print(f"Member: {member.name} (BSN: {member.bsn})")
        print("-" * 70)
        print(f"  Total Gross Income:      € {member.total_gross_income():,.2f}")
        print(f"  Total Deductions:        € {member.total_deductions():,.2f}")
        print(f"  Taxable Income (Box1):   € {member.compute_taxable_income():,.2f}")
        print(f"  Box1 Tax (before credits): € {member.compute_box1_tax(tax_config.box1_brackets):,.2f}")
        print(f"  Tax Credits:             € {member.total_tax_credits():,.2f}")
        print(f"  Withheld Tax:            € {member.compute_withheld_tax():,.2f}")
        print(f"  Net Tax Liability:       € {member.compute_net_tax_liability(tax_config.box1_brackets):,.2f}")
        print()
        print(f"  Assets Value:            € {member.total_asset_value():,.2f}")
        print()
    
    # Household calculations
    print("=" * 70)
    print("HOUSEHOLD SUMMARY")
    print("=" * 70)
    print()
    print(f"Total Household Income:    € {household.total_gross_income():,.2f}")
    print(f"Total Household Assets:    € {household.total_asset_value():,.2f}")
    print()
    
    # Box3 allocation (equal strategy)
    print("Box3 Tax Allocation (Equal Strategy):")
    box3_equal = household.allocate_box3_between_partners(
        tax_config.box3_rate,
        AllocationStrategy.EQUAL
    )
    total_box3 = household.compute_box3_tax(tax_config.box3_rate)
    print(f"  Total Box3 Tax:          € {total_box3:,.2f}")
    for bsn, tax in box3_equal.items():
        member = next(m for m in household.members if m.bsn == bsn)
        print(f"  {member.name}: € {tax:,.2f}")
    print()
    
    # Box3 allocation (proportional strategy)
    print("Box3 Tax Allocation (Proportional Strategy):")
    box3_proportional = household.allocate_box3_between_partners(
        tax_config.box3_rate,
        AllocationStrategy.PROPORTIONAL
    )
    for bsn, tax in box3_proportional.items():
        member = next(m for m in household.members if m.bsn == bsn)
        print(f"  {member.name}: € {tax:,.2f}")
    print()
    
    # Total tax liability
    print("=" * 70)
    print("TOTAL TAX LIABILITY")
    print("=" * 70)
    print()
    total_tax = household.compute_total_tax(
        tax_config.box1_brackets,
        tax_config.box3_rate,
        AllocationStrategy.EQUAL
    )
    for bsn, tax in total_tax.items():
        member = next(m for m in household.members if m.bsn == bsn)
        print(f"{member.name}: € {tax:,.2f}")
    print()
    print(f"Total Household Tax:       € {sum(total_tax.values()):,.2f}")
    print()
