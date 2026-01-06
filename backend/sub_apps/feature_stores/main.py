from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from typing import List, Optional
import uuid
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

#from openai import OpenAI
from dotenv import load_dotenv
import os
from datetime import datetime

import pandas as pd
import numpy as np

from utils.postgres import (
    db_create_table, 
    db_get_table_sample_data, 
    db_get_min_max_date,
    db_get_target_overview,
    db_get_key_overview,
    db_insert_to_feature_store,
    db_list_datasets_by_projectid,

    db_get_features_by_projectid,
    db_insert_to_feature_store_columns,
    db_get_feature_store_by_fsid,
    db_get_dataset_by_id,
    db_get_project_by_id,

    db_get_columns_by_datasetid,
    
    db_execute_sql,

)
from utils.wxo import multiprocess_llm_answer

# Load env vars
load_dotenv()


app = FastAPI(title="Voice STT API")

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

class SampleDataSchema(BaseModel):
    dataset_id: str = Field(description="Dataset ID to be checked")


@app.post("/get_table_sample_data")
def get_table_sample_data(payload: SampleDataSchema):

    dataset = db_get_dataset_by_id(payload.dataset_id)
    columns = db_get_columns_by_datasetid(payload.dataset_id)
    columns_used = [col["column_name"] for col in columns if col["is_forecast_key"] == 'Y' or col["is_date"] == "Y" or col["is_target"] == "Y" or col["is_feature"] == "Y"]
    sample_data = db_execute_sql("SELECT " + ", ".join([col for col in columns_used]) + " FROM " + dataset["raw_data_table_path"] + " LIMIT 5")

    return {
        "sample_data": [dict(data) for data in sample_data],
        "target_column_name": [col["column_name"] for col in columns if str(col["is_target"]) == 'Y'],
        "used_columns_for_feature_generation": [col["column_name"] for col in columns if str(col["is_feature"]) == 'Y'],
        "key_column_name": [col["column_name"] for col in columns if str(col["is_forecast_key"]) == 'Y'],
        "date_column_name": [col["column_name"] for col in columns if str(col["is_date"]) == 'Y'],
    }



@app.get("/get_sample_sql_statement")
def get_sample_sql_statement():
    '''
    lag_df = pd.read_excel(
        "data/sql_sample.xlsx",
        sheet_name="lag"
    )

    rolling_window_df = pd.read_excel(
        "data/sql_sample.xlsx",
        sheet_name="rolling_window"
    )

    diff_df = pd.read_excel(
        "data/sql_sample.xlsx",
        sheet_name="diff"
    )

    slope_df = pd.read_excel(
        "data/sql_sample.xlsx",
        sheet_name="slope"
    )

    calendar_df = pd.read_excel(
        "data/sql_sample.xlsx",
        sheet_name="calendar"
    )

    '''

    compiled_df = pd.read_excel(
        "data/sql_sample.xlsx",
        sheet_name="compiled_sql"
    )


    return {
        "compiled_features_sql": compiled_df
    }
					


