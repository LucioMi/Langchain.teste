import httpx
from .config import settings

async def send_text(number: str, text: str, options: dict | None = None):
    base = settings.evolution_base_url.rstrip('/')
    url = f"{base}/message/sendText/{settings.evolution_instance}"
    body = {"number": number, "text": text, "options": options or {"linkPreview": True}}
    headers = {
        "Content-Type": "application/json",
        "apikey": settings.evolution_token,
        # Ajuda a bypassar o lembrete do localtunnel em alguns casos
        "bypass-tunnel-reminder": "1",
        "User-Agent": "httpx"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=body, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()