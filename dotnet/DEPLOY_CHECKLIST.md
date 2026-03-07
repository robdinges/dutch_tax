# Deploy Checklist (.NET + SFTP)

Gebruik deze checklist bij elke nieuwe release van `DutchTax.Web`.

## 1) Build / publish lokaal

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
- `wwwroot/`

## 2) Upload via VS Code SFTP Extension

1. Open Command Palette.
2. Run `SFTP: Upload Folder`.
3. Selecteer `dotnet/DutchTax.Web/publish`.
4. Wacht tot upload volledig klaar is (geen fouten in Output panel).

## 3) Herstart app op server

- Linux/systemd: `sudo systemctl restart dutchtax`
- IIS: recycle app pool / restart website

## 4) Post-deploy checks

Controleer in browser:
- `/` laadt zonder 500-fout
- `/api/income-types` geeft `200` + JSON
- `/api/asset-types` geeft `200` + JSON
- `/api/calculate` werkt via formulier

## 5) Foutdiagnose

- Linux logs: `journalctl -u dutchtax -f`
- Nginx error log: `/var/log/nginx/error.log`
- IIS: Event Viewer + stdout logs

## 6) Security quick check

- Geen gevoelige gegevens in `.vscode/sftp.json` committen
- Liefst SFTP met `privateKey` i.p.v. wachtwoord
- Wachtwoorden periodiek roteren
