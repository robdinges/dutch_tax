#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="$ROOT_DIR/dotnet/DutchTax.Web/DutchTax.Web.csproj"

export DOTNET_CLI_HOME="${DOTNET_CLI_HOME:-/tmp/dotnet_home}"
export DOTNET_SKIP_FIRST_TIME_EXPERIENCE="${DOTNET_SKIP_FIRST_TIME_EXPERIENCE:-1}"

OBJ_BASE="${OBJ_BASE:-/tmp/dutchtax_obj/}"
OBJ_INTERMEDIATE="${OBJ_INTERMEDIATE:-/tmp/dutchtax_obj/obj/}"
BIN_BASE="${BIN_BASE:-/tmp/dutchtax_bin/}"

mkdir -p "$DOTNET_CLI_HOME" "$OBJ_BASE" "$OBJ_INTERMEDIATE" "$BIN_BASE"

dotnet restore "$PROJECT" \
  -p:BaseIntermediateOutputPath="$OBJ_BASE" \
  -p:IntermediateOutputPath="$OBJ_INTERMEDIATE"

dotnet run --project "$PROJECT" --no-restore \
  -p:BaseIntermediateOutputPath="$OBJ_BASE" \
  -p:IntermediateOutputPath="$OBJ_INTERMEDIATE" \
  -p:BaseOutputPath="$BIN_BASE"
