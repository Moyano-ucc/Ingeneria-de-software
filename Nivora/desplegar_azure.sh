#!/usr/bin/env bash
# Despliega Nivora en Azure App Service (Linux, plan gratuito F1).
#
# Uso, desde la carpeta Nivora y con la CLI de Azure instalada:
#   bash desplegar_azure.sh <nombre-unico-de-la-app> [region]
# Ejemplo:
#   bash desplegar_azure.sh nivora-pedro eastus2
#
# Se puede ejecutar varias veces: la primera crea los recursos y las
# siguientes solo vuelven a publicar el código. Publica lo que está
# confirmado en git (no sube .env, .venv ni archivos sin commit).
set -euo pipefail

APP_NAME="${1:?Uso: bash desplegar_azure.sh <nombre-unico-de-la-app> [region]}"
LOCATION="${2:-eastus2}"
RESOURCE_GROUP="${NIVORA_AZURE_GROUP:-nivora-rg}"
PLAN="${NIVORA_AZURE_PLAN:-nivora-plan}"
cd "$(dirname "$0")"

command -v az >/dev/null || {
    echo "Falta la CLI de Azure. Instálala con:"
    echo "  curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
    exit 1
}
az account show -o none 2>/dev/null || az login --use-device-code -o none

if [ -n "$(git status --porcelain -- .)" ]; then
    echo "Aviso: hay cambios sin commit en Nivora; no se publicarán."
fi

echo "1/5 Grupo de recursos y plan F1 (gratuito) en $LOCATION..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" -o none
if ! az appservice plan show -g "$RESOURCE_GROUP" -n "$PLAN" -o none 2>/dev/null; then
    az appservice plan create -g "$RESOURCE_GROUP" -n "$PLAN" \
        --is-linux --sku F1 --location "$LOCATION" -o none
fi

echo "2/5 Aplicación web $APP_NAME (Python 3.12)..."
if ! az webapp show -g "$RESOURCE_GROUP" -n "$APP_NAME" -o none 2>/dev/null; then
    az webapp create -g "$RESOURCE_GROUP" -p "$PLAN" -n "$APP_NAME" \
        --runtime "PYTHON:3.12" -o none
fi

echo "3/5 Configuración..."
settings=(
    "NIVORA_COOKIE_SECURE=1"
    "NIVORA_DATABASE_PATH=/home/data/nivora.db"
    "SCM_DO_BUILD_DURING_DEPLOYMENT=true"
    "WEB_CONCURRENCY=2"
)
# The secret key is generated only once: changing it would log everyone out.
existing_key="$(az webapp config appsettings list -g "$RESOURCE_GROUP" -n "$APP_NAME" \
    --query "[?name=='NIVORA_SECRET_KEY'].name" -o tsv)"
if [ -z "$existing_key" ]; then
    settings+=("NIVORA_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')")
fi
# Reuse the SMTP settings of this environment (e.g. Codespaces secrets).
for name in NIVORA_SMTP_HOST NIVORA_SMTP_PORT NIVORA_SMTP_USERNAME NIVORA_SMTP_PASSWORD NIVORA_SMTP_FROM; do
    if [ -n "${!name:-}" ]; then
        settings+=("$name=${!name}")
    fi
done
az webapp config appsettings set -g "$RESOURCE_GROUP" -n "$APP_NAME" \
    --settings "${settings[@]}" -o none
az webapp config set -g "$RESOURCE_GROUP" -n "$APP_NAME" \
    --startup-file "bash startup.sh" -o none
if [ -z "${NIVORA_SMTP_HOST:-}" ]; then
    echo "   Aviso: no hay NIVORA_SMTP_* en este entorno; los correos no funcionarán"
    echo "   hasta configurarlos en Azure (Configuración > Variables de entorno)."
fi

echo "4/5 Empaquetando el código confirmado en git..."
package="$(mktemp -d)/nivora.zip"
git archive --format=zip -o "$package" HEAD -- .

echo "5/5 Publicando (Azure instala las dependencias; puede tardar unos minutos)..."
az webapp deploy -g "$RESOURCE_GROUP" -n "$APP_NAME" \
    --src-path "$package" --type zip -o none
rm -f "$package"

echo
echo "Listo: https://$APP_NAME.azurewebsites.net"
echo "La primera carga puede tardar hasta un minuto (el plan gratuito se duerme)."
echo "Registros en vivo: az webapp log tail -g $RESOURCE_GROUP -n $APP_NAME"
