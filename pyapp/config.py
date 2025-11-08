from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass
class Settings:
    port: int = int(os.getenv("PORT", "5678"))
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "")
    system_prompt: str = os.getenv(
        "SYSTEM_PROMPT",
        "Você é um assistente curto e objetivo. Responda em português e em uma única frase.",
    )
    memory_backend: str = os.getenv("MEMORY_BACKEND", "sqlite")
    sqlite_db_path: str = os.getenv("SQLITE_DB_PATH", "pyapp.db")
    memory_max_messages: int = int(os.getenv("MEMORY_MAX_MESSAGES", "16"))
    memory_ttl_seconds: int = int(os.getenv("MEMORY_TTL_SECONDS", "0"))
    evolution_base_url: str = os.getenv("EVOLUTION_API_BASE_URL", "")
    evolution_token: str = os.getenv("EVOLUTION_API_TOKEN", "")
    evolution_instance: str = os.getenv("EVOLUTION_INSTANCE", "")
    langfuse_public_key: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    langfuse_secret_key: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    langfuse_host: str = os.getenv("LANGFUSE_HOST", "")

settings = Settings()

def warn_missing():
    missing = []
    for field in Settings.__dataclass_fields__.keys():
        if getattr(settings, field) in (None, ""):
            missing.append(field)
    if missing:
        print(f"Warn: missing envs: {', '.join(missing)}")