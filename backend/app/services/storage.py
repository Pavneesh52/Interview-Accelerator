import boto3
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
import uuid
import os
from pathlib import Path
from app.core.config import settings


class StorageService:
    """File storage with automatic local-filesystem fallback when S3/MinIO is unavailable."""

    def __init__(self):
        self.bucket_name = settings.S3_BUCKET_NAME
        self._use_local = False
        self._local_root = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent / "local_uploads"

        try:
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
            )
            self._ensure_bucket_exists()
        except Exception as e:
            print(f"Warning: S3 client creation failed ({e}). Using local storage.")
            self._use_local = True
            self._ensure_local_dirs()

    def _ensure_bucket_exists(self):
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                except Exception:
                    print("Warning: Cannot create S3 bucket. Falling back to local storage.")
                    self._use_local = True
                    self._ensure_local_dirs()
            else:
                print(f"Warning: S3 error ({e}). Falling back to local storage.")
                self._use_local = True
                self._ensure_local_dirs()
        except Exception as e:
            print(f"Warning: S3 unreachable ({e}). Falling back to local storage.")
            self._use_local = True
            self._ensure_local_dirs()

    def _ensure_local_dirs(self):
        for folder in ("uploads", "job_descriptions", "resumes"):
            (self._local_root / folder).mkdir(parents=True, exist_ok=True)

    # ── uploads ──────────────────────────────────────────────

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

        if self._use_local:
            return self._local_write(key, file_obj.read())

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

        if self._use_local:
            return self._local_write(key, data)

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return f"{settings.S3_ENDPOINT_URL}/{self.bucket_name}/{key}"

    # ── delete / presigned ───────────────────────────────────

    def delete_file(self, file_url: str) -> bool:
        if self._use_local:
            path = self._local_root / file_url.replace("local://", "")
            try:
                path.unlink(missing_ok=True)
                return True
            except Exception:
                return False
        try:
            key = file_url.split(f"{self.bucket_name}/")[-1]
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False

    def get_presigned_url(self, file_url: str, expiration: int = 3600) -> str:
        if self._use_local:
            return file_url  # no presigning needed for local files
        key = file_url.split(f"{self.bucket_name}/")[-1]
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expiration,
        )

    # ── local helpers ────────────────────────────────────────

    def _local_write(self, key: str, data: bytes) -> str:
        dest = self._local_root / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return f"local://{key}"


storage_service = StorageService()