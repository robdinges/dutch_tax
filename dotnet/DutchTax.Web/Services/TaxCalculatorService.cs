using System.Globalization;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;

namespace DutchTax.Web.Services;

public sealed class TaxCalculatorService
{
    private const decimal Box2Rate2025 = 0.269m;
    private const decimal SmallOwnHomeDebtDeductionRate = 0.76667m;
    private const decimal SmallPayableAssessmentThreshold = 57m;

    private static readonly decimal[] EigenwoningforfaitThresholds = [0m, 12_500m, 25_000m, 50_000m, 75_000m, 1_330_000m];
    private static readonly decimal[] EigenwoningforfaitPercents = [0m, 0.0010m, 0.0020m, 0.0025m, 0.0035m];
    private const decimal EigenwoningforfaitUpperBaseFixed = 4655m;
    private const decimal EigenwoningforfaitUpperRate = 0.0235m;

    private static readonly TaxConfig Config2025 = new()
    {
        Year = 2025,
        Box1Brackets =
        [
            new TaxBracket(0m, 38_441m, 0.0817m, "First bracket (8.17%)"),
            new TaxBracket(38_441m, 76_817m, 0.3748m, "Second bracket (37.48%)"),
            new TaxBracket(76_817m, null, 0.4950m, "Third bracket (49.50%)")
        ],
        Box3Rate = 0.3600m,
        Box3SavingsReturnRate = 0.0137m,
        Box3InvestmentReturnRate = 0.0588m,
        Box3TaxFreeAssetsSingle = 57_684m,
        PremiumAowRate = 0.1790m,
        PremiumAnwRate = 0.0010m,
        PremiumWlzRate = 0.0965m,
        PremiumIncomeCap = 38_441m,
        GreenInvestmentTaxCreditRate = 0.0010m,
        GreenInvestmentCreditBaseCapSingle = 26_312m
    };

    private readonly string _contentRootPath;

    public TaxCalculatorService(IHostEnvironment hostEnvironment)
    {
        _contentRootPath = hostEnvironment.ContentRootPath;
    }

    public object PreviewJointItems(JsonElement data)
    {
        var members = GetArray(data, "members").ToList();
        if (members.Count == 0)
        {
            throw new InvalidOperationException("Minimaal 1 persoon is verplicht.");
        }

        var memberIds = new List<string>();
        var memberLabels = new Dictionary<string, string>();
        var memberBox3Inputs = new List<MemberBox3Input>();

        for (var idx = 0; idx < members.Count; idx++)
        {
            var member = members[idx];
            var memberId = FirstNonEmpty(
                GetString(member, "member_id"),
                GetString(member, "bsn"),
                $"member_{idx + 1}");
            var fullName = FirstNonEmpty(GetString(member, "full_name"), $"Persoon {idx + 1}");

            memberIds.Add(memberId);
            memberLabels[memberId] = fullName;

            var box3Data = GetObject(member, "box3");
            var investmentAccounts = GetArray(box3Data, "investment_accounts").ToList();

            var accountsInvestmentsTotal = investmentAccounts
                .Where(account => !GetBoolFlexible(account, "is_green", "isGreen"))
                .Sum(account => RoundDownEuro(GetDecimalFlexible(account, "amount", "value")));

            var accountsGreenInvestmentsTotal = investmentAccounts
                .Where(account => GetBoolFlexible(account, "is_green", "isGreen"))
                .Sum(account => RoundDownEuro(GetDecimalFlexible(account, "amount", "value")));

            var accountDividendWithholdingTotal = investmentAccounts
                .Sum(account => RoundUpEuro(GetDecimal(account, "dividend_withholding")));

            var accountForeignDividendWithholdingTotal = investmentAccounts
                .Sum(account => RoundUpEuro(GetDecimal(account, "foreign_dividend_withholding")));

            memberBox3Inputs.Add(new MemberBox3Input
            {
                Savings = RoundDownEuro(GetDecimal(box3Data, "savings")),
                Investments = investmentAccounts.Count > 0
                    ? accountsInvestmentsTotal
                    : RoundDownEuro(GetDecimal(box3Data, "investments")),
                OtherAssets = RoundDownEuro(GetDecimal(box3Data, "other_assets")),
                Debts = RoundUpEuro(GetDecimal(box3Data, "debts")),
                GreenInvestments = accountsGreenInvestmentsTotal,
                DirectDividendWithholding = investmentAccounts.Count > 0
                    ? accountDividendWithholdingTotal
                    : RoundUpEuro(GetDecimalFlexible(member, "dividend_withholding", "withheld_dividend_tax")),
                DirectForeignDividendWithholding = investmentAccounts.Count > 0
                    ? accountForeignDividendWithholdingTotal
                    : RoundUpEuro(GetDecimal(member, "foreign_dividend_withholding"))
            });
        }

        var ownHome = GetObject(GetObject(data, "household_box1"), "own_home");
        if (ownHome.ValueKind == JsonValueKind.Undefined)
        {
            ownHome = GetObject(data, "own_home");
        }

        var householdWozValue = RoundDownEuro(GetDecimal(ownHome, "woz_value"));
        var householdPeriodFraction = GetDouble(ownHome, "period_fraction", 1.0);
        var householdHasOwnHome = GetBool(ownHome, "has_own_home") && householdWozValue > 0m;

        var householdEigenwoningforfait = householdHasOwnHome
            ? RoundDownEuro(CalculateEigenwoningforfait(householdWozValue, (decimal)householdPeriodFraction))
            : 0m;

        var householdSmallOwnHomeDebtDeduction = RoundUpEuro(householdEigenwoningforfait * SmallOwnHomeDebtDeductionRate);

        var householdBox3 = GetObject(data, "box3_household");
        var useHouseholdBox3 = householdBox3.ValueKind == JsonValueKind.Object && householdBox3.EnumerateObject().Any();

        decimal totalSavings;
        decimal totalInvestments;
        decimal totalOtherAssets;
        decimal totalDebts;
        decimal totalGreenInvestments;
        decimal householdDividendWithholdingTotal;
        decimal householdForeignDividendWithholdingTotal;

