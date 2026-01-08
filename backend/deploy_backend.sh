#!/bin/bash
set -e

echo "🚀 Deploying Docker Hub images to IBM Code Engine (us-south)"

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
CE_PROJECT_NAME="cc-6950005cap-vwjxu7pr-codeengine"
CE_REGION="us-south"
CONTAINER_PORT=8000

# Infrastructure sizing
CPU="2"
MEMORY="4G"
EPHEMERAL_STORAGE="4.4G"
MIN_INSTANCES=1
MAX_INSTANCES=10
CONCURRENCY=10

ENV_SECRET_NAME="app-env-secret"
ENV_FILE=".env"

# Apps in snake_case
APPS=( 
    # "bisma" 
    "feature_stores" 
    # "model_predictions" 
    )

MAX_RETRIES=1   # 🔥 only allow 1 retry

# --------------------------------------------------
# VALIDATION
# --------------------------------------------------
if [[ -z "$DOCKERHUB_USERNAME" ]]; then
  echo "❌ DOCKERHUB_USERNAME is not set"
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ $ENV_FILE not found"
  exit 1
fi

# --------------------------------------------------
# TARGET REGION & PROJECT
# --------------------------------------------------
ibmcloud target -r "$CE_REGION" >/dev/null

if ! ibmcloud ce project select --name "$CE_PROJECT_NAME" >/dev/null 2>&1; then
  echo "❌ Cannot access Code Engine project: $CE_PROJECT_NAME"
  exit 1
fi

echo "✅ Using Code Engine project: $CE_PROJECT_NAME"
echo ""

# --------------------------------------------------
# SYNC .env → SECRET
# --------------------------------------------------
echo "🔐 Syncing .env to Code Engine secret: $ENV_SECRET_NAME"

if ibmcloud ce secret get --name "$ENV_SECRET_NAME" >/dev/null 2>&1; then
  ibmcloud ce secret update \
    --name "$ENV_SECRET_NAME" \
    --from-env-file "$ENV_FILE"
else
  ibmcloud ce secret create \
    --name "$ENV_SECRET_NAME" \
    --from-env-file "$ENV_FILE"
fi

echo "✅ Secret synced"
echo ""

# --------------------------------------------------
# HELPER: SHOW LOGS & EVENTS
# --------------------------------------------------
show_debug_info () {
  local APP_NAME=$1

  echo ""
  echo "🚨 DEPLOYMENT FAILED FOR: $APP_NAME"
  echo "-----------------------------------"
  echo "📄 Application details:"
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

# --------------------------------------------------
# DEPLOY APPS WITH RETRY GUARD
# --------------------------------------------------
for app in "${APPS[@]}"; do
  CE_APP_NAME="${app//_/-}"
  IMAGE="docker.io/$DOCKERHUB_USERNAME/$app:latest"

  ATTEMPT=0
  SUCCESS=false

  while [[ $ATTEMPT -le $MAX_RETRIES ]]; do
    echo "🚀 Deploying $CE_APP_NAME (attempt $((ATTEMPT + 1)))"
    echo "   Image: $IMAGE"

    if ibmcloud ce application get --name "$CE_APP_NAME" >/dev/null 2>&1; then
      DEPLOY_CMD="update"
    else
      DEPLOY_CMD="create"
    fi

    set +e
    if [[ "$DEPLOY_CMD" == "update" ]]; then
      ibmcloud ce application update \
        --name "$CE_APP_NAME" \
        --image "$IMAGE" \
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
    echo "⚠️ Deploy failed, retrying..."
    sleep 5
  done

  if [[ "$SUCCESS" != "true" ]]; then
    show_debug_info "$CE_APP_NAME"
    echo "❌ Max retries exceeded. Stopping deployment."
    exit 1
  fi

  # --------------------------------------------------
  # SHOW APPLICATION URL
  # --------------------------------------------------
  APP_URL=$(ibmcloud ce application get --name "$CE_APP_NAME" \
    --output json | jq -r '.status.url')

  echo "✅ Successfully deployed: $CE_APP_NAME"
  echo "🌐 URL: $APP_URL"
  echo ""
done

echo "🎉 ALL APPLICATIONS DEPLOYED SUCCESSFULLY"
