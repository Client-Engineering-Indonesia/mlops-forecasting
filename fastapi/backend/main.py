from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import random

# Import Service Layer
from backend.services import data_service

app = FastAPI(title="ML Lifecycle API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Types / Models ---

from pydantic import BaseModel, Field

# ... (Previous imports)

class FeatureStore(BaseModel):
    id: str = Field(..., example="fs-123")
    name: str = Field(..., example="Credit Score Features")
    description: str = Field(..., example="Features for credit scoring model")
    offline_dataset_path: str = Field(..., example="s3://bucket/path/to/data.csv")
    created_at: str = Field(..., example="2023-10-27T10:00:00")

class Dataset(BaseModel):
    id: str = Field(..., example="d-123")
    name: str = Field(..., example="raw_data.csv")
    filename: str = Field(..., example="raw_data.csv")
    has_engineered: bool = Field(..., example=False)
    created_at: str = Field(..., example="2023-10-27T10:00:00")

class Project(BaseModel):
    id: str = Field(..., example="p1")
    name: str = Field(..., example="Credit Risk Model")

class DroppedFeature(BaseModel):
    name: str = Field(..., example="feature_correlation_too_high")
    reason: str = Field(..., example="correlation > 0.9")

class Model(BaseModel):
    id: str = Field(..., example="m-123")
    name: str = Field(..., example="Model-m-123")
    project_id: str = Field(..., example="p1")
    dataset_id: str = Field(..., example="d-123")
    task_type: str = Field(..., example="classification")
    target_column: str = Field(..., example="default_flag")
    metrics: Dict[str, float] = Field(..., example={"accuracy": 0.85, "f1": 0.82})
    cos_path: Optional[str] = Field(None, example="cos://bucket/key")

class TrainRequest(BaseModel):
    dataset_id: str = Field(..., example="d-123")
    selection_id: str = Field(..., example="fs-run-123")
    project_id: str = Field(..., example="p1")
    task_type: str = Field(..., example="classification")

class FeatureSelectionRequest(BaseModel):
    target_column: str = Field(..., example="Value_Next_7D")
    top_k: int = Field(10, example=10)

class FeatureSelectionResponse(BaseModel):
    selection_id: str = Field(..., example="fs-run-123")
    selected_features: List[str] = Field(..., example=["feature1", "feature2"])
    dropped_features: List[Dict[str, str]] = Field(..., example=[{"name": "feat3", "reason": "low variance"}])

class FeatureEngineeringResponse(BaseModel):
    status: str = Field(..., example="success")
    columns: List[str] = Field(..., example=["feature1", "feature2", "target"])

class Evaluation(BaseModel):
    id: str = Field(..., example="eval-123")
    model_id: str = Field(..., example="m-123")
    project_id: str = Field(..., example="p1")
    metrics: Dict[str, float] = Field(..., example={"accuracy": 0.88})
    status: str = Field(..., example="completed")
    created_at: str = Field(..., example="2023-10-27T12:00:00")

class Prediction(BaseModel):
    id: str = Field(..., example="pred-123")
    model_id: str = Field(..., example="m-123")
    project_id: str = Field(..., example="p1")
    status: str = Field(..., example="completed")
    preview: List[Dict[str, Any]] = Field(..., example=[{"id": 1, "prediction": 0}])
    created_at: str = Field(..., example="2023-10-27T12:30:00")

# --- In-Memory Database (Legacy/Mock for non-integrated parts) ---

PROJECTS = [
    Project(id='p1', name='Credit Risk Model'),
    Project(id='p2', name='Churn Prediction'),
]

# --- Endpoints ---

@app.get("/projects", response_model=List[Project])
def get_projects():
    return PROJECTS

# --- Dataset & Data Pipeline Endpoints ---

@app.get("/projects/{project_id}/datasets", response_model=List[Dataset])
def list_datasets(project_id: str):
    return data_service.list_datasets(project_id)

@app.post("/projects/{project_id}/datasets/upload")
async def upload_dataset(project_id: str, file: UploadFile = File(...)):
    content = await file.read()
    dataset_id = data_service.upload_dataset(project_id, file.filename, content)
    return {"dataset_id": dataset_id}

@app.post("/projects/{project_id}/datasets/{dataset_id}/feature-engineer", response_model=FeatureEngineeringResponse)
def feature_engineer(project_id: str, dataset_id: str):
    return data_service.run_feature_engineering(dataset_id, project_id)

@app.post("/projects/{project_id}/datasets/{dataset_id}/feature-select", response_model=FeatureSelectionResponse)
def feature_select(project_id: str, dataset_id: str, req: FeatureSelectionRequest):
    return data_service.run_feature_selection(dataset_id, project_id, req.target_column, req.top_k)

@app.get("/projects/{project_id}/models", response_model=List[Model])
def list_models_endpoint(project_id: str):
    return data_service.list_models(project_id)

@app.post("/projects/{project_id}/models/train")
def train_model_postgres(project_id: str, req: TrainRequest):
    return data_service.train_model(req.dataset_id, req.selection_id, req.project_id, req.task_type)

class UploadCOSResponse(BaseModel):
    status: str = Field(..., example="success")
    cos_path: str = Field(..., example="cos://bucket/key")

@app.post("/projects/{project_id}/models/{model_id}/upload-to-cos", response_model=UploadCOSResponse)
def upload_model_to_cos_endpoint(project_id: str, model_id: str):
    return data_service.upload_model_to_cos_manual(project_id, model_id)

@app.post("/projects/{project_id}/predictions/upload")
async def upload_prediction(project_id: str, file: UploadFile = File(...)):
    content = await file.read()
    try:
        table_name, pred_id = data_service.upload_external_prediction(project_id, file.filename, content)
        return {
            "prediction_id": pred_id,
            "status": "success",
            "table_name": table_name,
            "message": "Prediction result uploaded to Postgres successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PredictionRequest(BaseModel):
    model_id: str = Field(..., example="m-123")
    dataset_id: str = Field(..., example="d-123")
    project_id: str = Field(..., example="p1")

class PredictionResponse(BaseModel):
    prediction_id: str = Field(..., example="pred-run-123")
    status: str = Field(..., example="completed")
    output_table: str = Field(..., example="pred_res_guid")
    preview: List[Dict[str, Any]]

# ... (Previous endpoints)

@app.post("/projects/{project_id}/models/predict", response_model=PredictionResponse)
def predict_model(project_id: str, req: PredictionRequest):
    return data_service.run_prediction(req.model_id, req.dataset_id, req.project_id)

from fastapi.responses import Response

@app.get("/predictions/{prediction_id}/download")
def download_prediction(prediction_id: str):
    csv_content = data_service.get_prediction_csv(prediction_id)
    if not csv_content:
         raise HTTPException(status_code=404, detail="Prediction output not found")
    
    return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=prediction_results_{prediction_id}.csv"})

@app.delete("/projects/{project_id}")
def delete_project(project_id: str):
    return data_service.delete_project(project_id)

# --- Legacy / Mock Endpoints ---
# ... (kept for compatibility)

@app.get("/projects/{project_id}/feature-stores")
def get_feature_stores_legacy(project_id: str):
    datasets = data_service.list_datasets(project_id)
    return [
        FeatureStore(
            id=d['id'],
            name=d['name'],
            description=f"Filename: {d['filename']}",
            offline_dataset_path=d['filename'],
            created_at=d['created_at']
        ) for d in datasets
    ]

