import json
import httpx
from fastapi import APIRouter, WebSocket, status
from app.core.security import decode_token
from app.core.crypto import decrypt_api_key
from app.core.model_routing import build_litellm_overrides
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.message import Message
from app.models.connector import Connector
from app.config import settings

router = APIRouter()


@router.websocket("/ws/chat/{chat_id}")
async def chat_ws(websocket: WebSocket, chat_id: str):
    token = websocket.cookies.get("access_token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        user_id = decode_token(token)["sub"]
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    async with AsyncSessionLocal() as db:
        user = await db.get(User, user_id)
        if not user or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_json()
            content = raw.get("content", "").strip()
            if not content:
                await websocket.send_json({"type": "error", "content": "Empty message"})
                continue

            request_body = {"messages": [{"role": "user", "content": content}], "stream": True}
            model_label = raw.get("model")

            if raw.get("connector_id"):
                model_name = raw.get("model_name")
                if not model_name:
                    await websocket.send_json({"type": "error", "content": "No model name provided for connector"})
                    continue
                async with AsyncSessionLocal() as db:
                    connector = await db.get(Connector, raw["connector_id"])
                    if not connector or str(connector.user_id) != user_id or not connector.api_key_encrypted:
                        await websocket.send_json({"type": "error", "content": "Connector not configured"})
                        continue
                    api_key = decrypt_api_key(connector.api_key_encrypted)
                    overrides = build_litellm_overrides(connector, model_name, api_key)
                request_body.update(overrides)
                model_label = f"{connector.provider}:{model_name}"
            elif raw.get("model"):
                request_body["model"] = raw["model"]
            else:
                await websocket.send_json({"type": "error", "content": "No model or connector selected"})
                continue

            async with AsyncSessionLocal() as db:
                db.add(Message(chat_id=chat_id, role="user", content=content))
                await db.commit()

            full_response = ""
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST", f"{settings.litellm_url}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.litellm_master_key}"},
                    json=request_body,
                ) as resp:
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        payload = line[len("data: "):]
                        if payload.strip() == "[DONE]":
                            break
                        delta = json.loads(payload)["choices"][0]["delta"].get("content", "")
                        if delta:
                            full_response += delta
                            await websocket.send_json({"type": "token", "content": delta})

            async with AsyncSessionLocal() as db:
                db.add(Message(chat_id=chat_id, role="assistant", content=full_response, model_name=model_label))
                await db.commit()
    except Exception:
        await websocket.close()