        if (useHouseholdBox3)
        {
            var savingsAccounts = GetArray(householdBox3, "savings_accounts").ToList();
            var investmentAccounts = GetArray(householdBox3, "investment_accounts").ToList();
            var otherAssetsItems = GetArray(householdBox3, "other_assets_items").ToList();
            var debtItems = GetArray(householdBox3, "debt_items").ToList();

            var accountsSavingsTotal = savingsAccounts
                .Where(account => !GetBoolFlexible(account, "is_green", "isGreen"))
                .Sum(account => RoundDownEuro(GetDecimal(account, "amount")));

            var accountsInvestmentsTotal = investmentAccounts
                .Where(account => !GetBoolFlexible(account, "is_green", "isGreen"))
                .Sum(account => RoundDownEuro(GetDecimalFlexible(account, "amount", "value")));

            var accountsGreenInvestmentsTotal = investmentAccounts
                .Where(account => GetBoolFlexible(account, "is_green", "isGreen"))
                .Sum(account => RoundDownEuro(GetDecimalFlexible(account, "amount", "value")));

            var itemsOtherAssetsTotal = otherAssetsItems.Sum(item => RoundDownEuro(GetDecimal(item, "amount")));
            var itemsDebtTotal = debtItems.Sum(item => RoundUpEuro(decimal.Abs(GetDecimal(item, "amount"))));

            totalSavings = savingsAccounts.Count > 0 ? accountsSavingsTotal : RoundDownEuro(GetDecimal(householdBox3, "savings"));
            totalInvestments = investmentAccounts.Count > 0 ? accountsInvestmentsTotal : RoundDownEuro(GetDecimal(householdBox3, "investments"));
            totalOtherAssets = otherAssetsItems.Count > 0 ? itemsOtherAssetsTotal : RoundDownEuro(GetDecimal(householdBox3, "other_assets"));
            totalDebts = debtItems.Count > 0 ? itemsDebtTotal : RoundUpEuro(GetDecimal(householdBox3, "debts"));
            totalGreenInvestments = accountsGreenInvestmentsTotal;

            householdDividendWithholdingTotal = RoundUpEuro(GetDecimalFlexible(data, "dividend_withholding_total", "total_dividend_withholding"));
            if (householdDividendWithholdingTotal == 0m)
            {
                householdDividendWithholdingTotal = RoundUpEuro(GetDecimal(householdBox3, "total_dividend_withholding"));
            }

            householdForeignDividendWithholdingTotal = RoundUpEuro(GetDecimalFlexible(data, "foreign_dividend_withholding_total", "total_foreign_dividend_withholding"));
            if (householdForeignDividendWithholdingTotal == 0m)
            {
                householdForeignDividendWithholdingTotal = RoundUpEuro(GetDecimal(householdBox3, "total_foreign_dividend_withholding"));
            }

            if (householdDividendWithholdingTotal == 0m && investmentAccounts.Count > 0)
            {
                householdDividendWithholdingTotal = investmentAccounts.Sum(account => RoundUpEuro(GetDecimal(account, "dividend_withholding")));
            }

            if (householdForeignDividendWithholdingTotal == 0m && investmentAccounts.Count > 0)
            {
                householdForeignDividendWithholdingTotal = investmentAccounts.Sum(account => RoundUpEuro(GetDecimal(account, "foreign_dividend_withholding")));
            }
        }
        else
        {
            totalSavings = memberBox3Inputs.Sum(x => x.Savings);
            totalInvestments = memberBox3Inputs.Sum(x => x.Investments);
            totalOtherAssets = memberBox3Inputs.Sum(x => x.OtherAssets);
            totalDebts = memberBox3Inputs.Sum(x => x.Debts);
            totalGreenInvestments = memberBox3Inputs.Sum(x => x.GreenInvestments);
            householdDividendWithholdingTotal = memberBox3Inputs.Sum(x => x.DirectDividendWithholding);
            householdForeignDividendWithholdingTotal = memberBox3Inputs.Sum(x => x.DirectForeignDividendWithholding);
        }

        var grossAssets = totalSavings + totalInvestments + totalOtherAssets;
        var totalNetAssets = Math.Max(0m, grossAssets - totalDebts);
        var taxFreeAssets = Config2025.Box3TaxFreeAssetsSingle * members.Count;
        var netAssetFactor = grossAssets > 0m ? totalNetAssets / grossAssets : 0m;
        var netSavings = totalSavings * netAssetFactor;
        var netNonSavings = (totalInvestments + totalOtherAssets) * netAssetFactor;
        var deemedReturnSavings = RoundDownEuro(netSavings * Config2025.Box3SavingsReturnRate);
        var deemedReturnNonSavings = RoundDownEuro(netNonSavings * Config2025.Box3InvestmentReturnRate);
        var deemedReturnTotal = deemedReturnSavings + deemedReturnNonSavings;
        var correctedAssets = Math.Max(0m, totalNetAssets - taxFreeAssets);
        var correctionFactor = totalNetAssets > 0m ? correctedAssets / totalNetAssets : 0m;
        var deemedBox3Income = RoundDownEuro(deemedReturnTotal * correctionFactor);
        var debtNegativeIncomePost = -totalDebts;
        var box3Income = RoundDownEuro(deemedBox3Income + debtNegativeIncomePost);
        var box3TaxableIncome = Math.Max(0m, box3Income);

        var grondslagSparenBeleggen = Math.Max(0m, (totalSavings + totalInvestments) - taxFreeAssets);

        var sharedTotals = new Dictionary<string, decimal>
        {
            ["eigenwoningforfait"] = householdEigenwoningforfait,
            ["aftrek_geen_of_kleine_eigenwoningschuld"] = householdSmallOwnHomeDebtDeduction,
            ["grondslag_voordeel_sparen_beleggen"] = grondslagSparenBeleggen,
            ["vrijstelling_groene_beleggingen"] = totalGreenInvestments,
            ["ingehouden_dividendbelasting"] = householdDividendWithholdingTotal,
            ["ingehouden_buitenlandse_dividendbelasting"] = householdForeignDividendWithholdingTotal
        };

        return new
        {
            success = true,
            member_ids = memberIds,
            member_labels = memberLabels,
            joint_distribution_totals = sharedTotals
        };
    }

    public object Calculate(JsonElement data)
    {
        var savedFile = SaveInputDataToJson(data);
        var members = GetArray(data, "members").ToList();
        if (members.Count == 0)
        {
            throw new InvalidOperationException("Minimaal 1 persoon is verplicht.");
        }

        var fiscalPartner = GetBool(data, "fiscal_partner") || members.Count > 1;
        var allocationStrategy = FirstNonEmpty(GetString(data, "allocation_strategy"), "PROPORTIONAL");

        var ownHome = GetObject(GetObject(data, "household_box1"), "own_home");
        if (ownHome.ValueKind == JsonValueKind.Undefined)
        {
            ownHome = GetObject(data, "own_home");
        }

        var householdWozValue = RoundDownEuro(GetDecimal(ownHome, "woz_value"));
        var householdPeriodFraction = (decimal)GetDouble(ownHome, "period_fraction", 1.0);
        var householdHasOwnHome = GetBool(ownHome, "has_own_home") && householdWozValue > 0m;

        var householdEigenwoningforfait = householdHasOwnHome
            ? RoundDownEuro(CalculateEigenwoningforfait(householdWozValue, householdPeriodFraction))
            : 0m;
        var householdSmallOwnHomeDebtDeduction = RoundUpEuro(householdEigenwoningforfait * SmallOwnHomeDebtDeductionRate);

        var householdBox3 = GetObject(data, "box3_household");
        var useHouseholdBox3 = householdBox3.ValueKind == JsonValueKind.Object && householdBox3.EnumerateObject().Any();

        var memberInputs = new List<MemberInput>();
        var memberIds = new List<string>();

