from sqlalchemy import select

from app.core.security import decrypt_secret
from app.infrastructure.db.models import ApiKey
from app.infrastructure.db.session import SessionLocal


async def get_decrypted_key(provider_name: str) -> str:
    async with SessionLocal() as db:
        result = await db.execute(
            select(ApiKey).where(ApiKey.provider_name == provider_name, ApiKey.is_active.is_(True))
        )
        record = result.scalar_one_or_none()
        if record is None:
            raise RuntimeError(
                f"No active API key stored for provider '{provider_name}'. Add one in the API Key Manager."
            )
        return decrypt_secret(record.key_encrypted)
