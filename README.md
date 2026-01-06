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

4. Import watsonx orchestrate agents

5. Import tools using ```wxo-openapi.json```

