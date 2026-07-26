import os

from app.core.config import get_settings
from app.domain.interfaces.providers import StorageProvider


class S3StorageProvider(StorageProvider):
    name = "s3"

    def __init__(self) -> None:
        import boto3

        settings = get_settings()
        self.bucket = settings.storage_s3_bucket
        self.endpoint = settings.storage_s3_endpoint
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.storage_s3_endpoint or None,
            aws_access_key_id=settings.storage_s3_access_key,
            aws_secret_access_key=settings.storage_s3_secret_key,
        )

    async def save(self, local_path: str, key: str) -> str:
        self.client.upload_file(local_path, self.bucket, key)
        return await self.resolve(key)

    async def resolve(self, key: str) -> str:
        base = self.endpoint or f"https://{self.bucket}.s3.amazonaws.com"
        return f"{base.rstrip('/')}/{self.bucket}/{key}"
