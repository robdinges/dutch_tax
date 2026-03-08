# Lokaal draaien van de .NET app (macOS)

Deze handleiding is voor de .NET versie van de app in:

- `dotnet/DutchTax.Web`

## 1) Controleer of dotnet werkt

```bash
dotnet --version
```

Als je versie ziet (bijv. `10.0.103`), dan is het goed.

## 2) Starten met 1 commando (aanbevolen)

Ga naar de repository root (`dutch_tax`) en start:

```bash
./run-dotnet.sh
```

Belangrijk:
- Gebruik `./run-dotnet.sh` (met `./`)
- Zonder `./` krijg je vaak: `command not found`

## 3) Open de app

- `http://localhost:5000`

Snelle API check:

```bash
curl http://localhost:5000/api/income-types
```

## 4) Handmatig starten (alternatief)

```bash
cd dotnet/DutchTax.Web
DOTNET_CLI_HOME=/tmp/dotnet_home DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 dotnet restore -p:BaseIntermediateOutputPath=/tmp/dutchtax_obj/ -p:IntermediateOutputPath=/tmp/dutchtax_obj/obj/
DOTNET_CLI_HOME=/tmp/dotnet_home DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 dotnet run --no-restore -p:BaseIntermediateOutputPath=/tmp/dutchtax_obj/ -p:IntermediateOutputPath=/tmp/dutchtax_obj/obj/ -p:BaseOutputPath=/tmp/dutchtax_bin/
```

## 5) Veelvoorkomende fouten

### `zsh: command not found: dotnet`

- Herlaad shell:

```bash
source ~/.zshrc
rehash
```

- Test opnieuw:

```bash
dotnet --version
```

### `run-dotnet.sh: command not found`

- Je staat waarschijnlijk in de verkeerde map of mist `./`.
- Doe:

```bash
cd /Users/robvandererve/Documents/python_projects/dutch_tax
./run-dotnet.sh
```

### Framework mismatch (`net8.0` vs runtime)

- Deze repo gebruikt `net10.0`.
- Controleer in `dotnet/DutchTax.Web/DutchTax.Web.csproj` dat `TargetFramework` op `net10.0` staat.
