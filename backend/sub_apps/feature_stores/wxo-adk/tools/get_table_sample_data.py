from ibm_watsonx_orchestrate.agent_builder.tools import tool
from ibm_watsonx_orchestrate.agent_builder.connections import ConnectionType
from ibm_watsonx_orchestrate.run import connections

import requests

import types
import pandas as pd

from typing import Any, Optional
from pydantic import BaseModel, Field
from io import StringIO
import uuid


class TableSchema(BaseModel):
    dataset_id: str = Field(description="Dataset ID used to check")


@tool(
        name="BMRI_get_table_sample_data",
        description="Get sample data from certain table",
)
def BMRI_get_table_sample_data(raw_payload: TableSchema):
    
    url = f"https://tools-feature-store.23klqacsszs7.us-south.codeengine.appdomain.cloud/get_table_sample_data"

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "dataset_id": raw_payload.dataset_id
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.json()

@tool(
        name="BMRI_get_sample_sql_statement",
        description="Get sample SQL statement to generate features",
)
def BMRI_get_sample_sql_statement():
    
    url = f"https://tools-feature-store.23klqacsszs7.us-south.codeengine.appdomain.cloud/get_sample_sql_statement"

    headers = {
        "accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    return response.json()



class FeatureStoreSchema(BaseModel):
    table_name: str = Field(description="Table name that represents feature store created")
    sql_statement: str = Field(description="SQL statement to be executed into database")
    project_id: str = Field(description="Project ID"),
    dataset_id: str = Field(description="Dataset ID"),



@tool(
        name="BMRI_create_feature_store",
        description="Create feature store in database based on certain SQL statement",
)
def BMRI_create_feature_store(raw_payload: FeatureStoreSchema):
    
    url = f"https://tools-feature-store.23klqacsszs7.us-south.codeengine.appdomain.cloud/create_feature_store"

    headers = {
        "accept": "application/json"
    }

    payload = {
        "table_name": raw_payload.table_name,
        "sql_statement": raw_payload.sql_statement.replace("\n", " "),
        "project_id": raw_payload.project_id,
        "dataset_id": raw_payload.dataset_id,
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.json()