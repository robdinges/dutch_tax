using DutchTax.Web.Models;
using DutchTax.Web.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddSingleton<TaxCalculatorService>();

var app = builder.Build();

app.UseDefaultFiles();
app.UseStaticFiles();

app.MapGet("/api/income-types", () => Results.Json(new
{
    types = new[]
    {
        new TypeOption { Id = "EMPLOYMENT", Label = "Employment (W-2/salary)" },
        new TypeOption { Id = "SELF_EMPLOYMENT", Label = "Self-Employment (business)" },
        new TypeOption { Id = "RENTAL", Label = "Rental (property income)" },
        new TypeOption { Id = "PENSION", Label = "Pension (retirement)" },
        new TypeOption { Id = "INVESTMENT", Label = "Investment (dividends, interest)" },
        new TypeOption { Id = "OTHER", Label = "Other" }
    }
}));

app.MapGet("/api/asset-types", () => Results.Json(new
{
    types = new[]
    {
        new TypeOption { Id = "SAVINGS", Label = "Savings Account" },
        new TypeOption { Id = "INVESTMENT", Label = "Investment Portfolio" },
        new TypeOption { Id = "REAL_ESTATE", Label = "Real Estate (primary residence excluded)" },
        new TypeOption { Id = "BUSINESS", Label = "Business Assets" },
        new TypeOption { Id = "OTHER", Label = "Other Assets" }
    }
}));

app.MapGet("/api/allocation-strategies", () => Results.Json(new
{
    strategies = new[]
    {
        new TypeOption { Id = "EQUAL", Label = "Equal (50-50 split)" },
        new TypeOption { Id = "PROPORTIONAL", Label = "Proportional (by income)" },
        new TypeOption { Id = "CUSTOM", Label = "Custom percentages" }
    }
}));

app.MapPost("/api/calculate", (TaxRequest request, TaxCalculatorService calculator) =>
{
    try
    {
        var result = calculator.Calculate(request);
        return Results.Json(result);
    }
    catch (Exception ex)
    {
        return Results.Json(new { error = $"Calculation error: {ex.Message}" }, statusCode: 500);
    }
});

app.MapFallbackToFile("index.html");

app.Run();
