import httpx
from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
async def list_models(user = Depends(get_current_user)):
    """
    Proxies LiteLLM's /v1/models. Bose01's inference server is deployed
    separately from this codebase — if it isn't reachable yet, this
    returns an empty list rather than failing the whole frontend.
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{settings.litellm_url}/v1/models",
                                     headers={"Authorization": f"Bearer {settings.litellm_master_key}"}, timeout=5.0)
            resp.raise_for_status()
            return [{"id": m["id"]} for m in resp.json().get("data", [])]
        except httpx.HTTPError:
            return []