        for (var idx = 0; idx < members.Count; idx++)
        {
            var member = members[idx];
            var memberId = FirstNonEmpty(
                GetString(member, "member_id"),
                GetString(member, "bsn"),
                $"member_{idx + 1}");
            var fullName = FirstNonEmpty(GetString(member, "full_name"), $"Persoon {idx + 1}");

            memberIds.Add(memberId);

            var box1Data = GetObject(member, "box1");
            var incomes = GetArray(box1Data, "incomes").ToList();
            if (incomes.Count == 0)
            {
                incomes = GetArray(member, "incomes").ToList();
            }

            var deductions = GetArray(box1Data, "deductions").ToList();
            if (deductions.Count == 0)
            {
                deductions = GetArray(member, "deductions").ToList();
            }

            var taxCredits = GetArray(box1Data, "tax_credits").ToList();
            if (taxCredits.Count == 0)
            {
                taxCredits = GetArray(member, "tax_credits").ToList();
            }

            var hasAow = GetBoolFlexible(box1Data, "has_aow", "hasAow") || GetBoolFlexible(member, "has_aow", "hasAow");

            var box2Data = GetObject(member, "box2");
            var memberBox3 = GetObject(member, "box3");
            var memberInvestmentAccounts = GetArray(memberBox3, "investment_accounts").ToList();

            var accountsInvestmentsTotal = memberInvestmentAccounts
                .Where(account => !GetBoolFlexible(account, "is_green", "isGreen"))
                .Sum(account => RoundDownEuro(GetDecimalFlexible(account, "amount", "value")));

            var accountsGreenInvestmentsTotal = memberInvestmentAccounts
                .Where(account => GetBoolFlexible(account, "is_green", "isGreen"))
                .Sum(account => RoundDownEuro(GetDecimalFlexible(account, "amount", "value")));

            var accountDividendWithholdingTotal = memberInvestmentAccounts
                .Sum(account => RoundUpEuro(GetDecimal(account, "dividend_withholding")));

            var accountForeignDividendWithholdingTotal = memberInvestmentAccounts
                .Sum(account => RoundUpEuro(GetDecimal(account, "foreign_dividend_withholding")));

            var input = new MemberInput
            {
                MemberId = memberId,
                FullName = fullName,
                Incomes = incomes,
                Deductions = deductions,
                HasAow = hasAow,
                TaxCredits = taxCredits,
                WageWithholding = RoundUpEuro(GetDecimalFlexible(member, "wage_withholding", "withheld_tax")),
                OtherPrepaidTaxes = RoundUpEuro(GetDecimal(member, "other_prepaid_taxes")),
                Box2 = new Box2Input
                {
                    HasSubstantialInterest = GetBool(box2Data, "has_substantial_interest"),
                    DividendIncome = RoundDownEuro(GetDecimal(box2Data, "dividend_income")),
                    SaleGain = RoundDownEuro(GetDecimal(box2Data, "sale_gain")),
                    AcquisitionPrice = RoundUpEuro(GetDecimal(box2Data, "acquisition_price"))
                },
                Box3 = new MemberBox3Input
                {
                    Savings = RoundDownEuro(GetDecimal(memberBox3, "savings")),
                    Investments = memberInvestmentAccounts.Count > 0
                        ? accountsInvestmentsTotal
                        : RoundDownEuro(GetDecimal(memberBox3, "investments")),
                    OtherAssets = RoundDownEuro(GetDecimal(memberBox3, "other_assets")),
                    Debts = RoundUpEuro(GetDecimal(memberBox3, "debts")),
                    GreenInvestments = accountsGreenInvestmentsTotal,
                    DirectDividendWithholding = memberInvestmentAccounts.Count > 0
                        ? accountDividendWithholdingTotal
                        : RoundUpEuro(GetDecimalFlexible(member, "dividend_withholding", "withheld_dividend_tax")),
                    DirectForeignDividendWithholding = memberInvestmentAccounts.Count > 0
                        ? accountForeignDividendWithholdingTotal
                        : RoundUpEuro(GetDecimal(member, "foreign_dividend_withholding"))
                }
            };

            memberInputs.Add(input);
        }

        decimal totalSavings;
        decimal totalInvestments;
        decimal totalOtherAssets;
        decimal totalDebts;
        decimal totalGreenInvestments;
        decimal householdDividendWithholdingTotal;
        decimal householdForeignDividendWithholdingTotal;

        if (useHouseholdBox3)
        {
            var savingsAccounts = GetArray(householdBox3, "savings_accounts").ToList();
            var investmentAccounts = GetArray(householdBox3, "investment_accounts").ToList();
            var otherAssetsItems = GetArray(householdBox3, "other_assets_items").ToList();
            var debtItems = GetArray(householdBox3, "debt_items").ToList();

            var accountsSavingsTotal = savingsAccounts
                .Where(account => !GetBoolFlexible(account, "is_green", "isGreen"))
                .Sum(account => RoundDownEuro(GetDecimal(account, "amount")));

            var accountsInvestmentsTotal = investmentAccounts
                .Where(account => !GetBoolFlexible(account, "is_green", "isGreen"))
                .Sum(account => RoundDownEuro(GetDecimalFlexible(account, "amount", "value")));

            var accountsGreenInvestmentsTotal = investmentAccounts
                .Where(account => GetBoolFlexible(account, "is_green", "isGreen"))
                .Sum(account => RoundDownEuro(GetDecimalFlexible(account, "amount", "value")));

            var itemsOtherAssetsTotal = otherAssetsItems.Sum(item => RoundDownEuro(GetDecimal(item, "amount")));
            var itemsDebtTotal = debtItems.Sum(item => RoundUpEuro(decimal.Abs(GetDecimal(item, "amount"))));

            totalSavings = savingsAccounts.Count > 0 ? accountsSavingsTotal : RoundDownEuro(GetDecimal(householdBox3, "savings"));
            totalInvestments = investmentAccounts.Count > 0 ? accountsInvestmentsTotal : RoundDownEuro(GetDecimal(householdBox3, "investments"));
            totalOtherAssets = otherAssetsItems.Count > 0 ? itemsOtherAssetsTotal : RoundDownEuro(GetDecimal(householdBox3, "other_assets"));
            totalDebts = debtItems.Count > 0 ? itemsDebtTotal : RoundUpEuro(GetDecimal(householdBox3, "debts"));
            totalGreenInvestments = accountsGreenInvestmentsTotal;

            householdDividendWithholdingTotal = RoundUpEuro(GetDecimalFlexible(data, "dividend_withholding_total", "total_dividend_withholding"));
            if (householdDividendWithholdingTotal == 0m)
            {
                householdDividendWithholdingTotal = RoundUpEuro(GetDecimal(householdBox3, "total_dividend_withholding"));
            }

            householdForeignDividendWithholdingTotal = RoundUpEuro(GetDecimalFlexible(data, "foreign_dividend_withholding_total", "total_foreign_dividend_withholding"));
            if (householdForeignDividendWithholdingTotal == 0m)
            {
                householdForeignDividendWithholdingTotal = RoundUpEuro(GetDecimal(householdBox3, "total_foreign_dividend_withholding"));
            }

            if (householdDividendWithholdingTotal == 0m && investmentAccounts.Count > 0)
            {
                householdDividendWithholdingTotal = investmentAccounts.Sum(account => RoundUpEuro(GetDecimal(account, "dividend_withholding")));
            }

            if (householdForeignDividendWithholdingTotal == 0m && investmentAccounts.Count > 0)
            {
                householdForeignDividendWithholdingTotal = investmentAccounts.Sum(account => RoundUpEuro(GetDecimal(account, "foreign_dividend_withholding")));
            }
        }
        else
        {
            totalSavings = memberInputs.Sum(m => m.Box3.Savings);
            totalInvestments = memberInputs.Sum(m => m.Box3.Investments);
            totalOtherAssets = memberInputs.Sum(m => m.Box3.OtherAssets);
            totalDebts = memberInputs.Sum(m => m.Box3.Debts);
            totalGreenInvestments = memberInputs.Sum(m => m.Box3.GreenInvestments);
            householdDividendWithholdingTotal = memberInputs.Sum(m => m.Box3.DirectDividendWithholding);
            householdForeignDividendWithholdingTotal = memberInputs.Sum(m => m.Box3.DirectForeignDividendWithholding);
        }

