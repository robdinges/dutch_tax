"""
Interactive Form Preview

Demonstrates the improved, intuitive tax form with smart validation,
helpful hints, and a fresh, modern layout.
"""

from decimal import Decimal
from object_model import (
    Person, Household, IncomeSource, Asset, Deduction, TaxCredit,
    IncomeSourceType, AssetType, ResidencyStatus
)
from tax_brackets import get_latest_tax_config
from tax_form import TaxForm, Colors


def preview_form_layout():
    """Preview the new form layout with colors and formatting."""
    form = TaxForm()
    
    print("\n" * 2)
    form.print_header("🇳🇱 DUTCH TAX CALCULATOR 2025")
    
    print(f"{Colors.CYAN}Welcome to the interactive Dutch tax calculator!{Colors.RESET}")
    print(f"This form will help you calculate your tax liability for 2025.\n")
    
    print(f"{Colors.DIM}Tax Year Information:{Colors.RESET}")
    print(f"  • General Tax Credit: €2,917.00")
    print(f"  • Box3 Rate: 36.0%")
    print(f"  • Tax Brackets: 4 progressive brackets\n")
    
    form.print_section("👤 Add Household Member")
    print(f"\n{Colors.BOLD}Full name (€):{Colors.RESET}")
    print(f"{Colors.DIM}  💡 Tip: e.g., John Smith or Maria Garcia{Colors.RESET}")
    print(f"  > John Smith")
    
    form.print_success("John Smith added to household")
    
    form.print_section("💰 Income Sources for John Smith")
    print("\nIncome type")
    print(f"  {Colors.CYAN}1{Colors.RESET}. Employment (W-2/salary)")
    print(f"  {Colors.CYAN}2{Colors.RESET}. Self-Employment (business)")
    print(f"  {Colors.CYAN}3{Colors.RESET}. Rental (property income)")
    print(f"  {Colors.CYAN}4{Colors.RESET}. Pension (retirement)")
    print(f"  {Colors.CYAN}5{Colors.RESET}. Investment (dividends, interest)")
    print(f"  {Colors.CYAN}6{Colors.RESET}. Other")
    print(f"\n{Colors.BOLD}Your choice:{Colors.RESET} 1")
    
    form.print_success("Income 'Salary' added (€60,000.00)")
    
    form.print_section("📝 Deductions for John Smith")
    print(f"{Colors.BOLD}Add deductions? [Y/n]:{Colors.RESET} Y")
    
    form.print_success("Deduction 'Mortgage Interest' added (€10,000.00)")
    
    form.print_section("🏦 Assets for John Smith")
    print(f"{Colors.BOLD}Add assets? [Y/n]:{Colors.RESET} Y")
    
    form.print_success("Asset 'Savings Account' added (€75,000.00)")
    
    form.print_info("General tax credit applied (€2,917.00)")
    
    # Simulate results
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}Press Enter to calculate your taxes...{Colors.RESET}")
    print("=" * 70)
    
    form.print_header("📊 TAX CALCULATION RESULTS")
    
    form.print_section("Member: John Smith")
    
    print(f"\n{Colors.BOLD}Income:{Colors.RESET}")
    print(f"  • Salary                             €    60,000.00")
    print(f"  {Colors.DIM}{'─' * 50}{Colors.RESET}")
    print(f"  {'Total Gross Income':<35} €    60,000.00")
    
    print(f"\n{Colors.BOLD}Deductions:{Colors.RESET}")
    print(f"  • Mortgage Interest                  €    10,000.00")
    print(f"  {Colors.DIM}{'─' * 50}{Colors.RESET}")
    print(f"  {'Total Deductions':<35} €    10,000.00")
    
    print(f"\n{Colors.BOLD}Box1 Tax Calculation:{Colors.RESET}")
    print(f"  {'Taxable Income':<35} €    50,000.00")
    print(f"  {'Tax (before credits)':<35} €     9,952.47")
    print(f"  {'Tax Credits':<35} -€     2,917.00")
    print(f"  {'Tax after credits':<35} €     7,035.47")
    print(f"  {Colors.DIM}{'─' * 50}{Colors.RESET}")
    print(f"  {Colors.GREEN}{Colors.BOLD}{'No Tax Due':<35} €         0.00{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}Assets (Box3):{Colors.RESET}")
    print(f"  • Savings Account                    €    75,000.00")
    print(f"  {Colors.DIM}{'─' * 50}{Colors.RESET}")
    print(f"  {'Total Assets':<35} €    75,000.00")
    
    form.print_section("Final Tax Calculation")
    
    print(f"\n{Colors.BOLD}Tax Breakdown:{Colors.RESET}")
    print(f"  John Smith")
    print(f"    Box1 (Income Tax): €            0.00")
    print(f"    Box3 (Wealth Tax): €       27,000.00")
    print(f"    {Colors.BOLD}Subtotal{Colors.RESET}:       €       27,000.00")
    
    print(f"\n  {Colors.BOLD}Box3 Summary (Equal allocation):{Colors.RESET}")
    print(f"    Total Assets:     €       75,000.00")
    print(f"    At 36% Rate:      €       27,000.00\n")
    
    print(f"  {Colors.DIM}{'─' * 50}{Colors.RESET}")
    print(f"  {Colors.RED}{Colors.BOLD}{'TOTAL TAX DUE':<35} €       27,000.00{Colors.RESET}\n")
    
    print(f"  Effective Tax Rate: 45.00%")
    
    # Closing
    print(f"\n{Colors.BLUE}{'─' * 70}{Colors.RESET}")
    print(f"{Colors.GREEN}{Colors.BOLD}✓ Calculation complete!{Colors.RESET}")
    print(f"{Colors.DIM}For official tax purposes, consult the Dutch Tax Authority (Belastingdienst).{Colors.RESET}")
    print(f"{Colors.BLUE}{'─' * 70}{Colors.RESET}\n")


