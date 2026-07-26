import os
import shutil

from app.core.config import get_settings
from app.domain.interfaces.providers import StorageProvider


class LocalDiskStorageProvider(StorageProvider):
    name = "local_disk"

    def __init__(self) -> None:
        self.base_path = get_settings().storage_local_path
        os.makedirs(self.base_path, exist_ok=True)

    async def save(self, local_path: str, key: str) -> str:
        dest_path = os.path.join(self.base_path, key)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copyfile(local_path, dest_path)
        return f"/media/{key}"

    async def resolve(self, key: str) -> str:
        return f"/media/{key}"