        var grossAssets = totalSavings + totalInvestments + totalOtherAssets;
        var totalNetAssets = Math.Max(0m, grossAssets - totalDebts);
        var taxFreeAssets = Config2025.Box3TaxFreeAssetsSingle * members.Count;

        var netAssetFactor = grossAssets > 0m ? totalNetAssets / grossAssets : 0m;
        var netSavings = totalSavings * netAssetFactor;
        var netNonSavings = (totalInvestments + totalOtherAssets) * netAssetFactor;

        var deemedReturnSavings = RoundDownEuro(netSavings * Config2025.Box3SavingsReturnRate);
        var deemedReturnNonSavings = RoundDownEuro(netNonSavings * Config2025.Box3InvestmentReturnRate);
        var deemedReturnTotal = deemedReturnSavings + deemedReturnNonSavings;

        var correctedAssets = Math.Max(0m, totalNetAssets - taxFreeAssets);
        var correctionFactor = totalNetAssets > 0m ? correctedAssets / totalNetAssets : 0m;
        var deemedIncomeBeforeDebts = RoundDownEuro(deemedReturnTotal * correctionFactor);
        var debtNegativeIncomePost = -totalDebts;
        var correctedDeemedReturn = RoundDownEuro(deemedIncomeBeforeDebts + debtNegativeIncomePost);
        var box3TaxableIncome = Math.Max(0m, correctedDeemedReturn);

        var grondslagSparenBeleggen = Math.Max(0m, (totalSavings + totalInvestments) - taxFreeAssets);

        var sharedTotals = new Dictionary<string, decimal>
        {
            ["eigenwoningforfait"] = householdEigenwoningforfait,
            ["aftrek_geen_of_kleine_eigenwoningschuld"] = householdSmallOwnHomeDebtDeduction,
            ["grondslag_voordeel_sparen_beleggen"] = grondslagSparenBeleggen,
            ["vrijstelling_groene_beleggingen"] = totalGreenInvestments,
            ["ingehouden_dividendbelasting"] = householdDividendWithholdingTotal,
            ["ingehouden_buitenlandse_dividendbelasting"] = householdForeignDividendWithholdingTotal
        };

        var requiresDistribution = fiscalPartner && memberIds.Count >= 2;
        var jointDistributionRaw = GetObject(data, "joint_distribution");
        var (jointDistribution, distributionErrors) = NormalizeJointDistribution(memberIds, sharedTotals, jointDistributionRaw, requiresDistribution);
        if (distributionErrors.Count > 0)
        {
            throw new InvalidOperationException(string.Join(" ", distributionErrors));
        }

        var taxableGrondslagByMember = new Dictionary<string, decimal>();
        var taxableGrondslagTotal = 0m;
        foreach (var memberId in memberIds)
        {
            var grondslagShare = jointDistribution["grondslag_voordeel_sparen_beleggen"].GetValueOrDefault(memberId, 0m);
            var taxableShare = Math.Max(0m, grondslagShare);
            taxableGrondslagByMember[memberId] = taxableShare;
            taxableGrondslagTotal += taxableShare;
        }

        Dictionary<string, decimal> box3TaxableIncomeAllocated;
        if (box3TaxableIncome <= 0m)
        {
            box3TaxableIncomeAllocated = memberIds.ToDictionary(id => id, _ => 0m);
        }
        else if (taxableGrondslagTotal <= 0m)
        {
            box3TaxableIncomeAllocated = SplitEqual(memberIds, box3TaxableIncome);
        }
        else
        {
            box3TaxableIncomeAllocated = new Dictionary<string, decimal>();
            var running = 0m;
            for (var i = 0; i < memberIds.Count; i++)
            {
                var memberId = memberIds[i];
                decimal allocated;
                if (i == memberIds.Count - 1)
                {
                    allocated = box3TaxableIncome - running;
                }
                else
                {
                    allocated = RoundDownEuro(box3TaxableIncome * (taxableGrondslagByMember[memberId] / taxableGrondslagTotal));
                    running += allocated;
                }

                box3TaxableIncomeAllocated[memberId] = allocated;
            }
        }

        var partnerWealthWeights = memberIds.ToDictionary(
            id => id,
            id => jointDistribution["grondslag_voordeel_sparen_beleggen"].GetValueOrDefault(id, 0m));

        var totalPartnerWealth = partnerWealthWeights.Values.Sum();
        var partnerSharePct = new Dictionary<string, decimal>();
        if (totalPartnerWealth <= 0m)
        {
            var equalPct = memberIds.Count > 0 ? 100m / memberIds.Count : 0m;
            foreach (var memberId in memberIds)
            {
                partnerSharePct[memberId] = equalPct;
            }
        }
        else
        {
            foreach (var memberId in memberIds)
            {
                partnerSharePct[memberId] = (partnerWealthWeights[memberId] / totalPartnerWealth) * 100m;
            }
        }

        var grondslagRendementsberekeningTotal = totalSavings + totalInvestments;
        var grondslagRendementsberekeningPartner = AllocateByWeights(memberIds, grondslagRendementsberekeningTotal, partnerWealthWeights);
        var grondslagSparenBeleggenPartner = AllocateByWeights(memberIds, grondslagSparenBeleggen, partnerWealthWeights);
        var fictiefRendementPartner = AllocateByWeights(memberIds, deemedReturnTotal, partnerWealthWeights);

        var memberResults = new List<Dictionary<string, object?>>();

        var box1Total = 0m;
        var box2Total = 0m;
        var box3Total = 0m;
        var totalTaxCredits = 0m;
        var totalPrepaidTaxes = 0m;
        var premiumAowTotal = 0m;
        var premiumAnwTotal = 0m;
        var premiumWlzTotal = 0m;
        var premiumBasisTotal = 0m;
        var box1TaxableIncomeTotal = 0m;
        var box2TaxableIncomeTotal = 0m;
        var box3TaxableIncomeTotal = 0m;
        var totalGrossIncome = 0m;
        var totalMemberNetSettlement = 0m;

        var bracketsAppliedTotals = new Dictionary<string, BracketAggregate>();

