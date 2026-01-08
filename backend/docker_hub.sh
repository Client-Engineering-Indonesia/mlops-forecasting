#!/bin/bash
set -e

echo "🚀 Starting Docker Hub rebuild & push process"

# --------------------------------------------------
# VALIDATE ENV VARIABLES
# --------------------------------------------------
if [[ -z "$DOCKERHUB_USERNAME" || -z "$DOCKERHUB_PAT" ]]; then
  echo "❌ Missing Docker Hub credentials"
  echo "👉 export DOCKERHUB_USERNAME=your_username"
  echo "👉 export DOCKERHUB_PAT=your_personal_access_token"
  exit 1
fi

echo "🔐 Docker Hub Username: $DOCKERHUB_USERNAME"
echo "🔑 Docker Hub PAT: ${DOCKERHUB_PAT:0:4}********"
echo ""

# --------------------------------------------------
# RESOLVE PROJECT PATHS (AUTO-DETECT)
# --------------------------------------------------
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -d "$BASE_DIR/backend/sub_apps" ]; then
  SUB_APPS_DIR="$BASE_DIR/backend/sub_apps"
elif [ -d "$BASE_DIR/sub_apps" ]; then
  SUB_APPS_DIR="$BASE_DIR/sub_apps"
else
  echo "❌ Could not find sub_apps directory"
  exit 1
fi

echo "📂 Sub apps directory: $SUB_APPS_DIR"
echo ""

# --------------------------------------------------
# CONFIG (snake_case app names)
# --------------------------------------------------
APPS=(
#   "bisma"
#   "feature_stores"
  "models_predictions"
)

# --------------------------------------------------
# REQUIRE jq
# --------------------------------------------------
if ! command -v jq >/dev/null 2>&1; then
  echo "❌ jq is required. Install with: brew install jq"
  exit 1
fi

# --------------------------------------------------
# GET DOCKER HUB JWT TOKEN
# --------------------------------------------------
echo "🔑 Authenticating to Docker Hub API..."

TOKEN=$(curl -s -X POST https://hub.docker.com/v2/users/login/ \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$DOCKERHUB_USERNAME\",
    \"password\": \"$DOCKERHUB_PAT\"
  }" | jq -r '.token')

if [[ -z "$TOKEN" || "$TOKEN" == "null" ]]; then
  echo "❌ Failed to retrieve Docker Hub JWT token"
  exit 1
fi

echo "✅ Docker Hub JWT token acquired"
echo ""

# --------------------------------------------------
# LOGIN TO DOCKER HUB (PODMAN)
# --------------------------------------------------
echo "🔑 Logging into Docker Hub with Podman..."
echo "$DOCKERHUB_PAT" | podman login docker.io \
  --username "$DOCKERHUB_USERNAME" \
  --password-stdin
echo "✅ Podman login successful"
echo ""

# --------------------------------------------------
# DELETE & RECREATE DOCKER HUB REPOS (SAFE)
# --------------------------------------------------
echo "🔥 Recreating Docker Hub repositories (clean state)..."

for app in "${APPS[@]}"; do
  echo "➡️  Processing repo: $app"

  DELETE_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X DELETE \
    -H "Authorization: Bearer $TOKEN" \
    "https://hub.docker.com/v2/repositories/$DOCKERHUB_USERNAME/$app/")

  if [[ "$DELETE_CODE" == "204" || "$DELETE_CODE" == "202" ]]; then
    echo "🗑️  Delete requested (HTTP $DELETE_CODE): $app"
  elif [[ "$DELETE_CODE" == "404" ]]; then
    echo "ℹ️  Repo not found (ok): $app"
  else
    echo "❌ Failed to delete repo $app (HTTP $DELETE_CODE)"
    exit 1
  fi

  echo "⏳ Waiting for repo deletion to complete..."
  for i in {1..12}; do
    CHECK_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
      -H "Authorization: Bearer $TOKEN" \
      "https://hub.docker.com/v2/repositories/$DOCKERHUB_USERNAME/$app/")

    if [[ "$CHECK_CODE" == "404" ]]; then
      echo "✅ Repo fully deleted: $app"
      break
    fi

    if [[ "$i" == "12" ]]; then
      echo "❌ Repo deletion timed out: $app"
      exit 1
    fi

    sleep 5
  done

  CREATE_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST \
    "https://hub.docker.com/v2/repositories/$DOCKERHUB_USERNAME/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{
      \"name\": \"$app\",
      \"is_private\": false
    }")

  if [[ "$CREATE_CODE" == "201" || "$CREATE_CODE" == "409" ]]; then
    echo "✅ Repo ready: $app"
  else
    echo "❌ Failed to create repo $app (HTTP $CREATE_CODE)"
    exit 1
  fi

  echo ""
done

# --------------------------------------------------
# BUILD & PUSH IMAGES (FORCE amd64)
# --------------------------------------------------
echo "🔨 Building and pushing images (linux/amd64)..."

for app in "${APPS[@]}"; do
  APP_DIR="$SUB_APPS_DIR/$app"
  IMAGE="docker.io/$DOCKERHUB_USERNAME/$app:latest"

  if [ ! -d "$APP_DIR" ]; then
    echo "❌ App directory not found: $APP_DIR"
    exit 1
  fi

  echo "🔨 Building image: $IMAGE"
  podman build \
    --platform linux/amd64 \
    -t "$IMAGE" \
    "$APP_DIR"

  echo "📤 Pushing image: $IMAGE"
  podman push "$IMAGE"

  echo "✅ Successfully pushed: $IMAGE"
  echo ""
done

echo "🎉 ALL DONE — Images rebuilt (amd64) & pushed to Docker Hub successfully!"
