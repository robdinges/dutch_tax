# DutchTax.Probe — minimale .NET test

Gebruik dit project om te controleren of jouw hostingomgeving .NET ondersteunt,
**voordat** je de volledige `DutchTax.Web` app uploadt.

---

## Stap 1 – Publiceren

```bash
cd dotnet/DutchTax.Probe
dotnet publish -c Release -r win-x64 --self-contained false -o ./publish
```

## Stap 2 – Uploaden via FileZilla

1. Maak op de server een tijdelijke map aan: `wwwroot/dutch_tax_probe`
2. Stel deze in als **Virtual Application** in IIS (of je hostingpanel).
3. Upload de inhoud van `publish/` naar `wwwroot/dutch_tax_probe`.

## Stap 3 – Testen

Open in je browser:

```
https://www.jouwdomein.nl/dutch_tax_probe/probe
```

Verwacht antwoord (JSON):

```json
{
  "status": "ok",
  "message": ".NET draait correct op deze server.",
  "dotnet": "10.x.x",
  "time": "2025-..."
}
```

### Resultaat

| Wat je ziet | Betekenis |
|---|---|
| JSON zoals hierboven | ✅ .NET werkt — ga door met de echte app |
| `500.19` of `500.21` fout | ❌ AspNetCoreModuleV2 ontbreekt — installeer .NET Hosting Bundle |
| `502.5` of blanco pagina | ❌ .NET runtime ontbreekt of verkeerde versie |
| `404` | ❌ Virtual Application niet correct ingesteld in IIS |

---

## Stap 4 – Opruimen

Na een geslaagde test verwijder je `wwwroot/dutch_tax_probe` van de server.
Die map is alleen bedoeld als snelle omgevingstest.

---

## Daarna: echte app deployen

Zie `dotnet/INSTALL_ON_WEBSITE_NL.md` → **Optie C** voor de volledige stap-voor-stap handleiding.
