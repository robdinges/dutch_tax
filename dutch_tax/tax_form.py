"""
Interactive Tax Form - Dutch Tax System

A user-friendly, intuitive command-line form for entering tax information.
Features smart validation, helpful hints, and a clean, modern layout.
"""

from decimal import Decimal
from typing import Optional, List, Tuple
import sys
from dutch_tax.models import (
    Person, Household, IncomeSource, Asset, Deduction, TaxCredit,
    IncomeSourceType, AssetType, ResidencyStatus, AllocationStrategy
)
from dutch_tax.tax_brackets import get_tax_config, get_latest_tax_config


class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Colors
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    
    # Backgrounds
    BG_BLUE = '\033[104m'
    BG_GREEN = '\033[102m'


class TaxForm:
    """Interactive form for collecting tax information with smart validation."""
    
    def __init__(self, tax_year: Optional[int] = None):
        """Initialize the tax form with a specific tax year."""
        if tax_year:
            self.config = get_tax_config(tax_year)
        else:
            self.config = get_latest_tax_config()
        self.household = Household(household_id="FORM_001")
    
    @staticmethod
    def print_header(title: str):
        """Print a formatted, colorful header."""
        print(f"\n{Colors.BG_BLUE}{Colors.BOLD} {title:<68} {Colors.RESET}")
        print(f"{Colors.BLUE}{'─' * 70}{Colors.RESET}\n")
    
    @staticmethod
    def print_section(title: str):
        """Print a formatted section with emoji."""
        print(f"\n{Colors.CYAN}{Colors.BOLD}→ {title}{Colors.RESET}")
        print(f"{Colors.DIM}{'─' * 70}{Colors.RESET}")
    
    @staticmethod
    def print_success(message: str):
        """Print a success message."""
        print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")
    
    @staticmethod
    def print_error(message: str):
        """Print an error message."""
        print(f"{Colors.RED}✗ {message}{Colors.RESET}")
    
    @staticmethod
    def print_info(message: str):
        """Print an info message."""
        print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")
    
    @staticmethod
    def print_hint(message: str):
        """Print a hint message."""
        print(f"{Colors.DIM}  💡 Tip: {message}{Colors.RESET}")
    
    @staticmethod
    def get_input(prompt: str, required: bool = True, input_type=str, hint: str = "") -> any:
        """
        Get and validate user input with smart defaults and hints.
        
        Args:
            prompt: The question to ask
            required: Whether the field is mandatory
            input_type: Expected type (str, int, Decimal)
            hint: Helpful hint for the user
        """
        while True:
            try:
                # Display hint if provided
                if hint:
                    TaxForm.print_hint(hint)
                
                # Create prompt with type indicator
                type_indicator = ""
                if input_type == Decimal:
                    type_indicator = " (€)"
                elif input_type == int:
                    type_indicator = " (#)"
                
                default_text = "" if required else " [Enter to skip]"
                full_prompt = f"{prompt}{type_indicator}{default_text}: "
                
                value = input(f"{Colors.BOLD}{full_prompt}{Colors.RESET}").strip()
                
                # Handle empty input
                if not value:
                    if not required:
                        return None
                    else:
                        TaxForm.print_error("This field is required. Please try again.")
                        continue
                
                # Type conversion with validation
                if input_type == Decimal:
                    try:
                        decimal_val = Decimal(value)
                        if decimal_val < 0:
                            TaxForm.print_error("Amount cannot be negative. Please try again.")
                            continue
                        return decimal_val
                    except:
                        TaxForm.print_error(f"Invalid amount. Please use format: 1000 or 1000.50")
                        continue
                
                elif input_type == int:
                    try:
                        int_val = int(value)
                        if int_val < 0:
                            TaxForm.print_error("Number cannot be negative. Please try again.")
                            continue
                        return int_val
                    except:
                        TaxForm.print_error("Invalid number. Please use whole numbers only.")
                        continue
                
                else:
                    if not value.strip():
                        TaxForm.print_error("This field cannot be empty. Please try again.")
                        continue
                    return value
            
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e:
                TaxForm.print_error(f"Input error: {e}")
    
    @staticmethod
    def get_choice(prompt: str, options: dict) -> str:
        """
        Get user choice from predefined options.
        
        Args:
            prompt: Question to ask
            options: Dict of {key: display_name}
        
        Returns:
            The selected key
        """
        while True:
            print(f"\n{Colors.BOLD}{prompt}{Colors.RESET}")
            for key, name in options.items():
                print(f"  {Colors.CYAN}{key}{Colors.RESET}. {name}")
            
            choice = input(f"\n{Colors.BOLD}Your choice: {Colors.RESET}").strip()
            
            if choice in options:
                return choice
            else:
                TaxForm.print_error(f"Invalid choice. Please select from: {', '.join(options.keys())}")
    
    @staticmethod
    def confirm(prompt: str, default: bool = False) -> bool:
        """
        Ask for yes/no confirmation.
        
        Args:
            prompt: Question to ask
            default: Default value if user presses Enter
        
        Returns:
            Boolean confirmation
        """
        default_text = "[Y/n]" if default else "[y/N]"
        response = input(f"{Colors.BOLD}{prompt} {default_text}: {Colors.RESET}").strip().lower()
        
        if response == "":
            return default
        return response in ["y", "yes"]
    
    def add_person(self) -> Person:
        """Interactive form to add a new person to the household."""
        self.print_section("👤 Add Household Member")
        
        # Basic info
        name = self.get_input(
            "Full name",
            hint="e.g., John Smith or Maria Garcia"
        )
        
        bsn = self.get_input(
            "BSN (Dutch citizen number)",
            hint="9 digits, e.g., 123456789"
        )
        
        # Residency status
        residency = self.get_choice(
            "Residency status",
            {"1": "Resident (tax credit applies)", "2": "Non-resident (no credit)"}
        )
        residency_status = ResidencyStatus.RESIDENT if residency == "1" else ResidencyStatus.NON_RESIDENT
        
        # Create person
        person = Person(
            name=name,
            bsn=bsn,
            residency_status=residency_status
        )
        
        self.print_success(f"{name} added to household")
        
        # Income sources
        self.print_section(f"💰 Income Sources for {name}")
        if self.confirm("Add income source?", default=True):
            while True:
                income_name = self.get_input(
                    "Income source name",
                    hint="e.g., 'Salary', 'Freelance Income', 'Rental Income'"
                )
                amount = self.get_input(
                    "Gross amount per year",
                    input_type=Decimal,
                    hint="Annual gross income"
                )
                
                income_type = self.get_choice(
                    "Income type",
                    {
                        "1": "Employment (W-2/salary)",
                        "2": "Self-Employment (business)",
                        "3": "Rental (property income)",
                        "4": "Pension (retirement)",
                        "5": "Investment (dividends, interest)",
                        "6": "Other"
                    }
                )
                
                income_types = {
                    "1": IncomeSourceType.EMPLOYMENT,
                    "2": IncomeSourceType.SELF_EMPLOYMENT,
                    "3": IncomeSourceType.RENTAL,
                    "4": IncomeSourceType.PENSION,
                    "5": IncomeSourceType.INVESTMENT,
                    "6": IncomeSourceType.OTHER,
                }
                
                person.income_sources.append(
                    IncomeSource(
                        name=income_name,
                        source_type=income_types.get(income_type),
                        gross_amount=amount
                    )
                )
                
                self.print_success(f"Income '{income_name}' added (€{amount:,.2f})")
                
                if not self.confirm("Add another income source?"):
                    break
        
        # Deductions
        self.print_section(f"📝 Deductions for {name}")
        if self.confirm("Add deductions?"):
            while True:
                deduction_name = self.get_input(
                    "Deduction name",
                    hint="e.g., 'Mortgage Interest', 'Professional Expenses'"
                )
                amount = self.get_input(
                    "Amount per year",
                    input_type=Decimal,
                    hint="Deductible expense amount"
                )
                
                person.deductions.append(
                    Deduction(
                        name=deduction_name,
                        amount=amount,
                        deduction_type="professional"
                    )
                )
                
                self.print_success(f"Deduction '{deduction_name}' added (€{amount:,.2f})")
                
                if not self.confirm("Add another deduction?"):
                    break
        
        # Assets
        self.print_section(f"🏦 Assets for {name}")
        if self.confirm("Add assets?"):
            while True:
                asset_name = self.get_input(
                    "Asset name",
                    hint="e.g., 'Savings Account', 'Stock Portfolio', 'Investment Real Estate'"
                )
                value = self.get_input(
                    "Current value",
                    input_type=Decimal,
                    hint="Total value of this asset"
                )
                
                asset_type = self.get_choice(
                    "Asset type",
                    {
                        "1": "Savings Account",
                        "2": "Stocks/Shares",
                        "3": "Bonds",
                        "4": "Real Estate",
                        "5": "Cryptocurrency",
                        "6": "Other"
                    }
                )
                
                asset_types = {
                    "1": AssetType.SAVINGS,
                    "2": AssetType.STOCKS,
                    "3": AssetType.BONDS,
                    "4": AssetType.REAL_ESTATE,
                    "5": AssetType.CRYPTO,
                    "6": AssetType.OTHER,
                }

                dividend_tax_paid = Decimal(0)
                selected_type = asset_types.get(asset_type)
                if selected_type != AssetType.SAVINGS and self.confirm("Dividendbelasting betaald op deze beleggingsrekening?", default=False):
                    dividend_tax_paid = self.get_input(
                        "Dividendbelasting bedrag",
                        required=False,
                        input_type=Decimal,
                        hint="Totaal van dividendbelasting op deze rekening"
                    ) or Decimal(0)
                
                person.assets.append(
                    Asset(
                        name=asset_name,
                        asset_type=selected_type,
                        value=value,
                        dividend_tax_paid=dividend_tax_paid,
                    )
                )
                
                self.print_success(f"Asset '{asset_name}' added (€{value:,.2f})")
                
                if not self.confirm("Add another asset?"):
                    break
        
        # Withheld tax
        self.print_section(f"💸 Tax Withholdings for {name}")
        if self.confirm("Has tax already been withheld?"):
            withheld = self.get_input(
                "Withheld tax amount",
                required=False,
                input_type=Decimal,
                hint="Employer withholding, bank withholding, or quarterly payments"
            ) or Decimal(0)
            person.withheld_tax = withheld
            self.print_success(f"Withheld tax: €{withheld:,.2f}")
        
        # Auto-add general tax credit
        if person.residency_status == ResidencyStatus.RESIDENT:
            person.tax_credits.append(
                TaxCredit(
                    name="General Tax Credit",
                    amount=self.config.general_tax_credit,
                    description="Standard resident tax credit"
                )
            )
            self.print_info(f"General tax credit applied (€{self.config.general_tax_credit:,.2f})")
        
        return person
    
    def collect_household_data(self) -> Household:
        """Collect data for all household members with welcome screen."""
        self.print_header(f"🇳🇱 DUTCH TAX CALCULATOR {self.config.year}")
        
        print(f"{Colors.CYAN}Welcome to the interactive Dutch tax calculator!{Colors.RESET}")
        print(f"This form will help you calculate your tax liability for {self.config.year}.\n")
        
        print(f"{Colors.DIM}Tax Year Information:{Colors.RESET}")
        print(f"  • General Tax Credit: €{self.config.general_tax_credit:,.2f}")
        print(f"  • Box3 Rate: {float(self.config.box3_rate) * 100}%")
        print(f"  • Tax Brackets: 4 progressive brackets\n")
        
        num_members = self.get_input(
            "How many people in the household?",
            input_type=int,
            hint="You can add 1 person (single) or multiple (couple/family)"
        )
        
        for i in range(num_members):
            print(f"\n{Colors.BG_GREEN}{Colors.BOLD} Household Member {i + 1} of {num_members} {Colors.RESET}")
            person = self.add_person()
            self.household.add_member(person)
        
        return self.household
    
    def calculate_and_display_results(self):
        """Calculate and display detailed tax results with visual formatting."""
        self.print_header("📊 TAX CALCULATION RESULTS")
        
        if not self.household.members:
            self.print_error("No household members to calculate tax for!")
            return
        
        # Individual results
        for member in self.household.members:
            self._display_member_results(member)
        
        # Household summary
        if len(self.household.members) > 1:
            self._display_household_summary()
        
        # Tax results
        self._display_tax_results()
    
    def _display_member_results(self, member: Person):
        """Display detailed results for a single member."""
        self.print_section(f"Member: {member.name}")
        
        gross = member.total_gross_income()
        deductions = member.total_deductions()
        taxable = member.compute_taxable_income()
        box1_tax = member.compute_box1_tax(self.config.box1_brackets)
        credits = member.total_tax_credits()
        withheld = member.compute_withheld_tax()
        dividend_tax_paid = member.total_dividend_tax_paid()
        prepaid_taxes = member.compute_prepaid_taxes()
        net_box1 = member.compute_net_tax_liability(self.config.box1_brackets)
        
        # Income breakdown
        print(f"\n{Colors.BOLD}Income:{Colors.RESET}")
        for source in member.income_sources:
            print(f"  • {source.name:<35} €{source.gross_amount:>12,.2f}")
        print(f"  {Colors.DIM}{'─' * 50}{Colors.RESET}")
        print(f"  {'Total Gross Income':<35} €{gross:>12,.2f}")
        
        # Deductions
        if member.deductions:
            print(f"\n{Colors.BOLD}Deductions:{Colors.RESET}")
            for deduction in member.deductions:
                print(f"  • {deduction.name:<33} €{deduction.amount:>12,.2f}")
            print(f"  {Colors.DIM}{'─' * 50}{Colors.RESET}")
            print(f"  {'Total Deductions':<35} €{deductions:>12,.2f}")
        
        # Tax calculation
        print(f"\n{Colors.BOLD}Box1 Tax Calculation:{Colors.RESET}")
        print(f"  {'Taxable Income':<35} €{taxable:>12,.2f}")
        for bracket in sorted(self.config.box1_brackets, key=lambda b: b.lower_bound):
            taxable_in_bracket = bracket.taxable_amount(taxable)
            if taxable_in_bracket > 0:
                tax_in_bracket = taxable_in_bracket * bracket.rate
                print(
                    f"  • {bracket.description:<31} "
                    f"€{taxable_in_bracket:>10,.2f} x {float(bracket.rate) * 100:>5.2f}% = €{tax_in_bracket:>10,.2f}"
                )
        print(f"  {'Tax (before credits)':<35} €{box1_tax:>12,.2f}")
        
        if credits > 0:
            print(f"  {'Tax Credits':<35} -€{credits:>11,.2f}")
            print(f"  {'Tax after credits':<35} €{max(Decimal(0), box1_tax - credits):>12,.2f}")
        
        if withheld > 0:
            print(f"  {'Withheld Tax':<35} -€{withheld:>11,.2f}")
        if dividend_tax_paid > 0:
            print(f"  {'Dividend Tax Paid (assets)':<35} -€{dividend_tax_paid:>11,.2f}")
        if prepaid_taxes > 0:
            print(f"  {'Total Prepaid Taxes':<35} -€{prepaid_taxes:>11,.2f}")
        
        print(f"  {Colors.DIM}{'─' * 50}{Colors.RESET}")
        if net_box1 > 0:
            print(f"  {Colors.RED}{Colors.BOLD}{'Net Tax Owed':<35} €{net_box1:>12,.2f}{Colors.RESET}")
        else:
            refund = withheld - (box1_tax - credits)
            if refund > 0:
                print(f"  {Colors.GREEN}{Colors.BOLD}{'Refund Due':<35} €{refund:>12,.2f}{Colors.RESET}")
            else:
                print(f"  {Colors.GREEN}{'No Tax Due':<35} €{0:>12,.2f}{Colors.RESET}")
        
        # Assets
        if member.assets:
            print(f"\n{Colors.BOLD}Assets (Box3):{Colors.RESET}")
            for asset in member.assets:
                print(f"  • {asset.name:<33} €{asset.value:>12,.2f}")
            print(f"  {Colors.DIM}{'─' * 50}{Colors.RESET}")
            print(f"  {'Total Assets':<35} €{member.total_asset_value():>12,.2f}")
    
    def _display_household_summary(self):
        """Display household summary."""
        self.print_section("Household Summary")
        
        total_income = self.household.total_gross_income()
        total_assets = self.household.total_asset_value()
        
        print(f"\n{Colors.BOLD}Combined Information:{Colors.RESET}")
        print(f"  {'Members':<35} {len(self.household.members)}")
        print(f"  {'Total Gross Income':<35} €{total_income:>12,.2f}")
        print(f"  {'Total Assets':<35} €{total_assets:>12,.2f}")
    
    def _display_tax_results(self):
        """Display final tax liability results."""
        self.print_section("Final Tax Calculation")

        tax_free_assets = (
            self.config.box3_tax_free_assets_partner
            if len(self.household.members) > 1
            else self.config.box3_tax_free_assets_single
        )
        total_assets = self.household.total_asset_value()
        corrected_assets = max(Decimal(0), total_assets - tax_free_assets)
        correction_factor = (corrected_assets / total_assets) if total_assets > 0 else Decimal(0)

        savings_assets = self.household.total_savings_assets()
        investment_assets = self.household.total_investment_assets()
        savings_deemed_return = savings_assets * self.config.box3_savings_return_rate
        investment_deemed_return = investment_assets * self.config.box3_investment_return_rate
        corrected_savings_deemed_return = savings_deemed_return * correction_factor
        corrected_investment_deemed_return = investment_deemed_return * correction_factor
        total_deemed_return = savings_deemed_return + investment_deemed_return
        corrected_deemed_return = corrected_savings_deemed_return + corrected_investment_deemed_return

        total_box3 = self.household.compute_box3_tax(
            self.config.box3_rate,
            self.config.box3_savings_return_rate,
            self.config.box3_investment_return_rate,
            tax_free_assets,
        )
        total_tax = self.household.compute_total_tax(
            self.config.box1_brackets,
            self.config.box3_rate,
            AllocationStrategy.EQUAL,
            box3_savings_return_rate=self.config.box3_savings_return_rate,
            box3_investment_return_rate=self.config.box3_investment_return_rate,
            box3_tax_free_assets=tax_free_assets,
        )
        
        print(f"\n{Colors.BOLD}Tax Breakdown:{Colors.RESET}")
        
        # Box1 per member
        for bsn, total in total_tax.items():
            member = next(m for m in self.household.members if m.bsn == bsn)
            box1 = member.compute_net_tax_liability(self.config.box1_brackets)
            box3_share = total - box1
            print(f"  {member.name:<35}")
            if box1 > 0:
                print(f"    Box1 (Income Tax): €{box1:>14,.2f}")
            if box3_share > 0:
                print(f"    Box3 (Wealth Tax): €{box3_share:>14,.2f}")
            print(f"    {Colors.BOLD}Subtotal{Colors.RESET}:       €{total:>14,.2f}\n")
        
        total_all = sum(total_tax.values())
        
        if total_box3 > 0:
            print(f"  {Colors.BOLD}Box3 Summary (Equal allocation):{Colors.RESET}")
            print(f"    Total Assets:                     €{total_assets:>14,.2f}")
            print(f"    Heffingsvrij vermogen:            €{tax_free_assets:>14,.2f}")
            print(f"    Gecorrigeerd vermogen:            €{corrected_assets:>14,.2f}")
            print(f"    Correctiefactor:                   {float(correction_factor) * 100:>13.2f}%")
            print(f"    Spaargeld:                        €{savings_assets:>14,.2f}")
            print(f"    Beleggingen:                      €{investment_assets:>14,.2f}")
            print(
                f"    Fictief rendement spaargeld "
                f"({float(self.config.box3_savings_return_rate) * 100:.2f}%): €{savings_deemed_return:>14,.2f}"
            )
            print(
                f"    Fictief rendement beleggingen "
                f"({float(self.config.box3_investment_return_rate) * 100:.2f}%): €{investment_deemed_return:>14,.2f}"
            )
            print(f"    Totaal fictief rendement:         €{total_deemed_return:>14,.2f}")
            print(
                f"    Gecorrigeerd fictief rendement "
                f"((gecorrigeerd_vermogen/totaal_vermogen)*fictief_rendement): €{corrected_deemed_return:>14,.2f}"
            )
            print(f"    Box3 belasting ({float(self.config.box3_rate) * 100:.2f}%):      €{total_box3:>14,.2f}\n")
        
        print(f"  {Colors.DIM}{'─' * 50}{Colors.RESET}")
        
        if total_all > 0:
            print(f"  {Colors.RED}{Colors.BOLD}{'TOTAL TAX DUE':<35} €{total_all:>12,.2f}{Colors.RESET}\n")
        else:
            print(f"  {Colors.GREEN}{Colors.BOLD}{'NO TAX DUE':<35} €{0:>12,.2f}{Colors.RESET}\n")
        
        # Effective tax rate
        total_income = self.household.total_gross_income()
        if total_income > 0:
            effective_rate = (total_all / total_income) * 100
            print(f"  Effective Tax Rate: {effective_rate:.2f}%")


def main():
    """Main function to run the interactive tax form."""
    try:
        # Initialize form with latest tax year
        form = TaxForm()
        
        # Collect household data
        form.collect_household_data()
        
        # Calculate and display results
        print("\n" + "=" * 70)
        input(f"{Colors.BOLD}Press Enter to calculate your taxes...{Colors.RESET}")
        print("=" * 70)
        
        form.calculate_and_display_results()
        
        # Closing message
        print(f"\n{Colors.BLUE}{'─' * 70}{Colors.RESET}")
        print(f"{Colors.GREEN}{Colors.BOLD}✓ Calculation complete!{Colors.RESET}")
        print(f"{Colors.DIM}For official tax purposes, consult the Dutch Tax Authority (Belastingdienst).{Colors.RESET}")
        print(f"{Colors.BLUE}{'─' * 70}{Colors.RESET}\n")
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⊘ Form cancelled by user.{Colors.RESET}\n")
    except Exception as e:
        print(f"\n{Colors.RED}✗ Error: {e}{Colors.RESET}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
