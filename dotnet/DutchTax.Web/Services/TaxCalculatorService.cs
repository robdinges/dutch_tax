using DutchTax.Web.Models;

namespace DutchTax.Web.Services;

public sealed class TaxCalculatorService
{
    public TaxCalculationResponse Calculate(TaxRequest request)
    {
        var config = TaxConfigs.Latest;
        var parsedMembers = request.Members.Select(ParseMember).ToList();

        var box1Breakdown = new Dictionary<string, MemberBreakdown>();
        var box1Total = 0m;

        foreach (var member in parsedMembers)
        {
            var grossIncome = member.Incomes.Sum(x => x.GrossAmount);
            var deductions = member.Deductions.Sum(x => x.Amount);
            var taxableIncome = Math.Max(0m, grossIncome - deductions);

            var box1Tax = ComputeBox1Tax(taxableIncome, config.Box1Brackets);
            var taxCredits = member.TaxCredits.Sum(x => x.Amount);
            var taxAfterCredits = Math.Max(0m, box1Tax - taxCredits);
            var netLiability = Math.Max(0m, taxAfterCredits - member.WithheldTax);
            var assets = member.Assets.Sum(x => x.Value);

            box1Breakdown[member.FullName] = new MemberBreakdown
            {
                GrossIncome = grossIncome,
                Deductions = deductions,
                TaxableIncome = taxableIncome,
                Box1Tax = box1Tax,
                TaxCredits = taxCredits,
                WithheldTax = member.WithheldTax,
                NetLiability = netLiability,
                Assets = assets
            };

            box1Total += box1Tax;
        }

        var totalAssets = parsedMembers.Sum(m => m.Assets.Sum(a => a.Value));
        var totalIncome = parsedMembers.Sum(m => m.Incomes.Sum(i => i.GrossAmount));
        var box3Tax = totalAssets * config.Box3Rate;

        var strategy = ParseAllocationStrategy(request.AllocationStrategy);
        var box3Allocation = AllocateBox3(parsedMembers, box3Tax, strategy);

        var totalTax = parsedMembers.Sum(m =>
        {
            var netBox1 = box1Breakdown[m.FullName].NetLiability;
            var box3Share = box3Allocation.TryGetValue(m.FullName, out var allocation) ? allocation : 0m;
            return netBox1 + box3Share;
        });

        var effectiveRate = totalIncome > 0m ? decimal.Round((totalTax / totalIncome) * 100m, 2) : 0m;

        return new TaxCalculationResponse
        {
            Box1Breakdown = box1Breakdown,
            Box1Total = box1Total,
            Box3Tax = box3Tax,
            Box3Rate = config.Box3Rate * 100m,
            Box3Allocation = box3Allocation,
            TotalTax = totalTax,
            TotalAssets = totalAssets,
            TotalIncome = totalIncome,
            EffectiveTaxRate = effectiveRate,
            GeneralTaxCredit = config.GeneralTaxCredit,
            TaxYear = config.Year
        };
    }

    private static decimal ComputeBox1Tax(decimal taxableIncome, List<TaxBracket> brackets)
    {
        if (taxableIncome <= 0m)
        {
            return 0m;
        }

        var totalTax = 0m;
        foreach (var bracket in brackets.OrderBy(b => b.LowerBound))
        {
            var taxableInBracket = ComputeTaxableInBracket(taxableIncome, bracket);
            if (taxableInBracket > 0m)
            {
                totalTax += taxableInBracket * bracket.Rate;
            }
        }

        return totalTax;
    }

    private static decimal ComputeTaxableInBracket(decimal income, TaxBracket bracket)
    {
        if (income <= bracket.LowerBound)
        {
            return 0m;
        }

        var upper = bracket.UpperBound.HasValue ? Math.Min(income, bracket.UpperBound.Value) : income;
        return Math.Max(0m, upper - bracket.LowerBound);
    }

