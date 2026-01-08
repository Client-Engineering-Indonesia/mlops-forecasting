import yaml
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os
load_dotenv()


class PostgresIngestor:
    def __init__(self, host, port, db, user, password):
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=db,
            user=user,
            password=password
        )
        self.conn.autocommit = False

    def _load_yaml(self, yaml_path: str) -> dict:
        with open(yaml_path, "r") as f:
            return yaml.safe_load(f)

    def _format_default(self, default):
        """
        Format DEFAULT value safely for PostgreSQL
        """
        if default is None or str(default).upper() == "NULL":
            return None

        # SQL function (NOW(), gen_random_uuid(), etc.)
        if isinstance(default, str) and default.strip().endswith("()"):
            return default.strip()

        # String literal → quote and escape
        if isinstance(default, str):
            escaped = default.replace("'", "''")
            return f"'{escaped}'"

        # Numeric / boolean
        return str(default)

    def create_tables_from_yaml(self, yaml_path: str):
        config = self._load_yaml(yaml_path)
        tables = config.get("tables", [])

        if not tables:
            raise ValueError("No tables found in YAML")

        cursor = self.conn.cursor()

        try:
            for table in tables:
                table_name = table["table_name"]
                columns = table["columns"]

                column_defs = []

                for col in columns:
                    col_name = col["name"]
                    col_type = col["type"]
                    col_default = col.get("default")

                    default_sql = self._format_default(col_default)

                    if default_sql is None:
                        column_defs.append(
                            f"{col_name} {col_type}"
                        )
                    else:
                        column_defs.append(
                            f"{col_name} {col_type} DEFAULT {default_sql}"
                        )

                create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {', '.join(column_defs)}
                );
                """

                print(f"Creating table: {table_name}")
                cursor.execute(create_table_sql)

            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            raise e

        finally:
            cursor.close()

    def close(self):
        self.conn.close()


ingestor = PostgresIngestor(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    db=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD")
)

ingestor.create_tables_from_yaml("/Users/muhammadfadlyhidayat/Documents/ibm/IBM 2026/Machine Learning /Mandiri/mlops-forecasting/backend/table_schema.yaml")
ingestor.close()