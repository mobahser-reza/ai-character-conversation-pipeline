import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.schemas.common import (
    ApiKeyCreate,
    ApiKeyOut,
    ProviderConfigCreate,
    ProviderConfigOut,
)
from app.core.security import encrypt_secret
from app.infrastructure.db.models import ApiKey, ProviderConfig
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/api", tags=["provider-settings"], dependencies=[Depends(get_current_user)])


@router.post("/api-keys", response_model=ApiKeyOut, status_code=201)
async def upsert_api_key(payload: ApiKeyCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ApiKey).where(ApiKey.provider_name == payload.provider_name)
    )
    existing = result.scalar_one_or_none()
    encrypted = encrypt_secret(payload.api_key)
    if existing:
        existing.key_encrypted = encrypted
        existing.is_active = True
        await db.commit()
        await db.refresh(existing)
        return existing

    api_key = ApiKey(provider_name=payload.provider_name, key_encrypted=encrypted)
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key


@router.get("/api-keys", response_model=list[ApiKeyOut])
async def list_api_keys(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApiKey))
    return result.scalars().all()


@router.delete("/api-keys/{key_id}", status_code=204)
async def delete_api_key(key_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    api_key = await db.get(ApiKey, key_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="Key not found")
    await db.delete(api_key)
    await db.commit()


@router.post("/providers", response_model=ProviderConfigOut, status_code=201)
async def set_provider(payload: ProviderConfigCreate, db: AsyncSession = Depends(get_db)):
    if payload.is_default:
        result = await db.execute(
            select(ProviderConfig).where(ProviderConfig.capability == payload.capability)
        )
        for existing in result.scalars().all():
            existing.is_default = False

    config = ProviderConfig(**payload.model_dump())
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


@router.get("/providers", response_model=list[ProviderConfigOut])
async def list_providers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProviderConfig))
    return result.scalars().all()
