import os
import boto3
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

endpoint = os.getenv("R2_ENDPOINT")
access_key = os.getenv("R2_ACCESS_KEY")
secret_key = os.getenv("R2_SECRET_KEY")
bucket = os.getenv("R2_BUCKET", "certificates")

print(f"Connecting to R2 bucket '{bucket}'...")

s3 = boto3.client(
    "s3",
    endpoint_url=endpoint,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    config=Config(signature_version="s3v4"),
    region_name="auto",
)

test_key = "test_connection.txt"
test_content = b"R2 read/write test successful!"

# 1. Write
print(f"1. Uploading test file to {test_key}...")
s3.put_object(Bucket=bucket, Key=test_key, Body=test_content, ContentType="text/plain")
print("   -> Upload OK")

# 2. Read
print(f"2. Downloading test file {test_key}...")
resp = s3.get_object(Bucket=bucket, Key=test_key)
data = resp["Body"].read()
print(f"   -> Read OK: {data.decode()}")

# 3. Delete
print(f"3. Cleaning up {test_key}...")
s3.delete_object(Bucket=bucket, Key=test_key)
print("   -> Cleanup OK")

print("\nSUCCESS: R2 read and write permissions verified!")
