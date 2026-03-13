# DutchTax.Web (.NET versie)

ASP.NET Core versie van de Dutch Tax Calculator met dezelfde procesflow als de Python-app.

Ondersteund in deze .NET-variant:

- `POST /api/joint-items-preview` voor verplichte partnerverdeling
- `POST /api/calculate` met Box 1/2/3, premies, heffingskortingen en eindafrekening
- buitenlandse dividendverrekening en groene-beleggingenkorting
- kleine-aanslagregel (`<= EUR 57` -> `NIETS_TE_BETALEN`)

## Vereisten

- .NET SDK 10.0 of hoger

## Lokaal draaien

```bash
cd dotnet/DutchTax.Web
dotnet restore
dotnet run
```

Of vanuit de repository root met de macOS-workaround in één commando:

```bash
./run-dotnet.sh
```

Let op: gebruik `./run-dotnet.sh` (met `./`).

Uitgebreide NL handleiding:
- `dotnet/LOCAL_RUN_NL.md`
- `dotnet/FUNCTIONEEL_EN_OBJECTMODEL_NL.md`

Open daarna:
- `http://localhost:5000` of
- `https://localhost:5001`

## API endpoints

- `GET /api/income-types`
- `GET /api/box1-deduction-types`
- `GET /api/allocation-strategies`
- `POST /api/joint-items-preview`
- `POST /api/calculate`

## Frontend

Static files staan in `wwwroot`:
- `index.html`
- `app.js`
- `style.css`
