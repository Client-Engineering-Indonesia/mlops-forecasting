import pandas as pd
import numpy as np
import uuid
import logging
import io
import os
import json
import socket
import joblib
import pickle
from pathlib import Path
from datetime import datetime
from typing import Iterable, Any, Optional

# SQLAlchemy Imports
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Float, JSON, text, LargeBinary
from sqlalchemy.orm import declarative_base, sessionmaker

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================
# Database Configuration
# ==========================

# Environment (prefer POSTGRES_* to align with .env)
DB_USER = os.environ.get("POSTGRES_USER") or os.environ.get("DB_USER") or "postgres"
DB_PASS = os.environ.get("POSTGRES_PASSWORD") or os.environ.get("DB_PASS") or "postgres"
DB_HOST = os.environ.get("POSTGRES_HOST") or os.environ.get("DB_HOST") or "localhost"
DB_PORT = os.environ.get("POSTGRES_PORT") or os.environ.get("DB_PORT") or "5432"
DB_NAME = os.environ.get("POSTGRES_DB") or os.environ.get("DB_NAME") or "ml_lifecycle"

if os.environ.get("POSTGRES_HOST"):
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    connect_args = {}
else:
    # Fallback to SQLite when Postgres env is not provided
    DATABASE_URL = "sqlite:///./ml_lifecycle.db"
    connect_args = {"check_same_thread": False}

# ==========================
# COS Configuration
# ==========================
COS_API_KEY = os.environ.get("COS_API_KEY", "51C4_YbyMlAUtOvVS8kr6mcLN2vynD6EIu2slDkAWjKK")
COS_INSTANCE_CRN = os.environ.get("COS_INSTANCE_CRN", "crn:v1:bluemix:public:cloud-object-storage:global:a/a704679d44274f75b74b60a5a7c9ddd1:c93698cb-4ddb-48e6-947c-e3bd7951b3ab::")
COS_S3_ENDPOINT = os.environ.get("COS_S3_ENDPOINT", "https://s3.us-south.cloud-object-storage.appdomain.cloud")
COS_BUCKET = os.environ.get("COS_BUCKET", "mandiriforecasting-donotdelete-pr-iazsd30vb3oqyk")

# SQLAlchemy Setup
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================
# Database Models
# ==========================

class DatasetRegistry(Base):
    __tablename__ = "dataset_registry"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    target_column = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    content = Column(LargeBinary, nullable=True) 

class FeatureEngineeredTable(Base):
    __tablename__ = "engineered_datasets"
    
    dataset_id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)
    table_name = Column(String, nullable=False) 
    created_at = Column(DateTime, default=datetime.utcnow)

class FeatureSelectionRun(Base):
    __tablename__ = "feature_selection_runs"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)
    dataset_id = Column(String, nullable=False)
    target_column = Column(String, nullable=False)
    selected_features = Column(JSON, nullable=False) 
    dropped_features = Column(JSON, nullable=True)   
    created_at = Column(DateTime, default=datetime.utcnow)

class TrainedModel(Base):
    __tablename__ = "models"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    project_id = Column(String, nullable=False)
    dataset_id = Column(String, nullable=False)
    selection_id = Column(String, nullable=True)
    task_type = Column(String, nullable=False)
    target_column = Column(String, nullable=False)
    metrics = Column(JSON, nullable=False)
    artifact_path = Column(String, nullable=True)
    cos_path = Column(String, nullable=True)  # COS storage path
    created_at = Column(DateTime, default=datetime.utcnow)

class PredictionRun(Base):
    __tablename__ = "prediction_runs"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)
    model_id = Column(String, nullable=False)
    dataset_id = Column(String, nullable=False)
    status = Column(String, nullable=False) # 'completed', 'failed'
    output_path = Column(String, nullable=True) # Params for download
    created_at = Column(DateTime, default=datetime.utcnow)

# ==========================
# Database Helper Functions
# ==========================

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_raw_dataset(dataset_id: str, project_id: str, name: str, filename: str, df: pd.DataFrame):
    db = SessionLocal()
    try:
        # Define table name for raw data
        table_name = f"raw_{dataset_id.replace('-', '_')}"
        
        # Save Metadata
        entry = DatasetRegistry(
            id=dataset_id,
            project_id=project_id,
            name=name,
            filename=filename,
        )
        db.add(entry)
        db.commit()
        
        # Save Data to Table
        if engine.dialect.name == "postgresql":
             schema = os.environ.get("DB_SCHEMA", "public")
             with engine.begin() as conn:
                conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
             
             df.to_sql(table_name, engine, if_exists='replace', index=False, schema=schema)
        else:
             df.to_sql(table_name, engine, if_exists='replace', index=False)
             
        logger.info(f"Saved raw dataset {dataset_id} to table {table_name}")
        
    finally:
        db.close()

