import pickle
from io import BytesIO

import ibm_boto3
from ibm_botocore.client import Config

from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

COS_API_KEY=os.getenv("COS_API_KEY")
COS_SERVICE_INSTANCE_ID=os.getenv("COS_SERVICE_INSTANCE_ID")
COS_ENDPOINT_URL=os.getenv("COS_ENDPOINT_URL")
COS_BUCKET_NAME=os.getenv("COS_BUCKET_NAME")


def get_cos_client():
    return ibm_boto3.client(
        "s3",
        ibm_api_key_id=COS_API_KEY,
        ibm_service_instance_id=COS_SERVICE_INSTANCE_ID,
        config=Config(signature_version="oauth"),
        endpoint_url=COS_ENDPOINT_URL,
    )

def upload_model_to_cos(
        model,
        object_key: str,
):
    
    buffer = model_to_buffer(model)

    cos_client = get_cos_client()
    cos_client.put_object(
        Bucket=COS_BUCKET_NAME,
        Key=object_key,
        Body=buffer.getvalue()
    )

    return COS_BUCKET_NAME + "/" + object_key

def model_to_buffer(model) -> BytesIO:
    buffer = BytesIO()
    pickle.dump(model, buffer)
    buffer.seek(0)  # IMPORTANT
    return buffer


def dataframe_to_csv_buffer(df: pd.DataFrame) -> BytesIO:
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer


def upload_buffer_to_cos(
        df,
        object_key: str,
        content_type="text/csv"
):
    buffer = dataframe_to_csv_buffer(df)

    cos_client = get_cos_client()
    cos_client.put_object(
        Bucket=COS_BUCKET_NAME,
        Key=object_key,
        Body=buffer.getvalue(),
        ContentType=content_type
    )

    return COS_BUCKET_NAME + "/" + object_key


def download_csv_to_file(
    object_key: str,
):
    cos_client = get_cos_client()
    clean_object_key = object_key.replace(COS_BUCKET_NAME+"/", "")
    obj = cos_client.get_object(
        Bucket=COS_BUCKET_NAME,
        Key=clean_object_key
    )

    return obj, clean_object_key

def download_model_pickle(full_file_path, local_path):
    cos_client = get_cos_client()

    object_key = full_file_path.replace(COS_BUCKET_NAME + "/", "")
    print(object_key)
    cos_client.download_file(COS_BUCKET_NAME, object_key, local_path)