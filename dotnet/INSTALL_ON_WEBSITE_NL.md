# Installatie op je website (.NET versie)

Deze handleiding legt uit hoe je `dotnet/DutchTax.Web` live zet.

---

## Optie C: Windows shared hosting (IIS) via FileZilla (meest voorkomend)

Dit is de meest gebruikte methode als je een gewone webhostingpakket hebt met een `wwwroot` map.

### Vereiste op de server

- .NET 10 Hosting Bundle moet geïnstalleerd zijn op de server.
- Vraag dit na bij je hostingprovider als je er niet zeker van bent.

> **Aanbevolen: doe eerst een snelle omgevingstest (zie C0) voordat je de volledige app uploadt.**

### C0. Eerst testen: minimale probe app uploaden

Voordat je de volledige app uploadt, is het verstandig om met een kleine testapp te controleren
of de server überhaupt .NET ondersteunt. Dit bespaart veel debugtijd.

**Stap 1** — Publiceer de probe app:

```bash
cd dotnet/DutchTax.Probe
dotnet publish -c Release -r win-x64 --self-contained false -o ./publish
```

**Stap 2** — Upload via FileZilla naar `wwwroot/dutch_tax_probe` (nieuwe tijdelijke map).

**Stap 3** — Stel `dutch_tax_probe` in als Virtual Application in IIS / je hostingpanel.

**Stap 4** — Test in je browser:

```
https://www.jouwedomein.nl/dutch_tax_probe/probe
```

Verwacht antwoord:

```json
{ "status": "ok", "message": ".NET draait correct op deze server.", "dotnet": "10.x.x" }
```

| Wat je ziet | Actie |
|---|---|
| JSON zoals hierboven | ✅ Ga door naar **C1** |
| `500.19` / `500.21` fout | ❌ Installeer .NET 10 Hosting Bundle op de server |
| `502.5` of blanco pagina | ❌ Verkeerde .NET versie — controleer of Hosting Bundle 10 is |
| `404` | ❌ Virtual Application niet correct ingesteld — zie C3 |

Na een geslaagde test kun je `dutch_tax_probe` van de server verwijderen.
Zie ook `dotnet/DutchTax.Probe/README.md` voor meer uitleg.

### C1. Publiceren op je eigen pc

Open een terminal (PowerShell of Command Prompt) en ga naar de projectmap:

```bash
cd dotnet/DutchTax.Web
```

Publiceer de app voor Windows:

```bash
dotnet publish -c Release -r win-x64 --self-contained false -o ./publish
```

Na het publiceren staan alle benodigde bestanden in `dotnet/DutchTax.Web/publish/`.

Controleer of de volgende bestanden aanwezig zijn:

- `DutchTax.Web.dll`
- `DutchTax.Web.deps.json`
- `DutchTax.Web.runtimeconfig.json`
- `web.config`
- `wwwroot/`

### C2. Uploaden via FileZilla

1. Open FileZilla en verbind met je server (SFTP of FTP).
2. Navigeer aan de rechterkant (server) naar `wwwroot/dutch_tax`.
   - Als de map `dutch_tax` nog niet bestaat, maak hem aan via rechtermuisklik → **Aanmaken map**.
3. Navigeer aan de linkerkant (jouw pc) naar de `publish/` map van het project.
4. Selecteer **alle bestanden en mappen** in `publish/` (Ctrl+A).
5. Sleep ze naar `wwwroot/dutch_tax` op de server, of klik rechts → **Uploaden**.

> **Let op:** Kopieer de *inhoud* van `publish/` (niet de map zelf) naar `wwwroot/dutch_tax`.
> Na het uploaden staat `web.config` direct in `wwwroot/dutch_tax/`, niet in een submap.

### C3. IIS instelling controleren

In je hostingpanel (bijv. Plesk, cPanel of direct in IIS):

1. Zorg dat `dutch_tax` een **Virtual Application** is (niet alleen een map).
   - In Plesk: Maak een nieuwe webtoepassing aan op het pad `/dutch_tax`.
   - In IIS: Rechtermuisklik op de map → **Convert to Application**.
2. Stel de **Application Pool** in op **No Managed Code** (want .NET beheert zichzelf).
3. Geef de IIS-gebruiker (`IIS_IUSRS` of `IUSR`) **lees- en schrijfrechten** op de map.

### C4. App testen

Open je browser en ga naar:

```
https://www.jouwedomein.nl/dutch_tax/
```

