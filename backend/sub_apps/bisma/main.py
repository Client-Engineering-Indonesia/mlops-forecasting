from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from pathlib import Path
import shutil
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

#from openai import OpenAI
from dotenv import load_dotenv
import os
import re
import io
from datetime import datetime

import pandas as pd
import numpy as np

from utils.postgres import (
    db_list_projects,
    db_get_project_by_projectid,
    db_create_project,

    db_get_datasets_by_projectid,
    db_create_dataset,
    db_update_dataset,
    db_create_column,
    db_update_column,
    db_get_dataset_by_id,
    db_create_target_table,

    db_execute_sql_statement,

    db_create_base_data_table,
)

# Load env vars
load_dotenv()


app = FastAPI(title="Voice STT API")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

current_session_id = str(uuid.uuid4())

# Allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
def root():
    return {"message": "FastAPI + Whisper is running"}

class ProjectSchema(BaseModel):
    project_id: str = Field(description="Project ID")


@app.get("/list_projects")
def list_projects():
    return db_list_projects()


@app.get("/get_project_by_projectid")
def get_project_by_projectid(project_id: str):
    row = db_get_project_by_projectid(project_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return dict(row)


class CreateProjectSchema(BaseModel):
    project_name: str = Field(description="Project Name")
    project_description: str = Field(description="Project description includes overview of project, timeline, methodology, etc.")
				

@app.post("/create_project")
def create_project(payload: CreateProjectSchema):

    project_id = str(uuid.uuid4())

    db_create_project(project_id, payload.project_name, payload.project_description)

    return {"status": f"Project ID {project_id} has been created"}


@app.get("/get_datasets_by_projectid")
def get_datasets_by_projectid(project_id: str):
    result = db_get_datasets_by_projectid(project_id)

    if not result:
        return []
    
    result_df = pd.DataFrame([dict(data) for data in result])
    
    datasets = []
    for dataset_id in result_df["dataset_id"].unique():
        dataset = result_df[result_df["dataset_id"] == dataset_id]

        dataset_info = dataset[["project_id", "dataset_id", "raw_data_table_path", "base_data_table_path", "n_past_week_for_training", "n1_next_week_for_prediction", "n2_next_week_for_prediction"]]
        dataset_info = dataset_info.drop_duplicates(ignore_index=True)
        dataset_info = dataset_info.to_dict(orient='records')
        dataset_info = dataset_info[0]

        dataset_info["columns"] = [dict(val) for idx, val in dataset[["column_name", "column_type", "is_forecast_key", "is_target", "is_date", "is_feature"]].iterrows()]

        datasets.append(dataset_info)

    return datasets


class CreateDatasetSchema(BaseModel):
    project_id: str = Field(description="Project ID")
    table_path: str = Field(description="Table name")
    n_past_week_for_training: int = Field("How many weeks from the past until cutoff date to be used for training")
    n1_next_week_for_prediction: int = Field("How many weeks to be forecasted since cutoff date")
    n2_next_week_for_prediction: int = Field("How is maximum weeks to be forecasted since cutoff date for classification use case")


def pandas_to_sql_type(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return "INTEGER"
    elif pd.api.types.is_float_dtype(dtype):
        return "FLOAT"
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    else:
        return "VARCHAR"


def sanitize_identifier(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]", "_", s)
    s = re.sub(r"_+", "_", s)        # collapse multiple underscores
    return s.strip("_").lower()

@app.post("/create_dataset")
async def create_dataset(
    file: UploadFile = File(...),

    project_id: str = Form(...),
    n_past_week_for_training: int = Form(...),
    n1_next_week_for_prediction: int = Form(...),
    n2_next_week_for_prediction: int = Form(...),
):
    print(f"file.filename: {file.filename}")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = file.filename.lower().rsplit(".", 1)[-1]

    # ✅ READ ONCE
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    safe_name = f"dataset__{sanitize_identifier(file.filename)}_{uuid.uuid4().hex}"
    dest = UPLOAD_DIR / safe_name

    # ✅ Save (optional)
    with dest.open("wb") as f:
        f.write(contents)

    # ✅ Parse from the bytes you already read
    try:
        if ext == "csv":
            df = pd.read_csv(io.BytesIO(contents), nrows=0)

        elif ext == "xlsx":
            df = pd.read_excel(io.BytesIO(contents), sheet_name="Sheet1", engine="openpyxl")

        elif ext == "xls":
            df = pd.read_excel(io.BytesIO(contents), sheet_name="Sheet1", engine="xlrd")

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    dataset_id = str(uuid.uuid4())

    # build column list
    column_list = []
    renamed_cols = {}
    for col in df.columns:
        colname = sanitize_identifier(col)
        renamed_cols[col] = colname

    df = df.rename(columns=renamed_cols)

    print(f"df: {df}")

    for colname in df.columns:
        column_list.append({
            "name": colname,
            "type": pandas_to_sql_type(df[colname].dtype),
        })

    db_create_dataset(
        project_id, dataset_id, safe_name,
        n_past_week_for_training, n1_next_week_for_prediction, n2_next_week_for_prediction,
        column_list,
        df.to_dict(orient="records"),
    )

    for col in column_list:
        # NOTE: your code had pandas_to_sql_type(col['type']) which is wrong because col['type'] is already a SQL type string
        db_create_column(project_id, dataset_id, col["name"], col["type"])

    return {"status": f"Dataset ID {dataset_id} has been created"}


class DatasetColumns(BaseModel):
    column_name: str = Field(description="Column name")
    is_forecast_key: str = Field(description="Key to be forecasted")
    is_target: str = Field(description="Target column")
    is_date: str = Field(description="Date column")
    is_feature: str = Field(description="Used for Feature")

class UpdateDatasetSchema(BaseModel):
    project_id: str = Field(description="Project ID")
    dataset_id: str = Field(description="Dataset ID")
    columns: List[DatasetColumns] = Field(description="List of columns")

@app.post("/update_dataset")
def update_dataset(payload: UpdateDatasetSchema):

    key_column = ""
    date_column = ""
    target_column = ""

    for col in payload.columns:
        db_update_column(
            payload.project_id, 
            payload.dataset_id, 
            col.column_name, 
            is_forecast_key=col.is_forecast_key, 
            is_target=col.is_target, 
            is_date=col.is_date, 
            is_feature=col.is_feature
        )

        if col.is_forecast_key == "Y":
            key_column = col.column_name
        if col.is_date == "Y":
            date_column = col.column_name
        if col.is_target == "Y":
            target_column = col.column_name

    dataset = db_get_dataset_by_id(
        payload.project_id, 
        payload.dataset_id, 
    )
    target_data_table_path = db_create_target_table(key_column, date_column, target_column, dataset["raw_data_table_path"], dataset["n1_next_week_for_prediction"])
    base_data_table_path = db_create_base_data_table(dataset["raw_data_table_path"], target_data_table_path, f"base_data__{str(uuid.uuid4()).replace('-', '_')}", key_column, date_column)

    db_update_dataset(
        payload.project_id, 
        payload.dataset_id,
        target_data_table_path,
        base_data_table_path,
    )

    return {"status": f"Columns in dataset ID {payload.dataset_id} has been updated"}


class SQLStatementSchema(BaseModel):
    sql_statement: str = Field(description="SQL Statement")

@app.post("/execute_sql_statement")
def execute_sql_statement(payload: SQLStatementSchema):
    print(payload.sql_statement.replace("\n", " "))
    return {
        "status": "success",
        "sample_data": db_execute_sql_statement(payload.sql_statement)[:5]
    }