def preview_smart_validation():
    """Show examples of smart validation and helpful hints."""
    form = TaxForm()
    
    print("\n" * 2)
    form.print_header("🎯 SMART VALIDATION EXAMPLES")
    
    form.print_section("Example 1: Decimal Input Validation")
    print(f"\n{Colors.BOLD}Gross amount per year (€):{Colors.RESET}")
    print(f"{Colors.DIM}  💡 Tip: Annual gross income{Colors.RESET}")
    print(f"  > invalid_amount")
    form.print_error("Invalid amount. Please use format: 1000 or 1000.50")
    print(f"\n{Colors.BOLD}Gross amount per year (€):{Colors.RESET}")
    print(f"  > 50000")
    form.print_success("✓ Input accepted")
    
    form.print_section("Example 2: Required Field Validation")
    print(f"\n{Colors.BOLD}Full name:{Colors.RESET}")
    print(f"  > ")
    form.print_error("This field is required. Please try again.")
    print(f"\n{Colors.BOLD}Full name:{Colors.RESET}")
    print(f"  > John Smith")
    form.print_success("✓ Input accepted")
    
    form.print_section("Example 3: Choice Selection")
    print("\nIncome type")
    print(f"  {Colors.CYAN}1{Colors.RESET}. Employment (W-2/salary)")
    print(f"  {Colors.CYAN}2{Colors.RESET}. Self-Employment (business)")
    print(f"  {Colors.CYAN}3{Colors.RESET}. Rental (property income)")
    print(f"\n{Colors.BOLD}Your choice:{Colors.RESET} 4")
    form.print_error("Invalid choice. Please select from: 1, 2, 3")
    print(f"\n{Colors.BOLD}Your choice:{Colors.RESET} 1")
    form.print_success("✓ Selection accepted")
    
    form.print_section("Example 4: Confirmation with Default")
    print(f"\n{Colors.BOLD}Add another income source? [y/N]:{Colors.RESET} ")
    print(f"{Colors.DIM}(Pressed Enter, used default: No){Colors.RESET}")
    
    form.print_section("Example 5: Negative Value Prevention")
    print(f"\n{Colors.BOLD}Withheld tax amount (€):{Colors.RESET}")
    print(f"{Colors.DIM}  💡 Tip: Employer withholding, bank withholding, or quarterly payments{Colors.RESET}")
    print(f"  > -1000")
    form.print_error("Amount cannot be negative. Please try again.")
    print(f"\n{Colors.BOLD}Withheld tax amount (€):{Colors.RESET}")
    print(f"  > 15000")
    form.print_success("✓ Input accepted")


if __name__ == "__main__":
    preview_form_layout()
    print("\n" * 2)
    preview_smart_validation()
    print(f"\n{Colors.GREEN}✓ Form preview complete!{Colors.RESET}\n")