Snelle health check (geeft JSON terug als de app draait):

```
https://www.jouwedomein.nl/dutch_tax/api/health
```

Controleer ook de API:

```
https://www.jouwedomein.nl/dutch_tax/api/income-types
```

Dit moet een JSON-response geven. Als je een 500-fout of een lege pagina ziet, zie **Veelvoorkomende issues** onderaan.

---

## 1) Eenmalige voorbereiding

1. Installeer .NET 10 SDK op je ontwikkelmachine.
2. Installeer .NET 10 Hosting Bundle op je server (Windows/IIS) of .NET Runtime 10 op Linux.
3. Zorg dat poort 80/443 open staat en je domein naar de server wijst.

## 2) Publiceren vanaf je Mac

Ga naar de projectmap:

```bash
cd dotnet/DutchTax.Web
```

### Linux server publiceren

```bash
dotnet publish -c Release -r linux-x64 --self-contained false -o ./publish
```

### Windows server publiceren

```bash
dotnet publish -c Release -r win-x64 --self-contained false -o ./publish
```

Upload daarna alle bestanden uit `publish/` naar je server.

---

## Optie A: Linux + Nginx + systemd (aanbevolen)

### A1. App uploaden

Kopieer `publish/` naar bijvoorbeeld:

- `/var/www/dutchtax`

### A2. systemd service maken

Bestand: `/etc/systemd/system/dutchtax.service`

```ini
[Unit]
Description=Dutch Tax .NET App
After=network.target

[Service]
WorkingDirectory=/var/www/dutchtax
ExecStart=/usr/bin/dotnet /var/www/dutchtax/DutchTax.Web.dll
Restart=always
RestartSec=10
KillSignal=SIGINT
SyslogIdentifier=dutchtax
User=www-data
Environment=ASPNETCORE_ENVIRONMENT=Production
Environment=ASPNETCORE_URLS=http://127.0.0.1:5005
Environment=PATH_BASE=/dutch_tax

[Install]
WantedBy=multi-user.target
```

Activeer service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable dutchtax
sudo systemctl start dutchtax
sudo systemctl status dutchtax
```

### A3. Nginx reverse proxy

Bestand: `/etc/nginx/sites-available/dutchtax`

```nginx
server {
    listen 80;
    server_name jouwdomein.nl www.jouwdomein.nl;

    location /dutch_tax/ {
        proxy_pass         http://127.0.0.1:5005;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection keep-alive;
        proxy_set_header   Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

Enable + reload:

```bash
sudo ln -s /etc/nginx/sites-available/dutchtax /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### A4. HTTPS toevoegen

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d jouwdomein.nl -d www.jouwdomein.nl
```

---

## Optie B: Windows Server + IIS

1. Installeer .NET Hosting Bundle (belangrijk).
2. Maak in IIS een nieuwe site, physical path naar je `publish` map.
3. Application Pool: `No Managed Code`.
4. Geef IIS-gebruiker lees/schrijfrechten op de map.
5. Start de site.

IIS gebruikt `aspNetCore` module automatisch om `DutchTax.Web.dll` te starten.

---

## 3) Updaten na wijzigingen

1. Nieuwe publish draaien.
2. Bestanden op server vervangen.
3. Herstarten:
   - Linux: `sudo systemctl restart dutchtax`
   - IIS: recycle app pool of restart site.

## 4) Gezondheid-check

Na deploy:

- Open `https://www.vandererve.com/dutch_tax/`
- Snelle check: `https://www.vandererve.com/dutch_tax/api/health` → moet `{"status":"ok"}` teruggeven.
- Controleer in browser network tab dat `/dutch_tax/api/income-types` en `/dutch_tax/api/calculate` 200 teruggeven.

## Veelvoorkomende issues

- `dotnet: command not found` → .NET runtime/SDK ontbreekt op server.
- `500.19` of `500.21` (IIS) → AspNetCoreModuleV2 ontbreekt — installeer .NET 10 Hosting Bundle.
- `502.5` of blanco pagina → verkeerde .NET versie of `web.config` klopt niet.
- `404` op `/dutch_tax/` → `dutch_tax` is niet ingesteld als Virtual Application in IIS.
- 502 via Nginx → app draait niet of luistert op andere poort.
- 500 fout → check logs:
  - Linux: `journalctl -u dutchtax -f`
  - IIS stdout logs: zet `stdoutLogEnabled="true"` in `web.config`, herstart, kijk in `wwwroot/dutch_tax/logs/`.