        foreach (var member in memberInputs)
        {
            var memberId = member.MemberId;

            var grossIncome = 0m;
            var totalLaborCredit = 0m;
            foreach (var item in member.Incomes)
            {
                var lineIncome = RoundDownEuro(GetDecimalFlexible(item, "amount", "gross_amount"));
                var laborCredit = RoundUpEuro(GetDecimalFlexible(item, "labor_credit", "arbeidskorting"));
                grossIncome += lineIncome;
                totalLaborCredit += laborCredit;
            }

            totalGrossIncome += grossIncome;

            var totalDeductions = member.Deductions.Sum(item => RoundUpEuro(GetDecimal(item, "amount")));
            var eigenwoningforfaitShare = jointDistribution["eigenwoningforfait"].GetValueOrDefault(memberId, 0m);
            var smallOwnHomeDebtDeductionShare = jointDistribution["aftrek_geen_of_kleine_eigenwoningschuld"].GetValueOrDefault(memberId, 0m);

            var box1TaxableIncome = RoundDownEuro(Math.Max(0m,
                grossIncome
                + eigenwoningforfaitShare
                - smallOwnHomeDebtDeductionShare
                - totalDeductions));

            box1TaxableIncomeTotal += box1TaxableIncome;

            var box1Brackets = ComputeBox1BracketBreakdown(box1TaxableIncome);
            var box1Tax = RoundDownEuro(box1Brackets.Sum(row => row.TaxAmount));
            box1Total += box1Tax;

            var premiumBasisMember = Math.Min(box1TaxableIncome, Config2025.PremiumIncomeCap);
            premiumBasisTotal += premiumBasisMember;
            var premiumAowMember = member.HasAow ? 0m : RoundDownEuro(premiumBasisMember * Config2025.PremiumAowRate);
            var premiumAnwMember = RoundDownEuro(premiumBasisMember * Config2025.PremiumAnwRate);
            var premiumWlzMember = RoundDownEuro(premiumBasisMember * Config2025.PremiumWlzRate);
            var premiumMemberTotal = premiumAowMember + premiumAnwMember + premiumWlzMember;

            premiumAowTotal += premiumAowMember;
            premiumAnwTotal += premiumAnwMember;
            premiumWlzTotal += premiumWlzMember;

            foreach (var row in box1Brackets)
            {
                if (!bracketsAppliedTotals.TryGetValue(row.Description, out var aggregate))
                {
                    aggregate = new BracketAggregate
                    {
                        Description = row.Description,
                        Rate = row.Rate,
                        TaxableAmount = 0m,
                        TaxAmount = 0m
                    };
                    bracketsAppliedTotals[row.Description] = aggregate;
                }

                aggregate.TaxableAmount += row.TaxableAmount;
                aggregate.TaxAmount += row.TaxAmount;
            }

            var manualCreditItems = member.TaxCredits
                .Select(c => new CreditItem
                {
                    Name = FirstNonEmpty(GetString(c, "name"), "Heffingskorting"),
                    Amount = RoundUpEuro(GetDecimal(c, "amount"))
                })
                .ToList();

            var totalMemberCredits = manualCreditItems.Sum(item => item.Amount);

            var greenExemptionShare = jointDistribution["vrijstelling_groene_beleggingen"].GetValueOrDefault(memberId, 0m);
            var greenInvestmentCredit = ComputeGreenInvestmentCredit(greenExemptionShare);
            if (greenInvestmentCredit > 0m)
            {
                manualCreditItems.Add(new CreditItem
                {
                    Name = "Heffingskorting groene beleggingen",
                    Amount = greenInvestmentCredit
                });
                totalMemberCredits += greenInvestmentCredit;
            }

            totalTaxCredits += totalMemberCredits;

            var box2TaxableIncome = member.Box2.HasSubstantialInterest
                ? Math.Max(0m, member.Box2.DividendIncome + member.Box2.SaleGain - member.Box2.AcquisitionPrice)
                : 0m;
            box2TaxableIncome = RoundDownEuro(box2TaxableIncome);
            box2TaxableIncomeTotal += box2TaxableIncome;
            var box2Tax = RoundDownEuro(box2TaxableIncome * Box2Rate2025);
            box2Total += box2Tax;

            var grondslagShare = jointDistribution["grondslag_voordeel_sparen_beleggen"].GetValueOrDefault(memberId, 0m);
            var box3TaxableMember = box3TaxableIncomeAllocated.GetValueOrDefault(memberId, 0m);
            box3TaxableIncomeTotal += box3TaxableMember;

            var box3TaxBeforeForeignDividend = RoundDownEuro(box3TaxableMember * Config2025.Box3Rate);
            var foreignDividendWithholding = jointDistribution["ingehouden_buitenlandse_dividendbelasting"].GetValueOrDefault(memberId, 0m);
            var foreignDividendOffset = Math.Min(box3TaxBeforeForeignDividend, RoundUpEuro(foreignDividendWithholding));
            var box3TaxMember = Math.Max(0m, box3TaxBeforeForeignDividend - foreignDividendOffset);
            box3Total += box3TaxMember;

            var dividendWithholding = jointDistribution["ingehouden_dividendbelasting"].GetValueOrDefault(memberId, 0m);
            var prepaidTaxes = member.WageWithholding + dividendWithholding + member.OtherPrepaidTaxes;
            totalPrepaidTaxes += prepaidTaxes;

            var grossMemberTax = RoundDownEuro(box1Tax + box2Tax + box3TaxMember + premiumMemberTotal);
            var netMemberSettlementBeforeThreshold = RoundDownEuro(grossMemberTax - totalMemberCredits - prepaidTaxes);
            var (netMemberSettlement, thresholdApplied) = ApplySmallPayableThreshold(netMemberSettlementBeforeThreshold);
            totalMemberNetSettlement += netMemberSettlement;

            var box1BracketsOutput = box1Brackets.Select(row => new Dictionary<string, object?>
            {
                ["description"] = row.Description,
                ["lower_bound"] = row.LowerBound,
                ["upper_bound"] = row.UpperBound,
                ["rate"] = row.Rate,
                ["taxable_amount"] = row.TaxableAmount,
                ["tax_amount"] = row.TaxAmount
            }).ToList();

            memberResults.Add(new Dictionary<string, object?>
            {
                ["member_id"] = memberId,
                ["full_name"] = member.FullName,
                ["box1"] = new Dictionary<string, object?>
                {
                    ["gross_income"] = grossIncome,
                    ["labor_credit_total"] = totalLaborCredit,
                    ["has_aow"] = member.HasAow,
                    ["eigenwoningforfait"] = eigenwoningforfaitShare,
                    ["aftrek_geen_of_kleine_eigenwoningschuld"] = smallOwnHomeDebtDeductionShare,
                    ["deductions"] = totalDeductions,
                    ["taxable_income"] = box1TaxableIncome,
                    ["tax"] = box1Tax,
                    ["brackets"] = box1BracketsOutput,
                    ["credits"] = new Dictionary<string, object?>
                    {
                        ["items"] = manualCreditItems.Select(item => new Dictionary<string, object?>
                        {
                            ["name"] = item.Name,
                            ["amount"] = item.Amount
                        }).ToList(),
                        ["total"] = totalMemberCredits
                    }
                },
                ["box2"] = new Dictionary<string, object?>
                {
                    ["has_substantial_interest"] = member.Box2.HasSubstantialInterest,
                    ["taxable_income"] = box2TaxableIncome,
                    ["tax_rate"] = Box2Rate2025 * 100m,
                    ["tax"] = box2Tax
                },
                ["box3"] = new Dictionary<string, object?>
                {
                    ["grondslag_rendementsberekening"] = grondslagRendementsberekeningPartner.GetValueOrDefault(memberId, 0m),
                    ["grondslag_sparen_beleggen"] = grondslagSparenBeleggenPartner.GetValueOrDefault(memberId, 0m),
                    ["fictief_rendement_totaal"] = deemedReturnTotal,
                    ["partner_share_percentage"] = partnerSharePct.GetValueOrDefault(memberId, 0m),
                    ["fictief_rendement_partner"] = fictiefRendementPartner.GetValueOrDefault(memberId, 0m),
                    ["grondslag_voordeel_sparen_beleggen"] = grondslagShare,
                    ["vrijstelling_groene_beleggingen"] = greenExemptionShare,
                    ["taxable_income"] = box3TaxableMember,
                    ["tax_before_foreign_dividend"] = box3TaxBeforeForeignDividend,
                    ["foreign_dividend_withholding"] = foreignDividendWithholding,
                    ["foreign_dividend_tax_credit_applied"] = foreignDividendOffset,
                    ["tax"] = box3TaxMember
                },
                ["prepayments"] = new Dictionary<string, object?>
                {
                    ["wage_withholding"] = member.WageWithholding,
                    ["dividend_withholding"] = dividendWithholding,
                    ["other_prepaid_taxes"] = member.OtherPrepaidTaxes,
                    ["total"] = prepaidTaxes
                },
                ["premiums"] = new Dictionary<string, object?>
                {
                    ["aow"] = premiumAowMember,
                    ["anw"] = premiumAnwMember,
                    ["wlz"] = premiumWlzMember,
                    ["total"] = premiumMemberTotal
                },
                ["settlement"] = new Dictionary<string, object?>
                {
                    ["gross_income_tax"] = grossMemberTax,
                    ["tax_credits"] = totalMemberCredits,
                    ["prepaid_taxes"] = prepaidTaxes,
                    ["net_settlement_before_assessment_threshold"] = netMemberSettlementBeforeThreshold,
                    ["assessment_threshold_applied"] = thresholdApplied,
                    ["net_settlement"] = netMemberSettlement,
                    ["result_type"] = SettlementResultType(netMemberSettlement)
                },
                ["joint_allocation"] = new Dictionary<string, object?>
                {
                    ["eigenwoningforfait"] = eigenwoningforfaitShare,
                    ["aftrek_geen_of_kleine_eigenwoningschuld"] = smallOwnHomeDebtDeductionShare,
                    ["grondslag_voordeel_sparen_beleggen"] = grondslagShare,
                    ["vrijstelling_groene_beleggingen"] = greenExemptionShare,
                    ["ingehouden_dividendbelasting"] = dividendWithholding,
                    ["ingehouden_buitenlandse_dividendbelasting"] = foreignDividendWithholding
                }
            });
        }

