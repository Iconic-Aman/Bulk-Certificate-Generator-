import os
import boto3
from botocore.config import Config

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_BUCKET = os.getenv("R2_BUCKET", "certificates")


_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
    return _s3_client


def upload_bytes(key: str, data: bytes, content_type: str = "application/pdf") -> str:
    client = get_s3_client()
    client.put_object(
        Bucket=R2_BUCKET,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return key


def get_bytes(key: str) -> bytes:
    client = get_s3_client()
    resp = client.get_object(Bucket=R2_BUCKET, Key=key)
    return resp["Body"].read()


def get_presigned_url(key: str, filename: str = "", expires_in: int = 3600) -> str:
    client = get_s3_client()
    params = {"Bucket": R2_BUCKET, "Key": key}
    if filename:
        params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'
    return client.generate_presigned_url(
        "get_object",
        Params=params,
        ExpiresIn=expires_in,
    )
