namespace DutchTax.Web.Models;

public enum ResidencyStatus
{
    RESIDENT,
    NON_RESIDENT
}

public enum AllocationStrategy
{
    EQUAL,
    PROPORTIONAL,
    CUSTOM
}

public enum IncomeSourceType
{
    EMPLOYMENT,
    SELF_EMPLOYMENT,
    RENTAL,
    PENSION,
    INVESTMENT,
    OTHER
}

public enum AssetType
{
    SAVINGS,
    INVESTMENT,
    REAL_ESTATE,
    BUSINESS,
    OTHER
}

public sealed class IncomeSource
{
    public string Name { get; set; } = string.Empty;
    public IncomeSourceType SourceType { get; set; }
    public decimal GrossAmount { get; set; }
    public string Description { get; set; } = string.Empty;
}

public sealed class Asset
{
    public string Name { get; set; } = string.Empty;
    public AssetType AssetType { get; set; }
    public decimal Value { get; set; }
    public string Description { get; set; } = string.Empty;
}

public sealed class Deduction
{
    public string Name { get; set; } = string.Empty;
    public decimal Amount { get; set; }
    public string DeductionType { get; set; } = "personal";
    public string Description { get; set; } = string.Empty;
}

public sealed class TaxCredit
{
    public string Name { get; set; } = string.Empty;
    public decimal Amount { get; set; }
    public string Description { get; set; } = string.Empty;
}

public sealed class TaxBracket
{
    public decimal LowerBound { get; set; }
    public decimal? UpperBound { get; set; }
    public decimal Rate { get; set; }
    public string Description { get; set; } = string.Empty;
}

public sealed class TaxYearConfig
{
    public required int Year { get; init; }
    public required List<TaxBracket> Box1Brackets { get; init; }
    public required decimal Box3Rate { get; init; }
    public required decimal GeneralTaxCredit { get; init; }
    public string Description { get; init; } = string.Empty;
    public decimal Box3SavingsReturnRate { get; init; }
    public decimal Box3InvestmentReturnRate { get; init; }
    public decimal Box3TaxFreeAssetsSingle { get; init; }
    public decimal PremiumAowRate { get; init; }
    public decimal PremiumAnwRate { get; init; }
    public decimal PremiumWlzRate { get; init; }
    public decimal PremiumIncomeCap { get; init; }
    public decimal GreenInvestmentTaxCreditRate { get; init; }
    public decimal GreenInvestmentCreditBaseCapSingle { get; init; }
}

public static class TaxConfigs
{
    public static TaxYearConfig Latest => ByYear[ByYear.Keys.Max()];

    public static IReadOnlyDictionary<int, TaxYearConfig> ByYear { get; } =
        new Dictionary<int, TaxYearConfig>
        {
            [2023] = new TaxYearConfig
            {
                Year = 2023,
                Box1Brackets =
                [
                    new TaxBracket { LowerBound = 0m, UpperBound = 36_092m, Rate = 0.1893m, Description = "First bracket (18.93%)" },
                    new TaxBracket { LowerBound = 36_092m, UpperBound = 72_185m, Rate = 0.2809m, Description = "Second bracket (28.09%)" },
                    new TaxBracket { LowerBound = 72_185m, UpperBound = 962_500m, Rate = 0.3635m, Description = "Third bracket (36.35%)" },
                    new TaxBracket { LowerBound = 962_500m, UpperBound = null, Rate = 0.4950m, Description = "Fourth bracket (49.50%)" }
                ],
                Box3Rate = 0.3600m,
                GeneralTaxCredit = 2_713m,
                Description = "Dutch tax year 2023 - Realistic rates"
            },
            [2024] = new TaxYearConfig
            {
                Year = 2024,
                Box1Brackets =
                [
                    new TaxBracket { LowerBound = 0m, UpperBound = 37_150m, Rate = 0.1895m, Description = "First bracket (18.95%)" },
                    new TaxBracket { LowerBound = 37_150m, UpperBound = 74_301m, Rate = 0.2809m, Description = "Second bracket (28.09%)" },
                    new TaxBracket { LowerBound = 74_301m, UpperBound = 991_472m, Rate = 0.3635m, Description = "Third bracket (36.35%)" },
                    new TaxBracket { LowerBound = 991_472m, UpperBound = null, Rate = 0.4950m, Description = "Fourth bracket (49.50%)" }
                ],
                Box3Rate = 0.3600m,
                GeneralTaxCredit = 2_813m,
                Description = "Dutch tax year 2024 - Realistic rates"
            },
            [2025] = new TaxYearConfig
            {
                Year = 2025,
                Box1Brackets =
                [
                    new TaxBracket { LowerBound = 0m, UpperBound = 37_895m, Rate = 0.1906m, Description = "First bracket (19.06%)" },
                    new TaxBracket { LowerBound = 37_895m, UpperBound = 75_790m, Rate = 0.2843m, Description = "Second bracket (28.43%)" },
                    new TaxBracket { LowerBound = 75_790m, UpperBound = 1_011_724m, Rate = 0.3705m, Description = "Third bracket (37.05%)" },
                    new TaxBracket { LowerBound = 1_011_724m, UpperBound = null, Rate = 0.4949m, Description = "Fourth bracket (49.49%)" }
                ],
                Box3Rate = 0.3600m,
                GeneralTaxCredit = 2_917m,
                Box3SavingsReturnRate = 0.0137m,
                Box3InvestmentReturnRate = 0.0588m,
                Box3TaxFreeAssetsSingle = 57_684m,
                PremiumAowRate = 0.1790m,
                PremiumAnwRate = 0.0010m,
                PremiumWlzRate = 0.0965m,
                PremiumIncomeCap = 38_441m,
                GreenInvestmentTaxCreditRate = 0.0010m,
                GreenInvestmentCreditBaseCapSingle = 26_312m,
                Description = "Dutch tax year 2025 - Realistic rates"
            }
        };
}
