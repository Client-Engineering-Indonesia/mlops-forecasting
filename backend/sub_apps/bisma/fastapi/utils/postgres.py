# db.py
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from psycopg2 import sql

from dotenv import load_dotenv
import os

load_dotenv()


POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB")

def get_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        cursor_factory=RealDictCursor,  # returns dicts instead of tuples
    )

def db_list_projects():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM projects",
            )
            return cursor.fetchall()
    finally:
        conn.close()

def db_get_project_by_projectid(project_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM projects WHERE project_id = %s",
                (project_id,)
            )
            
            return cursor.fetchone()
    finally:
        conn.close()


def db_get_dataset_by_id(project_id, dataset_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM datasets WHERE project_id = %s AND dataset_id = %s",
                (project_id, dataset_id, )
            )
            
            return cursor.fetchone()
    finally:
        conn.close()

def db_create_project(project_id, project_name, project_description):
    query = """
        INSERT INTO projects(project_id, project_name, project_description)
        VALUES (%s, %s, %s)
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, (
        project_id, project_name, project_description
    ))

    conn.commit()
    cur.close()
    conn.close()

def db_get_datasets_by_projectid(project_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT d.*,
                    c.column_name,
                    c.column_type,
                    c.is_target,
                    c.is_forecast_key,
                    c.is_feature,
                    c.is_date 
                FROM datasets d
                JOIN enriched_columns c ON d.dataset_id = c.dataset_id
                WHERE d.project_id = %s""",
                (project_id, )
            )
            
            return cursor.fetchall()
    finally:
        conn.close()


def db_create_dataset(project_id, dataset_id, table_path, n_past_week_for_training, n1_next_week_for_prediction, n2_next_week_for_prediction, column_list, data):

    def create_dataset_table(table_path, column_list):
        # column_list: [{"name": "...", "type": "VARCHAR"}, ...]
        cols = [
            sql.SQL("{} {}").format(
                sql.Identifier(col["name"]),
                sql.SQL(col["type"])   # type is controlled by you, not user text
            )
            for col in column_list
        ]

        query = sql.SQL("CREATE TABLE {} ({})").format(
            sql.Identifier(table_path),
            sql.SQL(", ").join(cols)
        )

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(query)
            conn.commit()
        finally:
            cur.close()
            conn.close()

    def input_dataset_data(table_path, data):
        columns = list(data[0].keys())
        values = [list(d.values()) for d in data]

        conn = get_connection()
        cur = conn.cursor()

        try:
            query = sql.SQL("""
                INSERT INTO {table} ({fields})
                VALUES ({placeholders})
            """).format(
                table=sql.Identifier(table_path),
                fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
                placeholders=sql.SQL(", ").join(sql.Placeholder() * len(columns))
            )

            execute_batch(cur, query, values, page_size=1000)
            conn.commit()

        finally:
            cur.close()
            conn.close()

    create_dataset_table(table_path, column_list)
    input_dataset_data(table_path, data)

    query = """
        INSERT INTO datasets(project_id, dataset_id, table_path, n_past_week_for_training, n1_next_week_for_prediction, n2_next_week_for_prediction)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, (
        project_id, dataset_id, table_path, n_past_week_for_training, n1_next_week_for_prediction, n2_next_week_for_prediction
    ))

    conn.commit()
    cur.close()
    conn.close()


def db_create_column(project_id, dataset_id, column_name, column_type):
    query = """
        INSERT INTO enriched_columns(project_id, dataset_id, column_name, column_type)
        VALUES (%s, %s, %s, %s)
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, (
        project_id, dataset_id, column_name, column_type
    ))

    conn.commit()
    cur.close()
    conn.close()

def db_update_column(project_id, dataset_id, column_name, is_forecast_key=None, is_target=None, is_date=None, is_feature=None):
    query = """
        UPDATE enriched_columns
        SET is_forecast_key = %s, is_target = %s, is_date=%s, is_feature=%s
        WHERE project_id = %s AND dataset_id = %s AND column_name = %s
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, (
        is_forecast_key, is_target, is_date, is_feature, project_id, dataset_id, column_name
    ))

    conn.commit()
    cur.close()
    conn.close()


def db_update_dataset(project_id, dataset_id, target_table_path):
    query = """
        UPDATE datasets
        SET target_table_path = %s
        WHERE project_id = %s AND dataset_id = %s 
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, (
        target_table_path, project_id, dataset_id,
    ))

    conn.commit()
    cur.close()
    conn.close()

def db_create_target_table(key_column, date_column, target_column, table_path, forecasting_horizon):
    query = f"""
        drop table if exists target_table__{table_path};

        create table target_table__{table_path} as 
        select s1.{key_column}, s1.{date_column}, s2.{date_column} as forecasting_date, s2.{target_column} as forecasting_target_value
        from {table_path} s1
        join {table_path} s2 on s1.{key_column} = s2.{key_column}
        where s2.{date_column}::date - s1.{date_column}::date = {forecasting_horizon} * 7; 
    """

    print(query)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query)

    conn.commit()
    cur.close()
    conn.close()

    return f"target_table__{table_path}"

def db_execute_sql_statement(sql_statement):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql_statement)
            
            return cursor.fetchall()
    finally:
        conn.close()