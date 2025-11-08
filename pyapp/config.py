from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass
class Settings:
    port: int = int(os.getenv("PORT", "5678"))
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
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