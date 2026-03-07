using System.Text.Json.Serialization;

namespace DutchTax.Web.Models;

public sealed class TaxRequest
{
    [JsonPropertyName("household_id")]
    public string HouseholdId { get; set; } = "WEB_001";

    [JsonPropertyName("allocation_strategy")]
    public string AllocationStrategy { get; set; } = "EQUAL";

    [JsonPropertyName("members")]
    public List<MemberRequest> Members { get; set; } = [];
}

public sealed class MemberRequest
{
    [JsonPropertyName("full_name")]
    public string FullName { get; set; } = string.Empty;

    [JsonPropertyName("bsn")]
    public string Bsn { get; set; } = string.Empty;

    [JsonPropertyName("residency_status")]
    public string ResidencyStatus { get; set; } = "RESIDENT";

    [JsonPropertyName("incomes")]
    public List<IncomeRequest> Incomes { get; set; } = [];

    [JsonPropertyName("deductions")]
    public List<DeductionRequest> Deductions { get; set; } = [];

    [JsonPropertyName("withheld_tax")]
    public decimal WithheldTax { get; set; }

    [JsonPropertyName("assets")]
    public List<AssetRequest> Assets { get; set; } = [];
}

public sealed class IncomeRequest
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "EMPLOYMENT";

    [JsonPropertyName("amount")]
    public decimal Amount { get; set; }

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;
}

public sealed class DeductionRequest
{
    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("amount")]
    public decimal Amount { get; set; }
}

public sealed class AssetRequest
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "SAVINGS";

    [JsonPropertyName("value")]
    public decimal Value { get; set; }

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;
}

public sealed class TypeOption
{
    public required string Id { get; init; }
    public required string Label { get; init; }
}

public sealed class MemberBreakdown
{
    [JsonPropertyName("gross_income")]
    public decimal GrossIncome { get; init; }

    [JsonPropertyName("deductions")]
    public decimal Deductions { get; init; }

    [JsonPropertyName("taxable_income")]
    public decimal TaxableIncome { get; init; }

    [JsonPropertyName("box1_tax")]
    public decimal Box1Tax { get; init; }

    [JsonPropertyName("tax_credits")]
    public decimal TaxCredits { get; init; }

    [JsonPropertyName("withheld_tax")]
    public decimal WithheldTax { get; init; }

    [JsonPropertyName("net_liability")]
    public decimal NetLiability { get; init; }

    [JsonPropertyName("assets")]
    public decimal Assets { get; init; }
}

public sealed class TaxCalculationResponse
{
    [JsonPropertyName("success")]
    public bool Success { get; init; } = true;

    [JsonPropertyName("box1_breakdown")]
    public required Dictionary<string, MemberBreakdown> Box1Breakdown { get; init; }

    [JsonPropertyName("box1_total")]
    public decimal Box1Total { get; init; }

    [JsonPropertyName("box3_tax")]
    public decimal Box3Tax { get; init; }

    [JsonPropertyName("box3_rate")]
    public decimal Box3Rate { get; init; }

    [JsonPropertyName("box3_allocation")]
    public required Dictionary<string, decimal> Box3Allocation { get; init; }

    [JsonPropertyName("total_tax")]
    public decimal TotalTax { get; init; }

    [JsonPropertyName("total_assets")]
    public decimal TotalAssets { get; init; }

    [JsonPropertyName("total_income")]
    public decimal TotalIncome { get; init; }

    [JsonPropertyName("effective_tax_rate")]
    public decimal EffectiveTaxRate { get; init; }

    [JsonPropertyName("general_tax_credit")]
    public decimal GeneralTaxCredit { get; init; }

    [JsonPropertyName("tax_year")]
    public int TaxYear { get; init; }
}
