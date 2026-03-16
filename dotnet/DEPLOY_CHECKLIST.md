# Deploy Checklist (.NET + SFTP)

Gebruik deze checklist bij elke nieuwe release van `DutchTax.Web`.

## 0) Via GitHub Actions (aanbevolen — geen lokale build nodig)

Push naar `main` of start de workflow handmatig:
**GitHub → Actions → Deploy DutchTax.Probe naar externe site → Run workflow**

De workflow bouwt en uploadt `DutchTax.Probe` automatisch.
Vereiste secrets: `FTP_SERVER`, `FTP_USERNAME`, `FTP_PASSWORD`, `FTP_PROBE_DIR`.
Zie `dotnet/DutchTax.Probe/README.md` voor de volledige secretsinstructie.

---

## 1) Build / publish lokaal

### 1a) DutchTax.Probe (snelle omgevingstest)

Normaal:

```bash
cd dotnet/DutchTax.Probe
dotnet publish -c Release -r win-x64 --self-contained false -o ./publish
```

Op macOS: als je een permissiefout krijgt op de NuGet-cache, gebruik de `/tmp` workaround:

```bash
rm -rf /tmp/DutchTax.Probe
cp -R ./dotnet/DutchTax.Probe /tmp/DutchTax.Probe
DOTNET_CLI_HOME=/tmp/dotnet_home DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 \
  /usr/local/Cellar/dotnet/10.0.103/libexec/dotnet publish /tmp/DutchTax.Probe \
  -c Release -r win-x64 --self-contained false -o /tmp/DutchTax.Probe/publish
rm -rf ./dotnet/DutchTax.Probe/publish
mkdir -p ./dotnet/DutchTax.Probe/publish
cp -R /tmp/DutchTax.Probe/publish/. ./dotnet/DutchTax.Probe/publish/
```

### 1b) DutchTax.Web (volledige app)

Gebruik op deze Mac het absolute dotnet-pad:

```bash
DOTNET_CLI_HOME=/tmp/dotnet_home DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 /usr/local/opt/dotnet/libexec/dotnet publish /tmp/DutchTax.Web -c Release -o /tmp/DutchTax.Web/publish
```

Als je direct uit de repo publiceert en permissieproblemen krijgt, gebruik de `/tmp` workaround:

```bash
rm -rf /tmp/DutchTax.Web
cp -R ./dotnet/DutchTax.Web /tmp/DutchTax.Web
DOTNET_CLI_HOME=/tmp/dotnet_home DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 /usr/local/opt/dotnet/libexec/dotnet publish /tmp/DutchTax.Web -c Release -o /tmp/DutchTax.Web/publish
rm -rf ./dotnet/DutchTax.Web/publish
mkdir -p ./dotnet/DutchTax.Web/publish
cp -R /tmp/DutchTax.Web/publish/. ./dotnet/DutchTax.Web/publish/
```

Controleer dat deze bestanden bestaan in `dotnet/DutchTax.Web/publish`:
- `DutchTax.Web.dll`
- `DutchTax.Web.deps.json`
- `DutchTax.Web.runtimeconfig.json`
- `web.config`
- `wwwroot/`

## 2a) Upload via FileZilla (Windows shared hosting)

1. Open FileZilla en verbind met je server.
2. Navigeer op de server naar `wwwroot/dutch_tax` (maak de map aan als die nog niet bestaat).
3. Navigeer op je eigen pc naar `dotnet/DutchTax.Web/publish`.
4. Selecteer alle bestanden en mappen in `publish/` (Ctrl+A).
5. Upload ze naar `wwwroot/dutch_tax` op de server.
6. Controleer dat `web.config` aanwezig is in `wwwroot/dutch_tax/` na het uploaden.

> In IIS: zorg dat `dutch_tax` is ingesteld als **Virtual Application** met Application Pool op **No Managed Code**.

## 2b) Upload via VS Code SFTP Extension

1. Open Command Palette.
2. Run `SFTP: Upload Folder`.
3. Selecteer `dotnet/DutchTax.Web/publish`.
4. Wacht tot upload volledig klaar is (geen fouten in Output panel).

## 3) Herstart app op server

- Linux/systemd: `sudo systemctl restart dutchtax`
- IIS: recycle app pool / restart website (of via hostingpanel)

## 4) Post-deploy checks

Controleer in browser:
- `/dutch_tax/` laadt zonder 500-fout
- `/dutch_tax/api/income-types` geeft `200` + JSON
- `/dutch_tax/api/calculate` werkt via formulier

## 5) Foutdiagnose

- Linux logs: `journalctl -u dutchtax -f`
- Nginx error log: `/var/log/nginx/error.log`
- IIS stdout logs: `wwwroot/dutch_tax/logs/stdout_*.log` (zet `stdoutLogEnabled="true"` in `web.config`)
- IIS: Event Viewer → Windows Logs → Application

## 6) Security quick check

- Geen gevoelige gegevens in `.vscode/sftp.json` committen
- Liefst SFTP met `privateKey` i.p.v. wachtwoord
- Wachtwoorden periodiek roteren
