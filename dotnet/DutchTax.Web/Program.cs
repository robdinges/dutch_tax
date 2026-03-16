using DutchTax.Web.Models;
using DutchTax.Web.Services;
using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddSingleton<TaxCalculatorService>();

var app = builder.Build();

var pathBase = builder.Configuration["PATH_BASE"];
if (!string.IsNullOrWhiteSpace(pathBase))
{
    if (!pathBase.StartsWith('/'))
    {
        pathBase = "/" + pathBase;
    }
    app.UsePathBase(pathBase);
}

app.UseDefaultFiles();
app.UseStaticFiles();

app.MapGet("/api/health", () => Results.Json(new { status = "ok", app = "DutchTax.Web" }));

app.MapGet("/api/income-types", () => Results.Json(new
{
    types = new[]
    {
        new TypeOption { Id = "EMPLOYMENT", Label = "Loon uit dienstverband" },
        new TypeOption { Id = "SELF_EMPLOYMENT", Label = "Winst uit onderneming" },
        new TypeOption { Id = "BENEFITS", Label = "Uitkeringen" },
        new TypeOption { Id = "PENSION", Label = "Pensioen" },
        new TypeOption { Id = "OTHER", Label = "Overig Box 1 inkomen" }
    }
}));

app.MapGet("/api/box1-deduction-types", () => Results.Json(new
{
    types = new[]
    {
        new TypeOption { Id = "MORTGAGE_INTEREST", Label = "Hypotheekrente" },
        new TypeOption { Id = "ENTREPRENEUR_ALLOWANCE", Label = "Ondernemersaftrek" },
        new TypeOption { Id = "PERSONAL_ALLOWANCE", Label = "Persoonsgebonden aftrek" },
        new TypeOption { Id = "OTHER", Label = "Overige aftrek" }
    }
}));

app.MapGet("/api/allocation-strategies", () => Results.Json(new
{
    strategies = new[]
    {
        new TypeOption { Id = "EQUAL", Label = "Gelijk" },
        new TypeOption { Id = "PROPORTIONAL", Label = "Proportioneel op netto vermogen" },
        new TypeOption { Id = "CUSTOM", Label = "Custom verdeling (%)" }
    }
}));

app.MapPost("/api/joint-items-preview", (JsonElement payload, TaxCalculatorService calculator) =>
{
    try
    {
        var result = calculator.PreviewJointItems(payload);
        return Results.Json(result);
    }
    catch (Exception ex)
    {
        return Results.Json(new { error = $"Preview error: {ex.Message}" }, statusCode: 500);
    }
});

app.MapPost("/api/calculate", (JsonElement payload, TaxCalculatorService calculator) =>
{
    try
    {
        var result = calculator.Calculate(payload);
        return Results.Json(result);
    }
    catch (Exception ex)
    {
        return Results.Json(new { error = $"Calculation error: {ex.Message}" }, statusCode: 500);
    }
});

app.MapFallbackToFile("index.html");

app.Run();