@app.post("/create_basic_feature_store")
def create_basic_feature_store(payload: SampleDataSchema):

    dataset = db_get_dataset_by_id(payload.dataset_id)
    columns = db_get_columns_by_datasetid(dataset['dataset_id'])
    key_column = "".join([col['column_name'] for col in columns if col['is_forecast_key'] == 'Y'] ) 
    date_column = "".join([col['column_name'] for col in columns if col['is_date'] == 'Y'] ) 
    target_column = "".join([col['column_name'] for col in columns if col['is_target'] == 'Y'] ) 

    table_name = f"feature_store_{str(uuid.uuid4())}"
    table_name = table_name.replace("-", "_")

    # Step 1: Get sample dataset
    llm_response1 = multiprocess_llm_answer({
        "input_prompt": f"show sample data from dataset id: {payload.dataset_id}",
    })

    print(llm_response1)
    print()

    # Step 2: Design feature store
    llm_response2 = multiprocess_llm_answer({
        "input_prompt": f"Get sample of sql statement. Then, design feature store based on that sql sample "\
            f" using source table as below:\n{dataset['raw_data_table_path']}."\
                "Don't create feature store in database at this state.",
        "thread_id": llm_response1["thread_id"],
    })

    print(llm_response2)
    print()

    # Step 3: Add required columns
    llm_response3 = multiprocess_llm_answer({
        "input_prompt": f"Ensure your sql statement has columns named '{key_column}', '{date_column}', and '{target_column}' "\
            "that are retrieved from base data table. If not you have to recreate sql statement. "
            "Don't create feature store in database at this state.",
        "thread_id": llm_response1["thread_id"],
    })

    print(llm_response3)
    print()

    # Step 4: Design feature store
    llm_response4 = multiprocess_llm_answer({
        "input_prompt": f"Ensure your sql statement also store the result into table named {table_name}. If not you have to recreate sql statement. Don't create feature store at this state.",
        "thread_id": llm_response1["thread_id"],
    })

    print(llm_response4)
    print()

    

    # Step 4: Design feature store
    llm_response5 = multiprocess_llm_answer({
        "input_prompt": f"Now create feature store by executing that sql statement. Use destination table name: {table_name}, project id: {dataset['project_id']}, and dataset id: {payload.dataset_id}",
        "thread_id": llm_response1["thread_id"],
    })

    print(llm_response5)
    print()
    

    return {
        "status": "success", 
        "llm_response": [llm_response1, llm_response2, llm_response3, llm_response4, llm_response5]
    }



class CreateTableSchema(BaseModel):
    project_id: str = Field(description="Project ID")
    dataset_id: str = Field(description="Dataset ID")
    table_name: str = Field(description="Table Name")
    sql_statement: str = Field(description="SQL Statement")


@app.post("/create_feature_store")
def create_feature_store(payload: CreateTableSchema):

    status = db_create_table(payload.sql_statement)

    feature_store_id = str(uuid.uuid4())

    db_insert_to_feature_store(payload.project_id, payload.dataset_id, feature_store_id, payload.table_name, payload.sql_statement)

    fs = db_get_feature_store_by_fsid(feature_store_id)
    fs_columns = db_execute_sql(f"SELECT * FROM {fs['table_path']} LIMIT 1")
    fs_columns = pd.DataFrame([dict(feat) for feat in fs_columns])

    for col in fs_columns.columns:
        db_insert_to_feature_store_columns(payload.project_id, payload.dataset_id, feature_store_id, col)

    return {"status": status, "table_path": payload.table_name}

@app.get("/get_features_by_projectid")
def get_features_by_projectid(project_id: str):
    feature_final = []

    features = db_get_features_by_projectid(project_id)
    features_df = pd.DataFrame([dict(feat) for feat in features])

    if len(features_df) == 0:
        return feature_final
    
    for fsid in features_df["feature_store_id"].unique():
        columns = features_df[features_df["feature_store_id"] == fsid]
        if 'prediction_features' in columns["table_path"].values[0]:
            continue

        feature_final.append({
            "table_path": columns["table_path"].values[0],
            "features_list": list(columns["column_name"].values),
            "total_features": len(columns),
            "from_dataset": columns["base_data_table_path"].values[0],
        })


    
    for table_path in features_df["table_path"].unique():
        try:
            sample_data = db_execute_sql(f"SELECT * FROM {table_path} LIMIT 5")
            features_list =  [key for key in sample_data[0].keys()]

            dataset_name = db_execute_sql(f"SELECT DISTINCT d.table_path FROM feature_stores f JOIN datasets d ON d.dataset_id = f.dataset_id WHERE f.table_path = '{table_path}' ")
            dataset_name = "".join([d["table_path"] for d in dataset_name])

            
            feature_final.append({
                "table_path": table_path,
                "features_list": features_list,
                "total_features": len(features_list),
                "from_dataset": dataset_name,
            })
        except Exception as e:
            continue

    print(feature_final)

    return feature_final





