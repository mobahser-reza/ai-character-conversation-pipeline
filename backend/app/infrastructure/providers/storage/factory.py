from functools import lru_cache

from app.core.config import get_settings
from app.domain.interfaces.providers import StorageProvider


@lru_cache
def get_storage_provider() -> StorageProvider:
    backend = get_settings().storage_backend
    if backend == "local":
        from app.infrastructure.providers.storage.local_disk import LocalDiskStorageProvider

        return LocalDiskStorageProvider()
    if backend == "s3":
        from app.infrastructure.providers.storage.s3 import S3StorageProvider

        return S3StorageProvider()
    raise ValueError(f"Unknown storage backend: {backend}")
