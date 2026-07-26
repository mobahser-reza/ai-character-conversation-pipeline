import uuid
from urllib.parse import urlparse

from app.core.config import get_settings


def media_url_to_local_path(url: str) -> str:
    """Resolves a "/media/<key>" URL (LocalDiskStorageProvider) back to its file path.
    Only supported for the local storage backend, which is the default for stub/dev mode."""
    key = urlparse(url).path.removeprefix("/media/")
    return f"{get_settings().storage_local_path}/{key}"


def new_tmp_path(suffix: str) -> str:
    return f"/tmp/{uuid.uuid4()}{suffix}"
