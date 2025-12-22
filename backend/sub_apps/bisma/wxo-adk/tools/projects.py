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


@tool(
        name="BMRI_list_projects",
        description="Get all projects from database",
)
def BMRI_list_projects():
    
    url = f"https://tools-project.23klqacsszs7.us-south.codeengine.appdomain.cloud/list_projects"

    headers = {
        "accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    return response.json()


class ProjectSchema(BaseModel):
    project_id: str = Field(description="Project ID to be used for next process")

@tool(
        name="BMRI_get_datasets_by_projectid",
        description="Get datasets based on specific project id",
)
def BMRI_get_datasets_by_projectid(payload: ProjectSchema):
    
    url = f"https://tools-project.23klqacsszs7.us-south.codeengine.appdomain.cloud/get_datasets_by_projectid?project_id={payload.project_id}"

    headers = {
        "accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    return response.json()

class SQLStatementSchema(BaseModel):
    sql_statement: str = Field(description="SQL Statement to be tested")

@tool(
        name="BMRI_test_sql_statement",
        description="Run SQL statement given into postgres database to check if it is correct and working",
)
def BMRI_test_sql_statement(raw_payload: SQLStatementSchema):
    
    url = f"https://tools-project.23klqacsszs7.us-south.codeengine.appdomain.cloud/execute_sql_statement"

    headers = {
        "accept": "application/json"
    }

    payload = {
        "sql_statement": raw_payload.sql_statement.replace("\n", " ")
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.json()