        var verzamelinkomen = box1TaxableIncomeTotal + box2TaxableIncomeTotal + box3TaxableIncomeTotal;
        var totalPremiums = premiumAowTotal + premiumAnwTotal + premiumWlzTotal;
        var box1Box3Tax = box1Total + box3Total;
        var grossIncomeTax = RoundDownEuro(box1Box3Tax + totalPremiums + box2Total);
        var netSettlementBeforeAssessmentThreshold = RoundDownEuro(grossIncomeTax - totalTaxCredits - totalPrepaidTaxes);
        var netSettlement = RoundDownEuro(totalMemberNetSettlement);

        var effectiveRate = totalGrossIncome > 0m
            ? Math.Round((grossIncomeTax / totalGrossIncome) * 100m, 2)
            : 0m;

        var jointDistributionOutput = jointDistribution.ToDictionary(
            item => item.Key,
            item => (object?)item.Value.ToDictionary(x => x.Key, x => (object?)x.Value));

        var box1BracketsAppliedOutput = bracketsAppliedTotals.Values
            .OrderBy(x => x.Rate)
            .Select(x => new Dictionary<string, object?>
            {
                ["description"] = x.Description,
                ["rate"] = x.Rate,
                ["taxable_amount"] = x.TaxableAmount,
                ["tax_amount"] = x.TaxAmount
            })
            .ToList();

        return new Dictionary<string, object?>
        {
            ["success"] = true,
            ["tax_year"] = Config2025.Year,
            ["input_saved_to"] = savedFile,
            ["fiscal_partner"] = fiscalPartner,
            ["allocation_strategy"] = allocationStrategy,
            ["members"] = memberResults,
            ["joint_distribution"] = jointDistributionOutput,
            ["joint_distribution_totals"] = sharedTotals,
            ["box1"] = new Dictionary<string, object?>
            {
                ["total_taxable_income"] = box1TaxableIncomeTotal,
                ["total_tax"] = box1Total,
                ["brackets_applied"] = box1BracketsAppliedOutput
            },
            ["box2"] = new Dictionary<string, object?>
            {
                ["total_taxable_income"] = box2TaxableIncomeTotal,
                ["tax_rate"] = Box2Rate2025 * 100m,
                ["total_tax"] = box2Total
            },
            ["box3"] = new Dictionary<string, object?>
            {
                ["tax_rate"] = Config2025.Box3Rate * 100m,
                ["tax_free_assets"] = taxFreeAssets,
                ["savings_return_rate"] = Config2025.Box3SavingsReturnRate * 100m,
                ["investment_return_rate"] = Config2025.Box3InvestmentReturnRate * 100m,
                ["total_savings"] = totalSavings,
                ["total_investments"] = totalInvestments,
                ["total_other_assets"] = totalOtherAssets,
                ["total_debts"] = totalDebts,
                ["total_net_assets"] = totalNetAssets,
                ["deemed_return_savings"] = deemedReturnSavings,
                ["deemed_return_non_savings"] = deemedReturnNonSavings,
                ["deemed_return_total"] = deemedReturnTotal,
                ["correction_factor"] = correctionFactor,
                ["deemed_income_before_debts"] = deemedIncomeBeforeDebts,
                ["debt_negative_income_post"] = debtNegativeIncomePost,
                ["corrected_deemed_return"] = correctedDeemedReturn,
                ["taxable_income"] = box3TaxableIncome,
                ["total_tax"] = box3Total,
                ["allocation"] = memberIds.ToDictionary(
                    memberId => memberId,
                    memberId => (object?)jointDistribution["grondslag_voordeel_sparen_beleggen"].GetValueOrDefault(memberId, 0m)),
                ["green_investments_total"] = totalGreenInvestments,
                ["green_exemption_total"] = sharedTotals["vrijstelling_groene_beleggingen"],
                ["foreign_dividend_withholding_total"] = householdForeignDividendWithholdingTotal
            },
            ["settlement"] = new Dictionary<string, object?>
            {
                ["box1_box3_tax"] = box1Box3Tax,
                ["box2_tax"] = box2Total,
                ["premiums"] = new Dictionary<string, object?>
                {
                    ["basis"] = premiumBasisTotal,
                    ["aow"] = premiumAowTotal,
                    ["anw"] = premiumAnwTotal,
                    ["wlz"] = premiumWlzTotal,
                    ["total"] = totalPremiums
                },
                ["gross_income_tax"] = grossIncomeTax,
                ["total_tax_credits"] = totalTaxCredits,
                ["total_prepaid_taxes"] = totalPrepaidTaxes,
                ["net_settlement_before_assessment_threshold"] = netSettlementBeforeAssessmentThreshold,
                ["net_settlement"] = netSettlement,
                ["result_type"] = SettlementResultType(netSettlement),
                ["effective_rate"] = effectiveRate
            },
            ["verzamelinkomen"] = verzamelinkomen
        };
    }

