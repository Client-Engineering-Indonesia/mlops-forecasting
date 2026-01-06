from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from io import BytesIO
from pathlib import Path

from typing import List, Optional
import uuid
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

#from openai import OpenAI
from dotenv import load_dotenv
import os
import io
import re
import uuid
from datetime import datetime, timedelta

import pickle
import pandas as pd
import numpy as np

from utils.postgres import (
    db_get_dataset_by_id,
    db_get_columns_by_datasetid,

    db_get_feature_stores_by_projectid,
    db_get_models_by_projectid,
    db_get_feature_stores_by_id,

    db_insert_model,
    db_insert_selected_features,
    db_get_models_by_id,
    db_get_selected_features_by_modelid,

    db_execute_sql,

    db_get_predictions_by_projectid,
    db_upload_test_file,
    db_insert_predictions,

)
from utils.model import create_model_pipeline
from utils.wxo import multiprocess_llm_answer
from utils.cos import upload_model_to_cos, upload_buffer_to_cos, download_csv_to_file, download_model_pickle

# Load env vars
load_dotenv()


app = FastAPI(title="Voice STT API")

current_session_id = str(uuid.uuid4())

UPLOAD_DIR = Path("predictions")
UPLOAD_DIR.mkdir(exist_ok=True)


PICKLE_DIR = Path("model_pickle")
PICKLE_DIR.mkdir(exist_ok=True)

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

class SampleDataSchema(BaseModel):
    dataset_id: str = Field(description="Dataset ID to be checked")


@app.get("/get_feature_stores_by_projectid")
def get_feature_stores_by_projectid(project_id):

    feature_stores = db_get_feature_stores_by_projectid(project_id)

    if feature_stores is None:
        return []

    return [dict(fs) for fs in feature_stores]


@app.get("/get_models_by_projectid")
def get_models_by_projectid(project_id):

    models = db_get_models_by_projectid(project_id)

    if models is None:
        return []

    return [dict(m) for m in models]


@app.get("/get_predictions")
def get_predictions(project_id):

    models = db_get_predictions_by_projectid(project_id)

    if models is None:
        return []

    return [dict(m) for m in models]


class ModelSchema(BaseModel):
    feature_store_id: str = Field(description="Feature store ID")

@app.post("/create_model")
def create_model(payload: ModelSchema):

    fs_info = db_get_feature_stores_by_id(payload.feature_store_id)
    dataset = db_get_dataset_by_id(fs_info['dataset_id'])
    columns = db_get_columns_by_datasetid(fs_info['dataset_id'])
    date_column = "".join([col['column_name'] for col in columns if col['is_date'] == 'Y'])
    target_column = "".join([col['column_name'] for col in columns if col['is_target'] == 'Y'])
    key_column = "".join([col['column_name'] for col in columns if col['is_forecast_key'] == 'Y'])

    fs = db_execute_sql(f"SELECT * FROM {fs_info['table_path']} ")
    fs = [dict(feat) for feat in fs]
    fs = pd.DataFrame(fs)

    # set datetime to target column
    fs[date_column] = pd.to_datetime(fs[date_column])
    
    # set target
    fs_target = fs.copy()
    fs_target[f"date_on_next_{dataset['n1_next_week_for_prediction']}weeks"] = fs_target[date_column] + pd.Timedelta(days=7 * dataset['n1_next_week_for_prediction'])
    fs_target = pd.merge(fs.drop(columns=[target_column]), fs_target[[key_column, f"date_on_next_{dataset['n1_next_week_for_prediction']}weeks", target_column]], on=[key_column], how='inner')
    fs_target = fs_target[fs_target[date_column] == fs_target[f"date_on_next_{dataset['n1_next_week_for_prediction']}weeks"]]

    # filter training data withing defined horizon    
    earliest_dt = fs[date_column].min()
    fs_target = fs_target[fs_target[date_column] > earliest_dt + timedelta(days = 7 * dataset['n_past_week_for_training'])]

    y = fs_target[target_column]
    numeric_cols = fs_target.drop(columns=[target_column]).select_dtypes(include="number").columns.tolist()
    X = fs_target[numeric_cols]
    X = X.fillna(0)

    model_result = create_model_pipeline(X, y)
    
    # Ssave prediction result
    fs_target["pred"] = model_result["prediction"]["pred"]
    pred_path = f"training__{uuid.uuid4()}.csv"
    pred_file_path = upload_buffer_to_cos(fs_target, pred_path)
    
    # Save model
    model_id = f"model__{str(uuid.uuid4())}"
    model_path = f"{model_id}.pickle"
    model_file_path = upload_model_to_cos(model_result["model"], model_path)
    db_insert_model(
        fs_info["project_id"], 
        dataset["dataset_id"], 
        payload.feature_store_id, 
        model_id, 
        model_result["metrics"]["training_result"], 
        model_result["metrics"]["testing_result"], 
        pred_file_path, 
        model_file_path,
    )

    for feat in model_result["selected_features"]:
        db_insert_selected_features(fs_info["project_id"], dataset["dataset_id"], payload.feature_store_id, model_id, feat)


    return {"status": f"Model {model_id} has been created."}


