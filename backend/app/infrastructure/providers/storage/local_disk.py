import os
import shutil

from app.core.config import get_settings
from app.domain.interfaces.providers import StorageProvider


class LocalDiskStorageProvider(StorageProvider):
    name = "local_disk"

    def __init__(self) -> None:
        settings = get_settings()
        self.base_path = settings.storage_local_path
        self.public_base_url = settings.public_base_url.rstrip("/")
        os.makedirs(self.base_path, exist_ok=True)

    async def save(self, local_path: str, key: str) -> str:
        dest_path = os.path.join(self.base_path, key)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copyfile(local_path, dest_path)
        return f"{self.public_base_url}/media/{key}"

    async def resolve(self, key: str) -> str:
        return f"{self.public_base_url}/media/{key}"