    private string SaveInputDataToJson(JsonElement data)
    {
        var householdId = FirstNonEmpty(GetString(data, "household_id"), "WEB_001");
        var safeHouseholdId = Regex.Replace(householdId, "[^A-Za-z0-9_-]", "_");

        var submissionsDir = Path.GetFullPath(Path.Combine(_contentRootPath, "..", "..", "submissions"));
        Directory.CreateDirectory(submissionsDir);

        var filePath = Path.Combine(submissionsDir, $"{safeHouseholdId}.json");
        var payloadNode = JsonNode.Parse(data.GetRawText()) ?? new JsonObject();

        var wrapped = new JsonObject
        {
            ["saved_at"] = DateTime.Now.ToString("O", CultureInfo.InvariantCulture),
            ["household_id"] = householdId,
            ["data"] = payloadNode
        };

        File.WriteAllText(filePath, wrapped.ToJsonString(new JsonSerializerOptions { WriteIndented = true }));
        return filePath;
    }

    private static List<BracketRow> ComputeBox1BracketBreakdown(decimal taxableIncome)
    {
        var rows = new List<BracketRow>();
        foreach (var bracket in Config2025.Box1Brackets.OrderBy(b => b.LowerBound))
        {
            var taxableInBracket = ComputeTaxableInBracket(taxableIncome, bracket);
            if (taxableInBracket <= 0m)
            {
                continue;
            }

            var taxAmount = taxableInBracket * bracket.Rate;
            rows.Add(new BracketRow
            {
                Description = bracket.Description,
                LowerBound = bracket.LowerBound,
                UpperBound = bracket.UpperBound,
                Rate = bracket.Rate,
                TaxableAmount = taxableInBracket,
                TaxAmount = taxAmount
            });
        }

        return rows;
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

    private static decimal CalculateEigenwoningforfait(decimal wozValue, decimal periodFraction)
    {
        if (wozValue < 0m)
        {
            throw new InvalidOperationException("WOZ value cannot be negative");
        }

        if (periodFraction < 0m || periodFraction > 1m)
        {
            throw new InvalidOperationException("period_fraction must be between 0.0 and 1.0");
        }

        decimal forfait;
        if (wozValue <= EigenwoningforfaitThresholds[^1])
        {
            var bandIndex = 0;
            for (var index = 0; index < EigenwoningforfaitThresholds.Length - 1; index++)
            {
                if (wozValue >= EigenwoningforfaitThresholds[index])
                {
                    bandIndex = index;
                }
                else
                {
                    break;
                }
            }

            forfait = wozValue * EigenwoningforfaitPercents[bandIndex];
        }
        else
        {
            forfait = EigenwoningforfaitUpperBaseFixed + EigenwoningforfaitUpperRate * (wozValue - EigenwoningforfaitThresholds[^1]);
        }

        return forfait * periodFraction;
    }

    private static decimal ComputeGreenInvestmentCredit(decimal greenExemptionShare)
    {
        var creditBaseCapped = Math.Min(greenExemptionShare, Config2025.GreenInvestmentCreditBaseCapSingle);
        return RoundUpEuro(creditBaseCapped * Config2025.GreenInvestmentTaxCreditRate);
    }

    private static (decimal NetAmount, bool ThresholdApplied) ApplySmallPayableThreshold(decimal netAmount)
    {
        if (netAmount >= 0m && netAmount <= SmallPayableAssessmentThreshold)
        {
            return (0m, true);
        }

        return (netAmount, false);
    }

    private static string SettlementResultType(decimal netSettlement)
    {
        if (netSettlement == 0m)
        {
            return "NIETS_TE_BETALEN";
        }

        return netSettlement > 0m ? "TE_BETALEN" : "TERUGGAAF";
    }

    private static (Dictionary<string, Dictionary<string, decimal>> Distribution, List<string> Errors) NormalizeJointDistribution(
        List<string> memberIds,
        Dictionary<string, decimal> sharedTotals,
        JsonElement rawDistribution,
        bool mustValidate)
    {
        var distribution = new Dictionary<string, Dictionary<string, decimal>>();
        var errors = new List<string>();

        foreach (var shared in sharedTotals)
        {
            var itemKey = shared.Key;
            var totalAmount = shared.Value;
            JsonElement dist = default;

            var hasDistributionObject = false;
            if (rawDistribution.ValueKind == JsonValueKind.Object
                && rawDistribution.TryGetProperty(itemKey, out var distCandidate)
                && distCandidate.ValueKind == JsonValueKind.Object)
            {
                dist = distCandidate;
                hasDistributionObject = true;
            }

            if (!hasDistributionObject && mustValidate)
            {
                errors.Add($"Verdeling voor '{itemKey}' ontbreekt of heeft onjuist formaat.");
                continue;
            }

            var itemDistribution = new Dictionary<string, decimal>();
            var providedSum = 0m;

            foreach (var memberId in memberIds)
            {
                var amount = hasDistributionObject ? GetDecimal(dist, memberId) : 0m;
                if (amount < 0m)
                {
                    errors.Add($"Verdeling voor '{itemKey}' bevat negatieve waarde voor '{memberId}'.");
                }

                itemDistribution[memberId] = amount;
                providedSum += amount;
            }

            if (mustValidate)
            {
                if (Math.Abs(providedSum - totalAmount) > 0.01m)
                {
                    errors.Add($"Verdeling voor '{itemKey}' telt op tot {providedSum} maar moet {totalAmount} zijn.");
                }

                distribution[itemKey] = itemDistribution;
            }
            else
            {
                distribution[itemKey] = SplitEqual(memberIds, totalAmount);
            }
        }

        return (distribution, errors);
    }

    private static Dictionary<string, decimal> SplitEqual(List<string> memberIds, decimal total)
    {
        if (memberIds.Count == 0)
        {
            return [];
        }

        if (memberIds.Count == 1)
        {
            return new Dictionary<string, decimal> { [memberIds[0]] = total };
        }

        var each = RoundDownEuro(total / memberIds.Count);
        var allocation = memberIds.ToDictionary(id => id, _ => each);
        var allocatedTotal = each * memberIds.Count;
        allocation[memberIds[^1]] = total - (allocatedTotal - each);
        return allocation;
    }

    private static Dictionary<string, decimal> AllocateByWeights(
        List<string> memberIds,
        decimal total,
        Dictionary<string, decimal> weights)
    {
        if (memberIds.Count == 0)
        {
            return [];
        }

        var totalWeight = memberIds.Sum(memberId => Math.Max(0m, weights.GetValueOrDefault(memberId, 0m)));
        if (totalWeight <= 0m)
        {
            return SplitEqual(memberIds, total);
        }

        var allocation = new Dictionary<string, decimal>();
        var running = 0m;
        for (var idx = 0; idx < memberIds.Count; idx++)
        {
            var memberId = memberIds[idx];
            decimal amount;
            if (idx == memberIds.Count - 1)
            {
                amount = total - running;
            }
            else
            {
                var ratio = Math.Max(0m, weights.GetValueOrDefault(memberId, 0m)) / totalWeight;
                amount = RoundDownEuro(total * ratio);
                running += amount;
            }

            allocation[memberId] = amount;
        }

        return allocation;
    }

    private static decimal RoundDownEuro(decimal value) => decimal.Floor(value);

    private static decimal RoundUpEuro(decimal value) => decimal.Ceiling(value);

    private static string FirstNonEmpty(params string[] values)
    {
        foreach (var value in values)
        {
            if (!string.IsNullOrWhiteSpace(value))
            {
                return value.Trim();
            }
        }

        return string.Empty;
    }

    private static JsonElement GetObject(JsonElement element, string propertyName)
    {
        if (element.ValueKind == JsonValueKind.Object
            && element.TryGetProperty(propertyName, out var value)
            && value.ValueKind == JsonValueKind.Object)
        {
            return value;
        }

        return default;
    }

    private static IEnumerable<JsonElement> GetArray(JsonElement element, string propertyName)
    {
        if (element.ValueKind == JsonValueKind.Object
            && element.TryGetProperty(propertyName, out var value)
            && value.ValueKind == JsonValueKind.Array)
        {
            return value.EnumerateArray();
        }

        return Array.Empty<JsonElement>();
    }

    private static decimal GetDecimal(JsonElement element, string propertyName)
    {
        if (element.ValueKind == JsonValueKind.Object
            && element.TryGetProperty(propertyName, out var value))
        {
            return GetDecimalValue(value);
        }

        return 0m;
    }

    private static decimal GetDecimalFlexible(JsonElement element, string firstPropertyName, string secondPropertyName)
    {
        var first = GetDecimal(element, firstPropertyName);
        if (first != 0m)
        {
            return first;
        }

        return GetDecimal(element, secondPropertyName);
    }

    private static bool GetBool(JsonElement element, string propertyName)
    {
        if (element.ValueKind == JsonValueKind.Object
            && element.TryGetProperty(propertyName, out var value))
        {
            if (value.ValueKind == JsonValueKind.True)
            {
                return true;
            }

            if (value.ValueKind == JsonValueKind.False)
            {
                return false;
            }

            if (value.ValueKind == JsonValueKind.String
                && bool.TryParse(value.GetString(), out var parsed))
            {
                return parsed;
            }
        }

        return false;
    }

    private static bool GetBoolFlexible(JsonElement element, string firstPropertyName, string secondPropertyName)
    {
        return GetBool(element, firstPropertyName) || GetBool(element, secondPropertyName);
    }

    private static string GetString(JsonElement element, string propertyName)
    {
        if (element.ValueKind == JsonValueKind.Object
            && element.TryGetProperty(propertyName, out var value)
            && value.ValueKind == JsonValueKind.String)
        {
            return value.GetString() ?? string.Empty;
        }

        return string.Empty;
    }

    private static double GetDouble(JsonElement element, string propertyName, double defaultValue)
    {
        if (element.ValueKind == JsonValueKind.Object
            && element.TryGetProperty(propertyName, out var value))
        {
            if (value.ValueKind == JsonValueKind.Number && value.TryGetDouble(out var numberValue))
            {
                return numberValue;
            }

            if (value.ValueKind == JsonValueKind.String
                && double.TryParse(value.GetString(), NumberStyles.Any, CultureInfo.InvariantCulture, out var parsed))
            {
                return parsed;
            }
        }

        return defaultValue;
    }

    private static decimal GetDecimalValue(JsonElement value)
    {
        if (value.ValueKind == JsonValueKind.Number && value.TryGetDecimal(out var numberValue))
        {
            return numberValue;
        }

        if (value.ValueKind == JsonValueKind.String
            && decimal.TryParse(value.GetString(), NumberStyles.Any, CultureInfo.InvariantCulture, out var parsed))
        {
            return parsed;
        }

        return 0m;
    }

    private sealed class MemberInput
    {
        public required string MemberId { get; init; }
        public required string FullName { get; init; }
        public required List<JsonElement> Incomes { get; init; }
        public required List<JsonElement> Deductions { get; init; }
        public required bool HasAow { get; init; }
        public required List<JsonElement> TaxCredits { get; init; }
        public required decimal WageWithholding { get; init; }
        public required decimal OtherPrepaidTaxes { get; init; }
        public required Box2Input Box2 { get; init; }
        public required MemberBox3Input Box3 { get; init; }
    }

    private sealed class Box2Input
    {
        public bool HasSubstantialInterest { get; init; }
        public decimal DividendIncome { get; init; }
        public decimal SaleGain { get; init; }
        public decimal AcquisitionPrice { get; init; }
    }

    private sealed class MemberBox3Input
    {
        public decimal Savings { get; init; }
        public decimal Investments { get; init; }
        public decimal OtherAssets { get; init; }
        public decimal Debts { get; init; }
        public decimal GreenInvestments { get; init; }
        public decimal DirectDividendWithholding { get; init; }
        public decimal DirectForeignDividendWithholding { get; init; }
    }

    private sealed class CreditItem
    {
        public required string Name { get; init; }
        public required decimal Amount { get; init; }
    }

    private sealed class BracketRow
    {
        public required string Description { get; init; }
        public required decimal LowerBound { get; init; }
        public required decimal? UpperBound { get; init; }
        public required decimal Rate { get; init; }
        public required decimal TaxableAmount { get; init; }
        public required decimal TaxAmount { get; init; }
    }

    private sealed class BracketAggregate
    {
        public required string Description { get; init; }
        public required decimal Rate { get; init; }
        public required decimal TaxableAmount { get; set; }
        public required decimal TaxAmount { get; set; }
    }

    private sealed class TaxConfig
    {
        public int Year { get; init; }
        public required List<TaxBracket> Box1Brackets { get; init; }
        public decimal Box3Rate { get; init; }
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

    private sealed class TaxBracket(decimal lowerBound, decimal? upperBound, decimal rate, string description)
    {
        public decimal LowerBound { get; } = lowerBound;
        public decimal? UpperBound { get; } = upperBound;
        public decimal Rate { get; } = rate;
        public string Description { get; } = description;
    }
}
