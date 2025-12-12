from pathlib import Path
import yaml
from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import String, Integer, Float, Date
from dotenv import load_dotenv
import os

# -------------------------------------------------
# Load environment variables from .env file
# -------------------------------------------------
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# Build DATABASE_URL dynamically
DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Create DB engine
engine = create_engine(DATABASE_URL, echo=True)

# Mapping YAML types → SQLAlchemy types
TYPE_MAP = {
    "varchar": String,
    "string": String,
    "integer": Integer,
    "int": Integer,
    "float": Float,
    "date": Date,
    "jsonb": JSONB,
    "timestamptz": DateTime(timezone=True),
}


def load_yaml_schema(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def build_metadata(schema: dict) -> MetaData:
    metadata = MetaData()

    for table_def in schema.get("tables", []):
        table_name = table_def["table_name"]
        columns = []

        for col in table_def["columns"]:
            col_name = col["name"]
            col_type = col["type"].lower()
            default = col.get("default")

            if col_type not in TYPE_MAP:
                raise ValueError(f"Unsupported type: {col_type}")

            sqlalchemy_type = TYPE_MAP[col_type]
            kwargs = {}

            # Default value handling
            if default is not None and str(default).lower() != "null":
                if isinstance(default, str) and default.lower() == "now()":
                    kwargs["server_default"] = text("NOW()")
                else:
                    if isinstance(default, str):
                        kwargs["server_default"] = text(f"'{default}'")
                    else:
                        kwargs["server_default"] = text(str(default))

            columns.append(Column(col_name, sqlalchemy_type, **kwargs))

        Table(table_name, metadata, *columns)

    return metadata


def recreate_tables(path):
    schema = load_yaml_schema(path)
    metadata = build_metadata(schema)

    print("Dropping & creating tables from YAML schema...")
    metadata.drop_all(bind=engine)
    metadata.create_all(bind=engine)
    print("DONE.")

