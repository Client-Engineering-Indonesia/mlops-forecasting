#!/usr/bin/env bash
set -euo pipefail

# ----------------------------------
# 1️⃣ Upgrade/install ADK CLI
# ----------------------------------
echo "Installing/upgrading IBM watsonx Orchestrate ADK..."
pip install --upgrade ibm-watsonx-orchestrate

# ----------------------------------
# 2️⃣ Load .env configuration
# ----------------------------------
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
  echo "Loaded .env variables."
else
  echo "❌ .env file not found!"
  exit 1
fi

# Validate required variables
: "${SERVICE_URL:?Need SERVICE_URL in .env}"
: "${API_KEY:?Need API_KEY in .env}"
: "${ENV_NAME:?Need ENV_NAME in .env}"
: "${OPENAPI_JSON:?Need OPENAPI_JSON in .env}"
: "${AGENT_NAME:?Need AGENT_NAME in .env}"
: "${APP_ROOT:?Need APP_ROOT in .env}"

TARGET_HTML="$APP_ROOT/public/index.html"

# ----------------------------------
# 3️⃣ Add or activate ADK environment
# ----------------------------------
echo "Checking existing ADK environments..."
EXISTS=$(orchestrate env list | grep -w "$ENV_NAME" || true)
echo "this is the serviuce url $SERVICE_URL"

if [ -z "$EXISTS" ]; then
  echo "Environment '$ENV_NAME' not found — adding & activating..."
  # Add ADK remote environment for IBM Cloud
  echo "$API_KEY" | orchestrate env add --name "$ENV_NAME" \
    -u "$SERVICE_URL" \
    --type ibm_iam \
    --activate
else
  echo "Environment '$ENV_NAME' already exists — activating it..."
  orchestrate env activate "$ENV_NAME"
fi

echo "--- Active environments ---"
orchestrate env list

# ----------------------------------
# 4️⃣ Import OpenAPI JSON as tool
# ----------------------------------
echo "Importing OpenAPI spec: $OPENAPI_JSON"
if [[ -z "${CONNECTION_APP_ID:-}" ]]; then
  orchestrate tools import -k openapi -f "$OPENAPI_JSON"
else
  orchestrate tools import -k openapi -f "$OPENAPI_JSON" 
fi

echo "--- Tools imported ---"
orchestrate tools list

# ----------------------------------
# 5️⃣ Generate embed snippet safely
# ----------------------------------
echo "Generating embed snippet for agent: $AGENT_NAME"
RAW_SNIPPET=$(orchestrate channels webchat embed --agent-name "$AGENT_NAME" 2>&1 || true)

if [[ -z "$RAW_SNIPPET" ]]; then
  echo "❌ Failed to generate embed snippet — verify the agent exists and environment is correct"
  echo "Raw output was:"
  echo "$RAW_SNIPPET"
  exit 1
fi

EMBED_SNIPPET="$RAW_SNIPPET"
echo "Embed snippet captured."

# ----------------------------------
# 6️⃣ Update index.html
# ----------------------------------
echo "Updating HTML at: $TARGET_HTML"
cat > "$TARGET_HTML" <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Chat with $AGENT_NAME</title>
  $EMBED_SNIPPET
</head>
<body>
  <div id="chat-root"></div>
</body>
</html>
EOF

echo "HTML updated successfully."

# ----------------------------------
# 7️⃣ Install & build web app
# ----------------------------------
echo "Installing dependencies..."
npm install --prefix "$APP_ROOT"

echo "Building web app..."
npm run build --prefix "$APP_ROOT"

echo "🎉 Deployment complete!"
