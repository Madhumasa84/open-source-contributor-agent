from fastapi import APIRouter

from app.ai.providers.registry import ProviderRegistry
from app.schemas.provider import ProviderDescriptor

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=list[ProviderDescriptor])
async def list_providers() -> list[ProviderDescriptor]:
    return ProviderRegistry().descriptors()
