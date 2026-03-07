# DutchTax.Web (.NET versie)

ASP.NET Core versie van de Dutch Tax Calculator met dezelfde frontend-flow en API-endpoints.

## Vereisten

- .NET SDK 8.0 of hoger

## Lokaal draaien

```bash
cd dotnet/DutchTax.Web
dotnet restore
dotnet run
```

Open daarna:
- `http://localhost:5000` of
- `https://localhost:5001`

## API endpoints

- `GET /api/income-types`
- `GET /api/asset-types`
- `GET /api/allocation-strategies`
- `POST /api/calculate`

## Frontend

Static files staan in `wwwroot`:
- `index.html`
- `app.js`
- `style.css`
