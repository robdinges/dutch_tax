# Installatie op je website (.NET versie)

Deze handleiding legt uit hoe je `dotnet/DutchTax.Web` live zet.

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

    location / {
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

- Open `https://jouwdomein.nl`
- Controleer in browser network tab dat `/api/income-types` en `/api/calculate` 200 teruggeven.

## Veelvoorkomende issues

- `dotnet: command not found` → .NET runtime/SDK ontbreekt op server.
- 502 via Nginx → app draait niet of luistert op andere poort.
- 500 fout → check logs:
  - Linux: `journalctl -u dutchtax -f`
  - IIS: Event Viewer + stdout logs.