@app.get("/download_training_result")
def download_training_result(model_id: str):

    dataset = db_get_models_by_id(model_id)
    obj, clean_object_key = download_csv_to_file(dataset['training_pred_file_path'])

    buffer = BytesIO(obj["Body"].read())

    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={clean_object_key}"
        }
    )


def sanitize_identifier(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]", "_", s)
    s = re.sub(r"_+", "_", s)        # collapse multiple underscores
    return s.strip("_").lower()


def pandas_to_sql_type(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return "INTEGER"
    elif pd.api.types.is_float_dtype(dtype):
        return "FLOAT"
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    else:
        return "VARCHAR"

@app.post("/get_model_prediction")
async def get_model_prediction(
    file: UploadFile = File(...),
    model_id: str = Form(...),
):
    print(f"file.filename: {file.filename}")
    print("model_id: ", model_id)

    model_info = db_get_models_by_id(model_id)
    dataset = db_get_dataset_by_id(model_info["dataset_id"])
    enriched_columns = db_get_columns_by_datasetid(dataset["dataset_id"])
    date_column = "".join([col["column_name"] for col in enriched_columns if col["is_date"] == 'Y'])

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = file.filename.lower().rsplit(".", 1)[-1]

    # ✅ READ ONCE
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    safe_name = f"test_file__{sanitize_identifier(file.filename)}_{uuid.uuid4().hex}"
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

    # upload test file
    dataset_id = str(uuid.uuid4())
    db_upload_test_file(safe_name, df.to_dict(orient='records'), column_list, model_info["project_id"], dataset_id)

    print("File has been uploaded")

    # generate features needed
    fs_info = db_get_feature_stores_by_id(model_info["feature_store_id"])
    sql_statement = fs_info["sql_statement"]

    table_path = f"prediction_features__{str(uuid.uuid4())}"
    table_path = sanitize_identifier(table_path)

    # Step 1: Get sample dataset
    llm_response1 = multiprocess_llm_answer({
        "input_prompt": f"""Change source of table used from SQL statement below to '{safe_name} and destination table to '{table_path}'

SQL Statement:
```
{sql_statement}
```
""",
    })

    print(llm_response1)
    print()

    # Step 2: Design feature store
    llm_response2 = multiprocess_llm_answer({
        "input_prompt": f"Create feature store by executing that sql statement. Use destination table name: {table_path}, project id: {model_info['project_id']}, and dataset id: {dataset_id}",
        "thread_id": llm_response1["thread_id"],
    })

    print(llm_response2)
    print()

    
    # get prediction from model
    print("Model File PATH: ", model_info["model_file_path"])
    model_file_path = model_info["model_file_path"]

    local_path = f"{PICKLE_DIR}/{sanitize_identifier(model_file_path)}"
    download_model_pickle(model_file_path, local_path)

    with open(local_path, "rb") as f:
        model = pickle.load(f)

    
    test_data = db_execute_sql(f"SELECT * FROM {table_path}")
    test_data = pd.DataFrame([data for data in test_data])

    print(f"test data: {test_data.head(3).to_dict(orient='records')}")

    selected_features = db_get_selected_features_by_modelid(model_id)
    selected_features = [col["column_name"] for col in selected_features]

    print(f"selected features: {selected_features}")

    X_data = test_data[selected_features]
    X_data["prediction"] = model.predict(X_data)

    test_data[f"date_next_{dataset['n1_next_week_for_prediction']}"] = test_data[date_column] + pd.Timedelta(days=7 * dataset["n1_next_week_for_prediction"])
    test_data["prediction"] = X_data["prediction"]

    # Store prediction to csv and IBM COS
    pred_path = f"prediction_result__{uuid.uuid4()}.csv"
    pred_file_path = upload_buffer_to_cos(test_data, pred_path)


    db_insert_predictions(
        model_info["project_id"], 
        model_info["dataset_id"], 
        model_info["feature_store_id"], 
        model_info["model_id"], 
        pred_file_path
    )

    return {"status": f"Prediction can be found at {pred_file_path} has been created"}



@app.get("/download_prediction_result")
def download_prediction_result(pred_file_path: str):

    obj, clean_object_key = download_csv_to_file(pred_file_path)

    buffer = BytesIO(obj["Body"].read())

    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={clean_object_key}"
        }
    )