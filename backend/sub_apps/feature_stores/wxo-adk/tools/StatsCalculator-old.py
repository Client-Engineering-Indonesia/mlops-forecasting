# --- Feature engineering table generator (append below existing tools) ---
from ibm_watsonx_orchestrate.agent_builder.tools import tool

import csv
import io
import re
from datetime import datetime, date, time
from decimal import Decimal
from typing import Dict, List, Optional, Tuple


from dotenv import load_dotenv
import os, json
from sqlalchemy import create_engine, text


@tool
def get_metadata(nlimit: int = 1) -> dict:
    """
    Returns metadata and sample data for a PostgreSQL table.
    
    Args:
        schema: Database schema name (default: "public")
        table_name: Name of the table to query (default: "sample_datasets")
    
    Returns:
        dict: Contains count, columns metadata, and one sample row
    """
    # Custom JSON serializer
    def serialize(obj):
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        raise TypeError(f"Type {type(obj)} not serializable")
    
    schema = "public"
    table_name = "sample_datasets"

    # load_dotenv()s
    # Get and validate environment variables
    # pg_config = {
    #     'host': os.getenv("POSTGRES_HOST"),
    #     'port': os.getenv("POSTGRES_PORT"),
    #     'user': os.getenv("POSTGRES_USER"),
    #     'password': os.getenv("POSTGRES_PASSWORD"),
    #     'db': os.getenv("POSTGRES_DB"),
    #     'sslmode': os.getenv("POSTGRES_SSLMODE", "prefer")
    # }
    pg_config = {
        'host': 'xxx',
        'port': 8080,
        'user': 'xxx',
        'password': 'xxx',
        'db': 'xxx',
        'sslmode': 'prefer'
    }
    
    if not all([pg_config['host'], pg_config['user'], pg_config['password'], pg_config['db']]):
        raise ValueError("Missing required environment variables: POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, or POSTGRES_DB")
    
    # Create connection URL and engine
    conn_url = (
        f"postgresql+psycopg2://{pg_config['user']}:{pg_config['password']}"
        f"@{pg_config['host']}:{pg_config['port']}/{pg_config['db']}"
        f"?sslmode={pg_config['sslmode']}"
    )
    engine = create_engine(conn_url, pool_pre_ping=True)
    
    # Execute queries
    with engine.connect() as conn:
        count_result = conn.execute(
            text(f'SELECT COUNT(*) AS n FROM {schema}.{table_name}')
        ).mappings().first()
        
        sample_row = conn.execute(
            text(f'SELECT * FROM {schema}.{table_name} LIMIT :limit'),
            {"limit": nlimit}
        ).mappings().all()
        
        columns = conn.execute(
            text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = :schema AND table_name = :table
                ORDER BY ordinal_position
            """),
            {"schema": schema, "table": table_name}
        ).mappings().all()
    
    # Build and return result
    result = {
        "schema": schema,
        "table": table_name,
        "count": count_result["n"],
        "columns": [dict(col) for col in columns],
        "rows": [{k: v for k, v in row.items()} for row in sample_row]
    }
    
    return json.loads(json.dumps(result, default=serialize))


@tool
def get_column_data_v2(column_selected, host_id="", gap_days: int = 2) -> dict:
    """
    Performs a feature engineering that uses on sample_datasets, create average value metrics between two datetime points separated by a specified number of days. Show 10-20 rows of results in table format.

    Datasets only have 'datetime', 'hostname', 'core_number_avg', 'cpu_usage_percentage_avg', 'memory_number_avg', 'memory_usage_percentage_avg' columns.  

    Args:
        column_selected: Comma-separated column names string. All the data included data_index, data_target, and data_feature (default: 'hostname', 'datetime', 'core_number', 'cpu_usage_percentage', 'memory_number', 'memory_usage_percentage')
        host_id: Specific host_id to filter (e.g., "5"). If empty string, returns all hosts (default: "")
        gap_days: Number of days between comparison points (default: 2)

        Example:
        'data index choose hostname 1; data target is cpu usage percentage; data features only use memory usage percentage; gap days is 5'

        gap_days = 5
        host_id = "5"  # or "" for all hosts
        column_selected = ["hostname", "host_id", "datetime_1", "datetime_2", "cpu_usage_percentage_avg", "memory_usage_percentage_avg"]

        {"column_selected":"hostname,host_id,datetime_1,datetime_2,cpu_usage_percentage_avg,memory_usage_percentage_avg","host_id":"5","gap_days":2}
        
    
    Returns:
        dict: Contains query metadata and result rows with averaged metrics
    """
    from datetime import datetime, date, time
    from decimal import Decimal
    import json
    from sqlalchemy import create_engine, text
    
    # Custom JSON serializer
    def serialize(obj):
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        raise TypeError(f"Type {type(obj)} not serializable")
    
    # Database configuration
    pg_config = {
        'host': 'xxx',
        'port': 8080,
        'user': 'xxx',
        'password': 'xxx',
        'db': 'xxx',
        'sslmode': 'prefer'
    }
    
    if not all([pg_config['host'], pg_config['user'], pg_config['password'], pg_config['db']]):
        raise ValueError("Missing required database configuration")
    
    # Create connection URL and engine
    conn_url = (
        f"postgresql+psycopg2://{pg_config['user']}:{pg_config['password']}"
        f"@{pg_config['host']}:{pg_config['port']}/{pg_config['db']}"
        f"?sslmode={pg_config['sslmode']}"
    )
    engine = create_engine(conn_url, pool_pre_ping=True)
    
    # Convert host_id to integer or None
    filter_host_id = None
    if host_id and host_id.strip():
        try:
            filter_host_id = int(host_id.strip())
        except ValueError:
            raise ValueError(f"host_id must be a valid integer, got: {host_id}")
    
    # Gap analysis query with optional host_id filter
    query = text("""
        WITH params AS (
          SELECT 
            CAST(:gap_days AS INTEGER) AS gap_days,
            CAST(:filter_host_id AS INTEGER) AS filter_host_id
        ),
        base AS (
          SELECT
            hostname,
            (regexp_match(trim(hostname), '(\d+)'))[1]::int AS host_id,
            "datetime",
            core_number,
            cpu_usage_percentage,
            memory_number,
            memory_usage_percentage
          FROM public.sample_datasets
        ),
        filtered_base AS (
          SELECT * 
          FROM base
          WHERE (SELECT filter_host_id FROM params) IS NULL 
             OR host_id = (SELECT filter_host_id FROM params)
        )
        SELECT
          b1.hostname,
          b1.host_id,
          b1."datetime" AS datetime_1,
          b2."datetime" AS datetime_2,
          (b1.core_number + b2.core_number) / 2.0 AS core_number_avg,
          (b1.cpu_usage_percentage + b2.cpu_usage_percentage) / 2.0 AS cpu_usage_percentage_avg,
          (b1.memory_number + b2.memory_number) / 2.0 AS memory_number_avg,
          (b1.memory_usage_percentage + b2.memory_usage_percentage) / 2.0 AS memory_usage_percentage_avg
        FROM filtered_base b1
        JOIN params p ON true
        LEFT JOIN filtered_base b2
          ON b2.host_id = b1.host_id
         AND b2."datetime" = b1."datetime" + make_interval(days => p.gap_days)
        ORDER BY
          b1.host_id ASC,
          b1."datetime" ASC
    """)
    
    # Execute query with parameters
    with engine.connect() as conn:
        result_rows = conn.execute(query, {
            "gap_days": gap_days,
            "filter_host_id": filter_host_id  # None for all hosts, or specific integer
        }).mappings().all()
    
    # Filter columns based on column_selected
    if isinstance(column_selected, str):
        fields = [c.strip() for c in column_selected.split(",") if c.strip()]
    else:
        fields = list(column_selected)
    rows_filtered = [{k: row.get(k) for k in fields} for row in result_rows]

    # Build and return result
    result = {
        "query_type": "gap_analysis",
        "gap_days": gap_days,
        "host_id_filter": host_id if host_id else "all",
        "row_count": len(result_rows),
        "rows": rows_filtered[:20]  # limit to first 20 rows for brevity
    }
    
    return json.loads(json.dumps(result, default=serialize))