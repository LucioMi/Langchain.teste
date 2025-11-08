from typing import Optional, Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from .config import settings
from .memory import (
    get_history,
    append_message,
    count_context,
    add_preference,
    clear_preferences,
    get_preferences,
)


# Memória conversacional simples em memória, por usuário.
_MEMORY: Dict[str, list] = {}  # legado não usado com SQLite; mantido por compatibilidade


def _get_llm() -> ChatOpenAI:
    # Usa a chave de API do ambiente; evita hardcode de modelo.
    if settings.openai_model:
        return ChatOpenAI(model=settings.openai_model, temperature=0)
    return ChatOpenAI(temperature=0)


def _build_messages(user_id: Optional[str], text: str) -> List[BaseMessage]:
    system = SystemMessage(content=settings.system_prompt)
    msgs: List[BaseMessage] = [system]
    if user_id:
        # Load preferences and add as extra system context
        prefs = get_preferences(settings.sqlite_db_path, user_id)
        if prefs:
            prefs_system = SystemMessage(
                content=f"Preferências lembradas: {', '.join(prefs[:5])}."
            )
            msgs.append(prefs_system)
        # Load history from persistent storage
        hist = get_history(
            settings.sqlite_db_path,
            user_id,
            limit=settings.memory_max_messages,
            ttl_seconds=(settings.memory_ttl_seconds or None),
        )
        for role, content in hist:
            if role == "human":
                msgs.append(HumanMessage(content=content))
            elif role == "ai":
                msgs.append(AIMessage(content=content))
    msgs.append(HumanMessage(content=text))
    return msgs


def run_chain(text: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Executa uma interação simples de chat com memória leve.

    Retorna: { reply, usage, context_size }
    """
    # Fallback amigável quando não há chave de API.
    if not settings.openai_api_key:
        reply = "IA indisponível no momento. Configure OPENAI_API_KEY."
        ctx = count_context(settings.sqlite_db_path, user_id or "") if user_id else 0
        return {"reply": reply, "usage": None, "context_size": ctx}

    events: List[Dict[str, Any]] = []
    # Detect memory commands (simple heuristics)
    if user_id:
        low = text.lower()
        if "lembrar" in low:
            # Try to extract after ':' or whole text minus keyword
            item = text
            if ":" in text:
                item = text.split(":", 1)[1].strip()
            else:
                item = low.replace("lembrar", "").strip() or text.strip()
            if item:
                add_preference(settings.sqlite_db_path, user_id, item)
                events.append({"type": "memory_remember", "item": item})
        if "esquecer" in low:
            clear_preferences(settings.sqlite_db_path, user_id)
            events.append({"type": "memory_forget"})

    llm = _get_llm()
    messages = _build_messages(user_id, text)
    resp: AIMessage = llm.invoke(messages)
    reply = resp.content if isinstance(resp, AIMessage) else str(resp)

    # Atualiza memória do usuário.
    if user_id:
        append_message(settings.sqlite_db_path, user_id, "human", text)
        append_message(settings.sqlite_db_path, user_id, "ai", reply)

    usage = None
    try:
        # Alguns provedores expõem contagem de tokens no response_metadata
        usage = resp.response_metadata.get("token_usage")  # type: ignore[attr-defined]
    except Exception:
        usage = None

    ctx = count_context(settings.sqlite_db_path, user_id or "") if user_id else 0
    return {"reply": reply, "usage": usage, "context_size": ctx, "events": events}