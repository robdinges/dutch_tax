# DutchTax.Probe — minimale .NET test

Gebruik dit project om te controleren of jouw hostingomgeving .NET ondersteunt,
**voordat** je de volledige `DutchTax.Web` app uploadt.

---

## Stap 1 – Publiceren

### Optie A: via GitHub Actions (aanbevolen)

Push een wijziging naar `main` of start de workflow handmatig via
**Actions → Deploy DutchTax.Probe naar externe site → Run workflow**.
De workflow bouwt en uploadt de app automatisch zonder dat je lokaal
hoeft te publiceren.

Vereiste GitHub Secrets (éénmalig instellen via Settings → Secrets → Actions):

| Secret | Beschrijving |
|--------|--------------|
| `FTP_SERVER` | Hostname van je FTP-server (bijv. `ftp.vandererve.com`) |
| `FTP_USERNAME` | FTP-gebruikersnaam |
| `FTP_PASSWORD` | FTP-wachtwoord |
| `FTP_PROBE_DIR` | Serverpad waar de probe naartoe moet (bijv. `wwwroot/dutch_tax_probe/`) |

### Optie B: lokaal publiceren (Windows / Linux)

```bash
cd dotnet/DutchTax.Probe
dotnet publish -c Release -r win-x64 --self-contained false -o ./publish
```

### Optie C: lokaal publiceren op macOS (permissie-workaround)

Op macOS kan `dotnet publish` falen met een permissiefout op de NuGet-cache:

```
Access to the path '/Users/.../.nuget/packages/.../...' is denied.
Operation not permitted
```

Gebruik dan de `/tmp`-workaround:

```bash
rm -rf /tmp/DutchTax.Probe
cp -R ./dotnet/DutchTax.Probe /tmp/DutchTax.Probe
DOTNET_CLI_HOME=/tmp/dotnet_home \
DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 \
/usr/local/opt/dotnet/libexec/dotnet publish /tmp/DutchTax.Probe \
  -c Release -r win-x64 --self-contained false \
  -o /tmp/DutchTax.Probe/publish
rm -rf ./dotnet/DutchTax.Probe/publish
mkdir -p ./dotnet/DutchTax.Probe/publish
cp -R /tmp/DutchTax.Probe/publish/. ./dotnet/DutchTax.Probe/publish/
```

Als de `/usr/local/opt/dotnet`-locatie niet klopt, gebruik dan het pad dat je terugkrijgt
van `which dotnet` of het Homebrew-Cellar pad (bijv.
`/usr/local/Cellar/dotnet/10.0.103/libexec/dotnet`).

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
