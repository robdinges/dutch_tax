var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

var pathBase = builder.Configuration["PATH_BASE"];
if (!string.IsNullOrWhiteSpace(pathBase))
{
    if (!pathBase.StartsWith('/'))
        pathBase = "/" + pathBase;
    app.UsePathBase(pathBase);
}

app.MapGet("/probe", () => Results.Json(new
{
    status = "ok",
    message = ".NET draait correct op deze server.",
    dotnet = Environment.Version.ToString(),
    time = DateTime.UtcNow
}));

app.MapGet("/", () => Results.Text("DutchTax probe OK - zie /probe voor details."));

app.Run();