    private static Dictionary<string, decimal> AllocateBox3(
        IReadOnlyCollection<ParsedMember> members,
        decimal totalBox3Tax,
        AllocationStrategy strategy)
    {
        var allocation = new Dictionary<string, decimal>();

        if (members.Count == 0)
        {
            return allocation;
        }

        if (strategy == AllocationStrategy.EQUAL)
        {
            var perPerson = totalBox3Tax / members.Count;
            foreach (var member in members)
            {
                allocation[member.FullName] = perPerson;
            }

            return allocation;
        }

        if (strategy == AllocationStrategy.PROPORTIONAL)
        {
            var totalWealth = members.Sum(m => m.Assets.Sum(a => a.Value));
            if (totalWealth <= 0m)
            {
                var perPerson = totalBox3Tax / members.Count;
                foreach (var member in members)
                {
                    allocation[member.FullName] = perPerson;
                }

                return allocation;
            }

            foreach (var member in members)
            {
                var wealth = member.Assets.Sum(a => a.Value);
                var ratio = wealth / totalWealth;
                allocation[member.FullName] = totalBox3Tax * ratio;
            }

            return allocation;
        }

        var customPerPerson = totalBox3Tax / members.Count;
        foreach (var member in members)
        {
            allocation[member.FullName] = customPerPerson;
        }

        return allocation;
    }

    private static AllocationStrategy ParseAllocationStrategy(string strategy) =>
        Enum.TryParse<AllocationStrategy>(strategy, true, out var parsed)
            ? parsed
            : AllocationStrategy.EQUAL;

    private static ParsedMember ParseMember(MemberRequest member)
    {
        var fullName = string.IsNullOrWhiteSpace(member.FullName) ? "Unknown" : member.FullName.Trim();
        var bsn = string.IsNullOrWhiteSpace(member.Bsn) ? Guid.NewGuid().ToString("N")[..9] : member.Bsn.Trim();

        var incomes = member.Incomes
            .Where(i => i.Amount >= 0m)
            .Select(i => new IncomeSource
            {
                Name = string.IsNullOrWhiteSpace(i.Description) ? i.Type : i.Description,
                SourceType = ParseIncomeType(i.Type),
                GrossAmount = i.Amount,
                Description = i.Description
            })
            .ToList();

        var deductions = member.Deductions
            .Where(d => d.Amount >= 0m)
            .Select(d => new Deduction
            {
                Name = string.IsNullOrWhiteSpace(d.Description) ? "Deduction" : d.Description,
                Amount = d.Amount,
                DeductionType = "personal",
                Description = d.Description
            })
            .ToList();

        var assets = member.Assets
            .Where(a => a.Value >= 0m)
            .Select(a => new Asset
            {
                Name = string.IsNullOrWhiteSpace(a.Description) ? a.Type : a.Description,
                AssetType = ParseAssetType(a.Type),
                Value = a.Value,
                Description = a.Description
            })
            .ToList();

        return new ParsedMember
        {
            FullName = fullName,
            Bsn = bsn,
            ResidencyStatus = ParseResidency(member.ResidencyStatus),
            Incomes = incomes,
            Deductions = deductions,
            Assets = assets,
            TaxCredits = [],
            WithheldTax = Math.Max(0m, member.WithheldTax)
        };
    }

    private static ResidencyStatus ParseResidency(string status) =>
        Enum.TryParse<ResidencyStatus>(status, true, out var parsed)
            ? parsed
            : ResidencyStatus.RESIDENT;

    private static IncomeSourceType ParseIncomeType(string type) =>
        Enum.TryParse<IncomeSourceType>(type, true, out var parsed)
            ? parsed
            : IncomeSourceType.OTHER;

    private static AssetType ParseAssetType(string type) =>
        Enum.TryParse<AssetType>(type, true, out var parsed)
            ? parsed
            : AssetType.OTHER;

    private sealed class ParsedMember
    {
        public required string FullName { get; init; }
        public required string Bsn { get; init; }
        public required ResidencyStatus ResidencyStatus { get; init; }
        public required List<IncomeSource> Incomes { get; init; }
        public required List<Deduction> Deductions { get; init; }
        public required List<Asset> Assets { get; init; }
        public required List<TaxCredit> TaxCredits { get; init; }
        public required decimal WithheldTax { get; init; }
    }
}
