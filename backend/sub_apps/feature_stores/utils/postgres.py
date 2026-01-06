# db.py
import psycopg2
from psycopg2.extras import RealDictCursor

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



def db_get_project_by_id(project_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM projects WHERE project_id = %s",
                (project_id, ),
            )
            return cursor.fetchone()
    finally:
        conn.close()


def db_get_dataset_by_id(dataset_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM datasets WHERE dataset_id = %s",
                (dataset_id, ),
            )
            return cursor.fetchone()
    finally:
        conn.close()


def db_list_datasets_by_projectid(project_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM datasets WHERE project_id = %s",
                (project_id, ),
            )
            return cursor.fetchall()
    finally:
        conn.close()

def db_create_table(sql_statement):

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(sql_statement)
        print("success")
    except Exception as e:
        return str(e)
    
    conn.commit()
    cur.close()
    conn.close()

    return "success"


def db_get_feature_store_by_fsid(feature_store_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM feature_stores WHERE feature_store_id = %s",
                (feature_store_id, ),
            )
            return cursor.fetchone()
    finally:
        conn.close()

def db_insert_to_feature_store_columns(project_id, dataset_id, feature_store_id, column_name):
    query = """
        INSERT INTO feature_stores_columns(project_id, dataset_id, feature_store_id, column_name)
        VALUES (%s, %s, %s, %s)
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, (
        project_id,
        dataset_id,
        feature_store_id,
        column_name,
    ))

    conn.commit()
    cur.close()
    conn.close()

def db_insert_to_feature_store(project_id, dataset_id, feature_store_id, table_path, sql_statement):
    query = """
        INSERT INTO feature_stores(project_id, dataset_id, feature_store_id, table_path, sql_statement)
        VALUES (%s, %s, %s, %s, %s)
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, (
        project_id,
        dataset_id,
        feature_store_id,
        table_path,
        sql_statement
    ))

    conn.commit()
    cur.close()
    conn.close()

def delete_tables(tables):
    for tbl in tables:
        query = f"DROP TABLE {tbl}"

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(query)

        conn.commit()
        cur.close()
        conn.close()


def db_get_table_sample_data(table_name, limit=5):
    def get_total_rows(table_name):
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT COUNT(*) as total_rows FROM {table_name}",
                )
                return cursor.fetchone()
        finally:
            conn.close()

    def get_sample_data(table_name):
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT * FROM {table_name} LIMIT {limit}",
                )
                return cursor.fetchall()
        finally:
            conn.close()

    return {
        "total_rows": get_total_rows(table_name),
        "sample_data": get_sample_data(table_name)
    }


def db_get_min_max_date(table_name, date_column, limit=5):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT MIN({date_column}) as earliest_date, MAX({date_column}) as latest_date FROM {table_name} LIMIT {limit}",
            )
            return cursor.fetchall()
    finally:
        conn.close()

def db_get_target_overview(table_name, target_column, limit=5):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT {target_column}, COUNT(*) as total_rows FROM {table_name} GROUP BY {target_column} LIMIT {limit}",
            )
            return cursor.fetchall()
    finally:
        conn.close()


def db_get_key_overview(table_name, key_column, limit=5):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT {key_column}, COUNT(*) as total_rows FROM {table_name} GROUP BY {key_column} LIMIT {limit}",
            )
            return cursor.fetchall()
    finally:
        conn.close()
    

def db_get_features_by_projectid(project_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT f.*, d.base_data_table_path, c.column_name " \
                "FROM feature_stores f " \
                "JOIN datasets d ON d.dataset_id = f.dataset_id " \
                "JOIN feature_stores_columns c ON c.feature_store_id = f.feature_store_id " \
                "WHERE f.project_id = %s ",
                (project_id, )
            )

            return cursor.fetchall()

        
    finally:
        conn.close()


def db_get_columns_by_datasetid(dataset_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM enriched_columns WHERE dataset_id = %s ",
                (dataset_id, )
            )

            return cursor.fetchall()

        
    finally:
        conn.close()

def db_execute_sql(sql_statement):
    print(sql_statement)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql_statement)
            columns = [col[0] for col in cursor.description]
            return cursor.fetchall()
        
    finally:
        conn.close()