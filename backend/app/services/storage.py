import boto3
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
import uuid
import os
from app.core.config import settings


class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                raise
    
    def upload_file(
        self,
        file_obj: BinaryIO,
        file_name: str,
        content_type: str,
        folder: str = "uploads",
    ) -> str:
        file_extension = os.path.splitext(file_name)[1]
        unique_name = f"{uuid.uuid4()}{file_extension}"
        key = f"{folder}/{unique_name}"
        
        self.s3_client.upload_fileobj(
            file_obj,
            self.bucket_name,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        
        return f"{settings.S3_ENDPOINT_URL}/{self.bucket_name}/{key}"
    
    def upload_bytes(
        self,
        data: bytes,
        file_name: str,
        content_type: str,
        folder: str = "uploads",
    ) -> str:
        file_extension = os.path.splitext(file_name)[1]
        unique_name = f"{uuid.uuid4()}{file_extension}"
        key = f"{folder}/{unique_name}"
        
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        
        return f"{settings.S3_ENDPOINT_URL}/{self.bucket_name}/{key}"
    
    def delete_file(self, file_url: str) -> bool:
        try:
            key = file_url.split(f"{self.bucket_name}/")[-1]
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False
    
    def get_presigned_url(self, file_url: str, expiration: int = 3600) -> str:
        key = file_url.split(f"{self.bucket_name}/")[-1]
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expiration,
        )


storage_service = StorageService()