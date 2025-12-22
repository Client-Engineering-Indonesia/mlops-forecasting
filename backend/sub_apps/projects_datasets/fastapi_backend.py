"""
FastAPI untuk PoC Mandiri
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime
from contextlib import asynccontextmanager
import pandas as pd
import io
import uuid

from sqlalchemy.orm import Session

from config import get_settings
from database import engine, get_db, Base
from models import ProjectModel, DatasetModel
from schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    DatasetResponse, DatasetDetailResponse, PaginatedResponse
)


# =============================================================================
# Lifespan - Database Initialization
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified")
    yield
    print("Application shutdown")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Dataset Analysis API",
    description="API for managing projects and datasets (Excel/CSV) for data analysis",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = get_settings()


# =============================================================================
# Helper Functions
# =============================================================================

def parse_file(file: UploadFile) -> tuple[pd.DataFrame, str]:
    """Parse uploaded Excel or CSV file and return DataFrame with file type."""
    content = file.file.read()
    filename = file.filename.lower()

    if filename.endswith('.csv'):
        df = pd.read_csv(io.BytesIO(content))
        file_type = 'csv'
    elif filename.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(io.BytesIO(content))
        file_type = 'excel'
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload CSV or Excel file."
        )

    return df, file_type


def df_to_column_info(df: pd.DataFrame) -> List[dict]:
    """Extract column information from DataFrame."""
    return [{"name": col, "dtype": str(df[col].dtype)} for col in df.columns]


def df_to_json_records(df: pd.DataFrame) -> List[dict]:
    """Convert DataFrame to list of dictionaries, handling NaN values."""
    df = df.fillna("")
    return df.to_dict(orient='records')


# =============================================================================
# Project Endpoints
# =============================================================================

@app.post("/projects", response_model=ProjectResponse, status_code=201, tags=["Projects"])
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    db_project = ProjectModel(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return ProjectResponse(
        id=db_project.id,
        name=db_project.name,
        description=db_project.description,
        created_at=db_project.created_at,
        updated_at=db_project.updated_at,
        dataset_count=0
    )


@app.get("/projects", response_model=PaginatedResponse, tags=["Projects"])
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all projects with pagination."""
    query = db.query(ProjectModel)

    if search:
        query = query.filter(ProjectModel.name.ilike(f"%{search}%"))

    total = query.count()
    total_pages = (total + page_size - 1) // page_size

    projects = query.order_by(ProjectModel.created_at.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()

    items = []
    for p in projects:
        dataset_count = db.query(DatasetModel).filter(DatasetModel.project_id == p.id).count()
        items.append(ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            created_at=p.created_at,
            updated_at=p.updated_at,
            dataset_count=dataset_count
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@app.get("/projects/{project_id}", response_model=ProjectResponse, tags=["Projects"])
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific project by ID."""
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    dataset_count = db.query(DatasetModel).filter(DatasetModel.project_id == project_id).count()

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        dataset_count=dataset_count
    )


@app.put("/projects/{project_id}", response_model=ProjectResponse, tags=["Projects"])
def update_project(
    project_id: uuid.UUID,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update a project."""
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    dataset_count = db.query(DatasetModel).filter(DatasetModel.project_id == project_id).count()

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        dataset_count=dataset_count
    )


@app.delete("/projects/{project_id}", status_code=204, tags=["Projects"])
def delete_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a project and all its datasets."""
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()


# =============================================================================
# Dataset Endpoints
# =============================================================================

@app.post(
    "/projects/{project_id}/datasets",
    response_model=DatasetResponse,
    status_code=201,
    tags=["Datasets"]
)
async def create_dataset(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    name: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Create a new dataset by uploading an Excel or CSV file.
    
    Supported formats: .csv, .xlsx, .xls
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        df, file_type = parse_file(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")

    dataset_name = name or file.filename

    db_dataset = DatasetModel(
        project_id=project_id,
        name=dataset_name,
        description=description,
        file_name=file.filename,
        file_type=file_type,
        row_count=len(df),
        column_count=len(df.columns),
        columns=df_to_column_info(df),
        data=df_to_json_records(df)
    )

    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)

    return DatasetResponse(
        id=db_dataset.id,
        project_id=db_dataset.project_id,
        name=db_dataset.name,
        description=db_dataset.description,
        file_name=db_dataset.file_name,
        file_type=db_dataset.file_type,
        row_count=db_dataset.row_count,
        column_count=db_dataset.column_count,
        columns=db_dataset.columns,
        created_at=db_dataset.created_at,
        updated_at=db_dataset.updated_at
    )


@app.get(
    "/projects/{project_id}/datasets",
    response_model=PaginatedResponse,
    tags=["Datasets"]
)
def list_datasets(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all datasets for a specific project."""
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    query = db.query(DatasetModel).filter(DatasetModel.project_id == project_id)

    if search:
        query = query.filter(DatasetModel.name.ilike(f"%{search}%"))

    total = query.count()
    total_pages = (total + page_size - 1) // page_size

    datasets = query.order_by(DatasetModel.created_at.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()

    items = [
        DatasetResponse(
            id=d.id,
            project_id=d.project_id,
            name=d.name,
            description=d.description,
            file_name=d.file_name,
            file_type=d.file_type,
            row_count=d.row_count,
            column_count=d.column_count,
            columns=d.columns,
            created_at=d.created_at,
            updated_at=d.updated_at
        )
        for d in datasets
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@app.get(
    "/projects/{project_id}/datasets/{dataset_id}",
    response_model=DatasetDetailResponse,
    tags=["Datasets"]
)
def get_dataset(
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
    include_data: bool = Query(False, description="Include full dataset"),
    preview_rows: int = Query(10, ge=1, le=100, description="Number of preview rows"),
    db: Session = Depends(get_db)
):
    """
    Get a specific dataset by project ID and dataset ID.
    
    - Set `include_data=true` to get the full dataset
    - By default, returns only metadata and a preview of first N rows
    """
    dataset = db.query(DatasetModel).filter(
        DatasetModel.id == dataset_id,
        DatasetModel.project_id == project_id
    ).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    preview = dataset.data[:preview_rows] if dataset.data else None

    return DatasetDetailResponse(
        id=dataset.id,
        project_id=dataset.project_id,
        name=dataset.name,
        description=dataset.description,
        file_name=dataset.file_name,
        file_type=dataset.file_type,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        columns=dataset.columns,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        data=dataset.data if include_data else None,
        preview=preview
    )


@app.delete(
    "/projects/{project_id}/datasets/{dataset_id}",
    status_code=204,
    tags=["Datasets"]
)
def delete_dataset(
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Delete a dataset."""
    dataset = db.query(DatasetModel).filter(
        DatasetModel.id == dataset_id,
        DatasetModel.project_id == project_id
    ).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    db.delete(dataset)
    db.commit()


# =============================================================================
# Analysis Endpoints
# =============================================================================

@app.get(
    "/projects/{project_id}/datasets/{dataset_id}/statistics",
    tags=["Analysis"]
)
def get_dataset_statistics(
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get basic statistics for a dataset."""
    dataset = db.query(DatasetModel).filter(
        DatasetModel.id == dataset_id,
        DatasetModel.project_id == project_id
    ).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if not dataset.data:
        return {"message": "No data available"}

    df = pd.DataFrame(dataset.data)

    stats = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": {},
        "missing_values": {}
    }

    for col in df.columns:
        col_stats = {"dtype": str(df[col].dtype)}
        
        if pd.api.types.is_numeric_dtype(df[col]):
            col_stats.update({
                "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                "median": float(df[col].median()) if not pd.isna(df[col].median()) else None,
                "std": float(df[col].std()) if not pd.isna(df[col].std()) else None
            })
        else:
            col_stats.update({
                "unique_count": int(df[col].nunique()),
                "top_values": df[col].value_counts().head(5).to_dict()
            })

        stats["columns"][col] = col_stats
        stats["missing_values"][col] = int(df[col].isna().sum())

    return stats


# =============================================================================
# Health Check
# =============================================================================

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database_host": settings.POSTGRES_HOST
    }


# =============================================================================
# Run with: uvicorn main:app --reload
# =============================================================================