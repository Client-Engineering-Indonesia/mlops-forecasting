# db.py
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch, Json
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



def db_get_dataset_by_id(dataset_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM datasets WHERE dataset_id = %s",
                (dataset_id, ),
            )
            return cursor.fetchone()
    finally:
        conn.close()


def db_get_columns_by_datasetid(dataset_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM enriched_columns WHERE dataset_id = %s",
                (dataset_id, ),
            )
            return cursor.fetchall()
    finally:
        conn.close()


def db_get_feature_stores_by_projectid(project_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM feature_stores WHERE project_id = %s",
                (project_id, ),
            )
            return cursor.fetchall()
    finally:
        conn.close()



def db_get_feature_stores_by_id(feature_store_id):
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

def db_get_models_by_projectid(project_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT m.*, table_path "\
                    "FROM models m " \
                    "JOIN feature_stores f ON f.feature_store_id = m.feature_store_id " \
                    "WHERE m.project_id = %s",
                (project_id, ),
            )
            return cursor.fetchall()
    finally:
        conn.close()



def db_get_predictions_by_projectid(project_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM predictions WHERE project_id = %s",
                (project_id, ),
            )
            return cursor.fetchall()
    finally:
        conn.close()

def db_get_models_by_id(model_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM models WHERE model_id = %s",
                (model_id, ),
            )
            return cursor.fetchone()
    finally:
        conn.close()


def db_get_training_data(feature_store_id):
    def prep_training_data(base_data_table_path, target_data_table_path):
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT ",
                    (feature_store_id, ),
                )
                return cursor.fetchone()
        finally:
            conn.close()

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT f.*, target_data_table_path FROM feature_stores f JOIN datasets d ON d.dataset_id = f.dataset_id WHERE m.feature_store_id = %s",
                (feature_store_id, ),
            )
            return cursor.fetchone()
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


def db_insert_model(
        project_id, 
        dataset_id, 
        feature_store_id, 
        model_id, 
        training_evaluation, 
        testing_evaluation, 
        training_pred_file_path, 
        model_file_path,
        algorithm_used="xgboost"):
    query = """
        INSERT INTO models(
            project_id, 
            dataset_id, 
            feature_store_id, 
            model_id, 
            training_evaluation, 
            testing_evaluation, 
            training_pred_file_path, 
            model_file_path,
            algorithm_used
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, (
        project_id, 
        dataset_id, 
        feature_store_id, 
        model_id, 
        Json(training_evaluation), 
        Json(testing_evaluation), 
        training_pred_file_path, 
        model_file_path,
        algorithm_used,
    ))

    conn.commit()
    cur.close()
    conn.close()


def db_insert_selected_features(project_id, dataset_id, feature_store_id, model_id, column_name):
    query = """
        INSERT INTO selected_features(
            project_id, 
            dataset_id, 
            feature_store_id, 
            model_id, 
            column_name
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, (
        project_id, 
        dataset_id, 
        feature_store_id, 
        model_id, 
        column_name,
    ))

    conn.commit()
    cur.close()
    conn.close()


def db_insert_predictions(project_id, dataset_id, feature_store_id, model_id, pred_file_path):
    query = """
        INSERT INTO predictions(
            project_id, 
            dataset_id, 
            feature_store_id, 
            model_id, 
            pred_file_path
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, (
        project_id, 
        dataset_id, 
        feature_store_id, 
        model_id, 
        pred_file_path,
    ))

    conn.commit()
    cur.close()
    conn.close()

def db_get_selected_features_by_modelid(model_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM selected_features WHERE model_id = %s",
                (model_id, ),
            )
            return cursor.fetchall()
    finally:
        conn.close()

def db_upload_test_file(table_path, data, columns, project_id, dataset_id, is_test_file="Y"):

    def create_test_file_table(table_path, column_list):
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

    create_test_file_table(table_path, columns)
    input_dataset_data(table_path, data)

    query = """
        INSERT INTO datasets(project_id, dataset_id, raw_data_table_path, is_test_file)
        VALUES (%s, %s, %s, %s)
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, (
        project_id, dataset_id, table_path, is_test_file,
    ))

    conn.commit()
    cur.close()
    conn.close()

    return table_path