def load_raw_dataset(dataset_id: str) -> pd.DataFrame:
    db = SessionLocal()
    try:
        entry = db.query(DatasetRegistry).filter_by(id=dataset_id).first()
        if not entry:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        table_name = f"raw_{dataset_id.replace('-', '_')}"
        
        # Read from table
        if engine.dialect.name == "postgresql":
             schema = os.environ.get("DB_SCHEMA", "public")
             return pd.read_sql_table(table_name, engine, schema=schema)
        else:
             return pd.read_sql_table(table_name, engine)
    finally:
        db.close()

def save_engineered_dataset(dataset_id: str, project_id: str, df: pd.DataFrame):
    db = SessionLocal()
    table_name = f"feat_{dataset_id.replace('-', '_')}"
    try:
        # Record metadata
        existing = db.query(FeatureEngineeredTable).filter_by(dataset_id=dataset_id).first()
        if not existing:
            entry = FeatureEngineeredTable(
                dataset_id=dataset_id,
                project_id=project_id,
                table_name=table_name
            )
            db.add(entry)
            db.commit()
        
        # Write actual data
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        logger.info(f"Saved engineered data to table {table_name}")
    finally:
        db.close()

def load_engineered_dataset(dataset_id: str) -> pd.DataFrame:
    db = SessionLocal()
    try:
        entry = db.query(FeatureEngineeredTable).filter_by(dataset_id=dataset_id).first()
        if not entry:
            raise ValueError(f"Engineered dataset {dataset_id} not found in registry")
        
        return pd.read_sql_table(entry.table_name, engine)
    finally:
        db.close()

