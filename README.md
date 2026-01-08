# mlops-forecasting

1. Deploy PostgreSQL

2. Create .env file with variables as below:

```
# watsonx Orchestrate
WXO_API_KEY=
AGENT_ID=
TENANT_ID=
REGION_CODE=

# Postgres
POSTGRES_HOST=
POSTGRES_PORT=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=

# IBM Cloud Object Storage 
COS_API_KEY=
COS_SERVICE_INSTANCE_ID=
COS_ENDPOINT_URL=
COS_BUCKET_NAME=
```

3. Put .env into folder ```backend/sub_apps/bisma```, ```backend/sub_apps/feature_stores``` and ```backend/sub_apps/models_predictions``` and deploy them all

4. Go to backend and read the Readme there, basically you only need to run, make sure to change the project name of the code engine instance that you have.
```
chmod +x dockher_hub.sh
chmod +x deploy_backend.sh

./dockher_hub.sh
./deploy_backend.sh
```

5. Import watsonx orchestrate agents by log in to your watsonx.orchestrate account, create an agent
```
Agent Name: AI_DS_DE_Agent
Descirptions: xxxxx
```
6. Import tools using ```wxo-openapi.json``` but you need to change the URL of the feature store from your ./deployed_backend.sh in the openapi.json file


7. Set up the front end by adding this .env template:
```
REACT_APP_API_URL=http://127.0.0.1:8000
REACT_APP_API_URL2=http://127.0.0.1:8001
REACT_APP_API_URL3=http://127.0.0.1:8002

# IBM Cloud watsonx Orchestrate
SERVICE_URL=https://api.<region>.watson-orchestrate.cloud.ibm.com #<region> can be us-south, ap-south, dl and else. 
API_KEY=your_api_key_here
ENV_NAME=ibmcloud_env

# OpenAPI JSON spec path (relative to script)
OPENAPI_JSON=./openapi/my_api.json

# Connection (optional)
CONNECTION_APP_ID=your_connection_app_id

# Agent to attach tools to
AGENT_NAME=my_orchestrate_agent

# Web app specifics
APP_ROOT=./my-app
```
You can get the URL after finisihing the deploy_backend.sh


8. npm run and npm start

#### This Porcess is not necessary
8. Activate Conda or Miniconda or Venv since we need to install pip for watsonx orchestrate


