#!/bin/bash
set -e

echo "🚀 Deploying Docker Hub images to IBM Code Engine (us-south)"

# ==================================================
# CONFIGURATION
# ==================================================
CE_PROJECT_NAME="cc-6950005cap-vwjxu7pr-codeengine"
CE_REGION="us-south"
CONTAINER_PORT=8000

# Infrastructure sizing (NOT low)
CPU="2"
MEMORY="4G"
EPHEMERAL_STORAGE="2.4G"
MIN_INSTANCES=1
MAX_INSTANCES=10
CONCURRENCY=10

# Secrets
ENV_SECRET_NAME="app-env-secret"
ENV_FILE=".env"
REGISTRY_SECRET_NAME="dockerhub-registry"

# Apps in snake_case (Docker image / repo names)
APPS=(
    "bisma"
    "feature_stores"
    "models_predictions"
)

MAX_RETRIES=1

# ==================================================
# VALIDATION
# ==================================================
if [[ -z "$DOCKERHUB_USERNAME" || -z "$DOCKERHUB_PAT" ]]; then
  echo "❌ DOCKERHUB_USERNAME or DOCKERHUB_PAT not set"
  echo "👉 export DOCKERHUB_USERNAME=your_username"
  echo "👉 export DOCKERHUB_PAT=your_dockerhub_pat"
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ $ENV_FILE not found"
  exit 1
fi

# ==================================================
# TARGET REGION & PROJECT
# ==================================================
ibmcloud target -r "$CE_REGION" >/dev/null

if ! ibmcloud ce project select --name "$CE_PROJECT_NAME" >/dev/null 2>&1; then
  echo "❌ Cannot access Code Engine project: $CE_PROJECT_NAME"
  exit 1
fi

echo "✅ Using Code Engine project: $CE_PROJECT_NAME"
echo ""

# ==================================================
# CREATE / UPDATE DOCKER HUB REGISTRY SECRET
# ==================================================
echo "🔐 Syncing Docker Hub registry credentials"

if ibmcloud ce registry get --name "$REGISTRY_SECRET_NAME" >/dev/null 2>&1; then
  ibmcloud ce registry update \
    --name "$REGISTRY_SECRET_NAME" \
    --server docker.io \
    --username "$DOCKERHUB_USERNAME" \
    --password "$DOCKERHUB_PAT"
else
  ibmcloud ce registry create \
    --name "$REGISTRY_SECRET_NAME" \
    --server docker.io \
    --username "$DOCKERHUB_USERNAME" \
    --password "$DOCKERHUB_PAT"
fi

echo "✅ Registry secret ready"
echo ""

# ==================================================
# CREATE / UPDATE ENV SECRET FROM .env
# ==================================================
echo "🔐 Syncing .env to Code Engine secret"

if ibmcloud ce secret get --name "$ENV_SECRET_NAME" >/dev/null 2>&1; then
  ibmcloud ce secret update \
    --name "$ENV_SECRET_NAME" \
    --from-env-file "$ENV_FILE"
else
  ibmcloud ce secret create \
    --name "$ENV_SECRET_NAME" \
    --from-env-file "$ENV_FILE"
fi

echo "✅ Env secret ready"
echo ""

# ==================================================
# HELPER: SHOW DEBUG INFO
# ==================================================
show_debug_info () {
  local APP_NAME=$1

  echo ""
  echo "🚨 DEPLOYMENT FAILED FOR: $APP_NAME"
  echo "----------------------------------"

  echo "📄 Application status:"
  ibmcloud ce application get --name "$APP_NAME" || true

  echo ""
  echo "📜 Error logs:"
  ibmcloud ce application logs \
    --name "$APP_NAME" \
    --severity error || true

  echo ""
  echo "📢 Events:"
  ibmcloud ce application events --name "$APP_NAME" || true
  echo ""
}

# ==================================================
# DEPLOY APPLICATIONS (WITH RETRY GUARD)
# ==================================================
for app in "${APPS[@]}"; do
  CE_APP_NAME="${app//_/-}"
  IMAGE="docker.io/$DOCKERHUB_USERNAME/$app:latest"

  ATTEMPT=0
  SUCCESS=false

  while [[ $ATTEMPT -le $MAX_RETRIES ]]; do
    echo "🚀 Deploying $CE_APP_NAME (attempt $((ATTEMPT + 1)))"
    echo "   Image: $IMAGE"

    if ibmcloud ce application get --name "$CE_APP_NAME" >/dev/null 2>&1; then
      ACTION="update"
    else
      ACTION="create"
    fi

    set +e
    if [[ "$ACTION" == "update" ]]; then
      ibmcloud ce application update \
        --name "$CE_APP_NAME" \
        --image "$IMAGE" \
        --registry-secret "$REGISTRY_SECRET_NAME" \
        --port "$CONTAINER_PORT" \
        --cpu "$CPU" \
        --memory "$MEMORY" \
        --ephemeral-storage "$EPHEMERAL_STORAGE" \
        --min-scale "$MIN_INSTANCES" \
        --max-scale "$MAX_INSTANCES" \
        --concurrency "$CONCURRENCY" \
        --env-from-secret "$ENV_SECRET_NAME"
    else
      ibmcloud ce application create \
        --name "$CE_APP_NAME" \
        --image "$IMAGE" \
        --registry-secret "$REGISTRY_SECRET_NAME" \
        --port "$CONTAINER_PORT" \
        --cpu "$CPU" \
        --memory "$MEMORY" \
        --ephemeral-storage "$EPHEMERAL_STORAGE" \
        --min-scale "$MIN_INSTANCES" \
        --max-scale "$MAX_INSTANCES" \
        --concurrency "$CONCURRENCY" \
        --env-from-secret "$ENV_SECRET_NAME"
    fi
    RESULT=$?
    set -e

    if [[ $RESULT -eq 0 ]]; then
      SUCCESS=true
      break
    fi

    ATTEMPT=$((ATTEMPT + 1))
    echo "⚠️ Deployment failed, retrying..."
    sleep 5
  done

  if [[ "$SUCCESS" != "true" ]]; then
    show_debug_info "$CE_APP_NAME"
    echo "❌ Max retries exceeded. Stopping all deployments."
    exit 1
  fi

  # ------------------------------------------------
  # SHOW APPLICATION URL
  # ------------------------------------------------
  APP_URL=$(ibmcloud ce application get \
    --name "$CE_APP_NAME" \
    --output json | jq -r '.status.url')

  echo "✅ Successfully deployed: $CE_APP_NAME"
  echo "🌐 URL: $APP_URL"
  echo ""
done

echo "🎉 ALL APPLICATIONS DEPLOYED SUCCESSFULLY"