def save_feature_selection(run_id: str, project_id: str, dataset_id: str, target_col: str, selected: list, dropped: list):
    db = SessionLocal()
    try:
        entry = FeatureSelectionRun(
            id=run_id,
            project_id=project_id,
            dataset_id=dataset_id,
            target_column=target_col,
            selected_features=selected,
            dropped_features=dropped
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()

def get_feature_selection(run_id: str):
    db = SessionLocal()
    try:
        return db.query(FeatureSelectionRun).filter_by(id=run_id).first()
    finally:
        db.close()

def save_model_metadata(model_id: str, name: str, project_id: str, dataset_id: str, selection_id: str, task: str, target: str, metrics: dict):
    db = SessionLocal()
    try:
        entry = TrainedModel(
            id=model_id,
            name=name,
            project_id=project_id,
            dataset_id=dataset_id,
            selection_id=selection_id,
            task_type=task,
            target_column=target,
            metrics=metrics
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()

def save_prediction_run(run_id: str, project_id: str, model_id: str, dataset_id: str, status: str, output_path: str):
    db = SessionLocal()
    try:
        entry = PredictionRun(
            id=run_id,
            project_id=project_id,
            model_id=model_id,
            dataset_id=dataset_id,
            status=status,
            output_path=output_path
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()

def get_prediction_run(run_id: str):
    db = SessionLocal()
    try:
        return db.query(PredictionRun).filter_by(id=run_id).first()
    finally:
        db.close()

def save_prediction_result_table(run_id: str, df: pd.DataFrame):
    """
    Saves prediction result to a dynamic table `pred_res_{run_id}`.
    """
    table_name = f"pred_res_{run_id.replace('-', '_')}"
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    return table_name

def upload_external_prediction(project_id: str, filename: str, content: bytes) -> str:
    """
    Uploads an external prediction CSV to Postgres.
    Returns the table name.
    """
    try:
        # Read CSV content
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        # Validate content (optional: check for minimum rows/cols)
        if df.empty:
            raise ValueError("Uploaded file is empty")
            
        # Generate ID and Table Name
        pred_id = str(uuid.uuid4())
        table_name = f"ext_pred_{pred_id.replace('-', '_')}"
        
        # Save to Postgres
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        logger.info(f"External prediction saved to table {table_name}")
        
        return table_name, pred_id
        
    except Exception as e:
        logger.error(f"Failed to upload external prediction: {e}")
        raise ValueError(f"Failed to process file: {str(e)}")

def load_prediction_result_table(table_name: str) -> pd.DataFrame:
    return pd.read_sql_table(table_name, engine)

def delete_project_resources(project_id: str):
    """
    Cascade delete all resources for a project.
    """
    db = SessionLocal()
    try:
        # 1. Drop Engineered & Raw Tables
        # Find all datasets
        datasets = db.query(DatasetRegistry).filter_by(project_id=project_id).all()
        for ds in datasets:
            # Drop Engineered
            feat = db.query(FeatureEngineeredTable).filter_by(dataset_id=ds.id).first()
            if feat:
                try:
                    with engine.connect() as conn:
                        conn.execute(text(f"DROP TABLE IF EXISTS {feat.table_name}"))
                        conn.commit()
                except Exception as e:
                    logger.warning(f"Failed to drop table {feat.table_name}: {e}")
            
            # Drop Raw
            raw_table_name = f"raw_{ds.id.replace('-', '_')}"
            try:
                with engine.connect() as conn:
                    schema = os.environ.get("DB_SCHEMA", "public")
                    full_name = f'"{schema}"."{raw_table_name}"' if engine.dialect.name == "postgresql" else f'"{raw_table_name}"'
                    
                    conn.execute(text(f"DROP TABLE IF EXISTS {full_name}"))
                    conn.commit()
            except Exception as e:
                logger.warning(f"Failed to drop table {raw_table_name}: {e}")
        
        # 2. Drop Prediction Result Tables
        predictions = db.query(PredictionRun).filter_by(project_id=project_id).all()
        for p in predictions:
            if p.output_path and p.output_path.startswith("pred_res_"):
                try:
                    with engine.connect() as conn:
                        conn.execute(text(f"DROP TABLE IF EXISTS {p.output_path}"))
                        conn.commit()
                except Exception as e:
                    logger.warning(f"Failed to drop table {p.output_path}: {e}")

        # 3. Delete Metadata Records
        db.query(PredictionRun).filter_by(project_id=project_id).delete()
        db.query(TrainedModel).filter_by(project_id=project_id).delete()
        db.query(FeatureSelectionRun).filter_by(project_id=project_id).delete()
        db.query(FeatureEngineeredTable).filter_by(project_id=project_id).delete()
        db.query(DatasetRegistry).filter_by(project_id=project_id).delete()
        
        db.commit()
    finally:
        db.close()


# ==========================
# Data Processing Logic (Internal)
# ==========================

def _load_env_file_internal(path: str = ".env") -> bool:
    env_path = Path(path)
    if not env_path.exists():
        return False
    # ... Simplified loaded mostly used by main/standalone, not critical for service if env already loaded by uvicorn/dotenv
    return True

def engineer_memory_features(
    df: pd.DataFrame,
    value_col: str = "Value",
    high_threshold: float = 70.0,
    target_threshold: float = 80.0,
    future_horizon_days: int = 21,
) -> pd.DataFrame:
    df = df.copy()
    if "Date" not in df.columns:
        # Fallback or strict fail? df should be validated before.
        pass
        
    df["Date"] = pd.to_datetime(df["Date"])

    group_cols = ["Type", "Application", "IP"]
    # Ensure expected columns exist or fail
    if not set(group_cols).issubset(df.columns):
         # If raw data doesn't have these, we might have issue. 
         pass
         
    df = df.sort_values(group_cols + ["Date"])

    df["Date_Next_2Weeks"] = df["Date"] + pd.Timedelta(days=14)
    df["Date_Next_3Weeks"] = df["Date"] + pd.Timedelta(days=21)

    def _per_device(group: pd.DataFrame) -> pd.DataFrame:
        if not set(group_cols).issubset(group.columns):
            key = group.name
            if not isinstance(key, tuple):
                key = (key,)
            for col, value in zip(group_cols, key):
                group[col] = value

        group = group.sort_values("Date").set_index("Date")

        v = group[value_col]
        idx = group.index
        horizon = pd.Timedelta(days=future_horizon_days)

        future_max_list = []
        for t in idx:
            mask = (idx > t) & (idx <= t + horizon)
            future_max_list.append(v[mask].max() if mask.any() else 0.0)

        group["Value_target_Max"] = future_max_list
        group["Target"] = (group["Value_target_Max"] >= target_threshold).astype(int)

        def past_rolling(series, window_str, func):
            rolled = getattr(series.rolling(window_str), func)()
            return rolled.shift(1)

        group["Value_Last_1Day"] = past_rolling(v, "1D", "max")
        group["Value_Last_3Days"] = past_rolling(v, "3D", "max")

        group["Date_Value_Last_28Days_SDev"] = past_rolling(v, "28D", "std")
        group["Date_Value_Last_28Days_Median"] = past_rolling(v, "28D", "median")

        above = (v > high_threshold).astype(int)
        group["Date_Count_Value_Above_70_Last_3Days"] = past_rolling(above, "3D", "sum")
        group["Date_Count_Value_Above_70_Last_7Days"] = past_rolling(above, "7D", "sum")
        group["Date_Count_Value_Above_70_Last_14Days"] = past_rolling(above, "14D", "sum")
        group["Date_Count_Value_Above_70_Last_28Days"] = past_rolling(above, "28D", "sum")

        def minmax_range_past(series, window_str):
            roll_max = series.rolling(window_str).max()
            roll_min = series.rolling(window_str).min()
            return (roll_max - roll_min).shift(1)

        group["Date_MinMax_Range_Last_3Days"] = minmax_range_past(v, "3D")
        group["Date_MinMax_Range_Last_7Days"] = minmax_range_past(v, "7D")
        group["Date_MinMax_Range_Last_14Days"] = minmax_range_past(v, "14D")
        group["Date_MinMax_Range_Last_28Days"] = minmax_range_past(v, "28D")

        return group.reset_index()

    grouped = df.groupby(group_cols, group_keys=False)
    try:
        applied = grouped.apply(_per_device, include_groups=False)
    except TypeError:
        applied = grouped.apply(_per_device)

    df_feat = applied.sort_values(group_cols + ["Date"]).reset_index(drop=True)
    return df_feat.fillna(0)


# ==========================
# Service Functions (Consolidated)
# ==========================

# Initialize DB on load
init_db()

def upload_dataset(project_id: str, file_name: str, content: bytes) -> str:
    dataset_id = str(uuid.uuid4())
    try:
        if file_name.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file_name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise ValueError("Unsupported file format. Only CSV and Excel are supported.")
            
        save_raw_dataset(dataset_id, project_id, file_name, file_name, df)
        logger.info(f"Dataset uploaded: {dataset_id}")
        return dataset_id
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise ValueError(f"Failed to process file: {str(e)}")

def list_datasets(project_id: str):
    session = SessionLocal()
    try:
        datasets = session.query(DatasetRegistry).filter_by(project_id=project_id).all()
        results = []
        for d in datasets:
            engineered = session.query(FeatureEngineeredTable).filter_by(dataset_id=d.id).first()
            results.append({
                "id": d.id,
                "name": d.name,
                "filename": d.filename,
                "has_engineered": engineered is not None,
                "created_at": d.created_at.isoformat()
            })
        return results
    finally:
        session.close()

def list_models(project_id: str):
    session = SessionLocal()
    try:
        models = session.query(TrainedModel).filter_by(project_id=project_id).all()
        results = []
        for m in models:
            results.append({
                "id": m.id,
                "name": m.name,
                "project_id": m.project_id,
                "dataset_id": m.dataset_id,
                "task_type": m.task_type,
                "target_column": m.target_column,
                "metrics": m.metrics,
                "cos_path": m.cos_path
            })
        return results
    finally:
        session.close()

def run_feature_engineering(dataset_id: str, project_id: str):
    try:
        # 1. Load Raw from Postgres
        df_raw = load_raw_dataset(dataset_id)
        logger.info(f"Loaded raw data for {dataset_id}: {df_raw.shape}")
        
        # 2. Engineer using internal logic
        value_col = "Value"
        # Optional validation
        
        df_feat = engineer_memory_features(df_raw, value_col=value_col)
        logger.info(f"Feature engineering complete. Shape: {df_feat.shape}")

        # 3. Save Engineered to Postgres
        save_engineered_dataset(dataset_id, project_id, df_feat)
        
        return {"status": "success", "columns": list(df_feat.columns)}
        
    except ValueError as ve:
        logger.error(f"FE Validation Error: {ve}")
        raise ValueError(f"Feature Engineering Validation Failed: {str(ve)}")
    except Exception as e:
        logger.error(f"FE Failed: {e}", exc_info=True)
        raise ValueError(f"Feature Engineering process failed: {str(e)}")

def run_feature_selection(dataset_id: str, project_id: str, target_column: str, top_k: int = 10):
    try:
        df = load_engineered_dataset(dataset_id)
        
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in dataset columns: {list(df.columns)}")
            
        numeric_df = df.select_dtypes(include=['number'])
        
        if target_column not in numeric_df.columns:
             raise ValueError(f"Target column '{target_column}' matches no numeric data for correlation check.")

        correlations = numeric_df.corr()[target_column].abs().sort_values(ascending=False)
        features_corr = correlations.drop(labels=[target_column], errors='ignore')
        selected = features_corr.head(top_k).index.tolist()
        
        all_numeric = [c for c in numeric_df.columns if c != target_column]
        dropped = [
            {"name": c, "reason": "Low correlation or outside top-k"} 
            for c in all_numeric if c not in selected
        ]
        
        run_id = str(uuid.uuid4())
        save_feature_selection(run_id, project_id, dataset_id, target_column, selected, dropped)
        
        return {
            "selection_id": run_id, 
            "selected_features": selected, 
            "dropped_features": dropped
        }
    except Exception as e:
        logger.error(f"Feature Selection Failed: {e}", exc_info=True)
        raise ValueError(f"Feature Selection failed: {str(e)}")

MODEL_DIR = "models_artifacts"
OUTPUT_DIR = "outputs"
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def train_model(dataset_id: str, selection_id: str, project_id: str, task_type: str):
    try:
        # 1. Get Selection Metadata
        selection = get_feature_selection(selection_id)
        if not selection:
            raise ValueError(f"Feature selection run {selection_id} not found/expired.")
            
        target = selection.target_column
        features = selection.selected_features
        
        # 2. Load Data from Postgres
        df = load_engineered_dataset(dataset_id)
        
        missing_feats = [f for f in features if f not in df.columns]
        if missing_feats:
             raise ValueError(f"Selected features missing from dataset: {missing_feats}")
        if target not in df.columns:
             raise ValueError(f"Target column {target} missing from dataset")
             
        X = df[features]
        y = df[target]
        
        # 3. Train with XGBoost
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, f1_score, mean_squared_error, r2_score, precision_score, recall_score
        import xgboost as xgb
        import pickle
        
        X = X.fillna(0) 
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        metrics = {}
        if task_type == 'classification':
            model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                eval_metric='logloss'
            )
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            metrics['accuracy'] = accuracy_score(y_test, preds)
            metrics['f1'] = f1_score(y_test, preds, average='weighted')
            metrics['precision'] = precision_score(y_test, preds, average='weighted', zero_division=0)
            metrics['recall'] = recall_score(y_test, preds, average='weighted', zero_division=0)
        else:
            model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            metrics['rmse'] = mean_squared_error(y_test, preds, squared=False)
            metrics['r2'] = r2_score(y_test, preds)

        # 4. Save Model Artifact as pickle
        model_id = str(uuid.uuid4())
        artifact_path = os.path.join(MODEL_DIR, f"{model_id}.pkl")
        with open(artifact_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Model artifact saved locally: {artifact_path}")

        # 5. Upload Model to COS
        cos_path = upload_model_to_cos(model, model_id)
        if cos_path:
            logger.info(f"Model uploaded to COS: {cos_path}")
        else:
            logger.warning(f"COS upload failed, model only available locally")

        # 6. Save Model Metadata
        save_model_metadata(model_id, f"{task_type.title()}Model-{model_id[:6]}", project_id, dataset_id, selection_id, task_type, target, metrics)
        
        # 7. Update artifact path and COS path
        session = SessionLocal()
        try:
            m = session.query(TrainedModel).filter_by(id=model_id).first()
            if m:
                m.artifact_path = artifact_path
                m.cos_path = cos_path
                session.commit()
        finally:
            session.close()
        
        logger.info(f"XGBoost model trained {model_id} with metrics {metrics}")
        
        return {
            "model_id": model_id,
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Training Failed: {e}", exc_info=True)
        raise ValueError(f"Model training failed: {str(e)}")


def run_prediction(model_id: str, dataset_id: str, project_id: str):
    try:
        # 1. Get Model Metadata
        session = SessionLocal()
        try:
             model_entry = session.query(TrainedModel).filter_by(id=model_id).first()
        finally:
             session.close()
             
        if not model_entry or not model_entry.artifact_path:
             raise ValueError(f"Model {model_id} not found or has no artifact.")
        
        # 2. Get Selection Metadata
        selection = get_feature_selection(model_entry.selection_id)
        if not selection:
             raise ValueError("Feature selection metadata missing for model.")
             
        # 3. Load Data & Model
        df = load_engineered_dataset(dataset_id)
        
        # Load model - try COS first, fallback to local file
        model = None
        
        # Try COS if path is available
        if model_entry.cos_path:
            logger.info(f"Attempting to load model from COS: {model_entry.cos_path}")
            model = download_model_from_cos(model_entry.cos_path)
            
            if model:
                logger.info(f"✅ Model loaded from COS successfully")
            else:
                logger.warning(f"⚠️ COS download failed, falling back to local file")
        
        # Fallback to local file
        if not model and model_entry.artifact_path:
            logger.info(f"Loading model from local file: {model_entry.artifact_path}")
            with open(model_entry.artifact_path, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"✅ Model loaded from local file successfully")
        
        if not model:
            raise ValueError(f"Failed to load model from both COS and local storage")
        
        # Prepare Features
        features = selection.selected_features
        missing = [f for f in features if f not in df.columns]
        if missing:
             raise ValueError(f"Dataset missing features required by model: {missing}")
        
        X = df[features].fillna(0)
        
        # 4. Predict
        preds = model.predict(X)
        
        # 5. Create Result DataFrame
        result_df = df.copy()
        pred_col = f"predicted_{model_entry.target_column}"
        result_df[pred_col] = preds
        
        # Filter for minimal output (Target + Predicted only)
        cols_to_keep = [pred_col]
        # Include original target if it exists for comparison
        if model_entry.target_column in df.columns:
            cols_to_keep.insert(0, model_entry.target_column)
            
        final_df = result_df[cols_to_keep]
        
        # 6. Save to Postgres
        prediction_id = str(uuid.uuid4())
        table_name = save_prediction_result_table(prediction_id, final_df)
        logger.info(f"Prediction saved to table {table_name}")
        
        # 7. Record Run
        save_prediction_run(
            run_id=prediction_id, 
            project_id=project_id, 
            model_id=model_id, 
            dataset_id=dataset_id, 
            status="completed", 
            output_path=table_name 
        )
        
        return {
            "prediction_id": prediction_id,
            "status": "completed",
            "output_table": table_name,
            "preview": result_df.head(5).to_dict(orient='records')
        }
        
    except Exception as e:
        logger.error(f"Prediction Failed: {e}", exc_info=True)
        raise ValueError(f"Prediction failed: {str(e)}")

def delete_project(project_id: str):
    try:
        delete_project_resources(project_id)
        return {"status": "success", "message": f"Project {project_id} deleted."}
    except Exception as e:
         logger.error(f"Delete project failed: {e}", exc_info=True)
         raise ValueError(f"Failed to delete project: {str(e)}")

def get_prediction_csv(prediction_id: str):
    run = get_prediction_run(prediction_id)
    if not run or not run.output_path:
        return None
    
    if run.output_path.startswith("pred_res_"):
        df = load_prediction_result_table(run.output_path)
        return df.to_csv(index=False)
    elif os.path.exists(run.output_path):
        return open(run.output_path, 'r').read()
    else:
        return None


# ==========================
# COS Helper Functions
# ==========================

def _get_cos_client():
    """Create and return IBM COS S3 client"""
    try:
        import ibm_boto3
        from ibm_botocore.client import Config
        
        client = ibm_boto3.client(
            service_name="s3",
            ibm_api_key_id=COS_API_KEY,
            ibm_service_instance_id=COS_INSTANCE_CRN,
            ibm_auth_endpoint="https://iam.cloud.ibm.com/identity/token",
            config=Config(signature_version="oauth"),
            endpoint_url=COS_S3_ENDPOINT,
        )
        return client
    except ImportError:
        logger.error("ibm_boto3 not installed. Install with: pip install ibm-cos-sdk")
        raise
    except Exception as e:
        logger.error(f"Failed to create COS client: {e}")
        raise

def upload_model_to_cos(model: Any, model_id: str) -> Optional[str]:
    """
    Upload trained model to IBM COS
    
    Args:
        model: Trained model object (XGBoost, sklearn, etc.)
        model_id: Unique identifier for the model
        
    Returns:
        COS path (e.g., "cos://bucket/models/{model_id}.pkl") or None if failed
    """
    try:
        s3 = _get_cos_client()
        object_key = f"models/{model_id}.pkl"
        
        # Serialize model
        binary_data = pickle.dumps(model)
        
        # Upload to COS
        s3.put_object(
            Bucket=COS_BUCKET,
            Key=object_key,
            Body=binary_data,
            ContentType="application/octet-stream"
        )
        
        cos_path = f"cos://{COS_BUCKET}/{object_key}"
        logger.info(f"✅ Model uploaded to COS: {cos_path}")
        
        return cos_path
        
    except Exception as e:
        logger.error(f"❌ Failed to upload model to COS: {e}")
        return None

def download_model_from_cos(cos_path: str) -> Optional[Any]:
    """
    Download and deserialize model from IBM COS
    
    Args:
        cos_path: COS path (e.g., "cos://bucket/models/{model_id}.pkl")
        
    Returns:
        Deserialized model object or None if failed
    """
    try:
        s3 = _get_cos_client()
        
        # Parse COS path
        # Format: cos://bucket/key
        if not cos_path.startswith("cos://"):
            raise ValueError(f"Invalid COS path format: {cos_path}")
        
        path_parts = cos_path.replace("cos://", "").split("/", 1)
        bucket = path_parts[0]
        object_key = path_parts[1] if len(path_parts) > 1 else ""
        
        # Download from COS
        response = s3.get_object(Bucket=bucket, Key=object_key)
        binary_data = response['Body'].read()
        
        # Deserialize model
        model = pickle.loads(binary_data)
        
        logger.info(f"✅ Model downloaded from COS: {cos_path}")
        return model
        
    except Exception as e:
        logger.error(f"❌ Failed to download model from COS: {e}")
        return None

def get_cos_url(cos_path: str) -> str:
    """
    Convert COS path to public S3 URL
    """
    if not cos_path.startswith("cos://"):
        return cos_path
    
    path_parts = cos_path.replace("cos://", "").split("/", 1)
    bucket = path_parts[0]
    object_key = path_parts[1] if len(path_parts) > 1 else ""
    
    return f"{COS_S3_ENDPOINT}/{bucket}/{object_key}"

def delete_model_from_cos(cos_path: str) -> bool:
    """
    Delete model from IBM COS
    """
    try:
        s3 = _get_cos_client()
        
        # Parse COS path
        if not cos_path.startswith("cos://"):
            raise ValueError(f"Invalid COS path format: {cos_path}")
        
        path_parts = cos_path.replace("cos://", "").split("/", 1)
        bucket = path_parts[0]
        object_key = path_parts[1] if len(path_parts) > 1 else ""
        
        # Delete from COS
        s3.delete_object(Bucket=bucket, Key=object_key)
        
        logger.info(f"✅ Model deleted from COS: {cos_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to delete model from COS: {e}")
        return False

def upload_model_to_cos_manual(project_id: str, model_id: str):
    """
    Manually upload a model to COS if it hasn't been uploaded yet or to retry.
    """
    session = SessionLocal()
    try:
        model_entry = session.query(TrainedModel).filter_by(id=model_id, project_id=project_id).first()
        if not model_entry:
            raise ValueError(f"Model {model_id} not found in project {project_id}")
            
        if not model_entry.artifact_path or not os.path.exists(model_entry.artifact_path):
             raise ValueError(f"Local model artifact not found at {model_entry.artifact_path}")
             
        # Load model logic to verify it works/exists
        with open(model_entry.artifact_path, 'rb') as f:
            model = pickle.load(f)
            
        # Upload
        cos_path = upload_model_to_cos(model, model_id)
        
        if not cos_path:
            raise ValueError("Failed to upload model to COS.")
            
        # Update DB
        model_entry.cos_path = cos_path
        session.commit()
        
        return {"status": "success", "cos_path": cos_path}
        
    except Exception as e:
        logger.error(f"Manual COS Upload Failed: {e}", exc_info=True)
        raise ValueError(f"COS upload failed: {str(e)}")
    finally:
        session.close()
