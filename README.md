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

4. Go to backend and read the Readme there, basically you only need to run
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
6. Import tools using ```wxo-openapi.json```

