from functools import lru_cache
import boto3
from botocore.config import Config
from config.settings import settings

class MediaStorageNotConfigured(RuntimeError):
    pass

@lru_cache(maxsize=1)
def client():
    if not settings.media_bucket or not settings.media_access_key_id or not settings.media_secret_access_key:
        raise MediaStorageNotConfigured("Configure MEDIA_BUCKET, MEDIA_ACCESS_KEY_ID and MEDIA_SECRET_ACCESS_KEY.")
    if settings.media_storage_driver.lower() != "s3":
        raise MediaStorageNotConfigured("Only the S3-compatible storage driver is enabled.")
    return boto3.client(
        "s3",
        endpoint_url=settings.media_endpoint_url or None,
        region_name=settings.media_region,
        aws_access_key_id=settings.media_access_key_id,
        aws_secret_access_key=settings.media_secret_access_key,
        config=Config(signature_version="s3v4"),
    )

def create_upload_form(object_key: str, content_type: str, file_size_bytes: int) -> dict:
    return client().generate_presigned_post(
        Bucket=settings.media_bucket,
        Key=object_key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", file_size_bytes, file_size_bytes],
        ],
        ExpiresIn=900,
    )

def inspect_uploaded_object(object_key: str) -> dict:
    return client().head_object(Bucket=settings.media_bucket, Key=object_key)

def create_playback_url(object_key: str, expires_in: int = 600) -> str:
    return client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.media_bucket, "Key": object_key},
        ExpiresIn=expires_in,
    )
