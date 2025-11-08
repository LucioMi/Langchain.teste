from typing import Optional, Dict, Any, List
from collections import deque, defaultdict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from .config import settings


# Memória conversacional simples em memória, por usuário.
_MEMORY: Dict[str, deque] = defaultdict(lambda: deque(maxlen=8))


def _get_llm() -> ChatOpenAI:
    # Usa a chave de API do ambiente; evita hardcode de modelo.
    return ChatOpenAI(temperature=0)


def _build_messages(user_id: Optional[str], text: str) -> List[BaseMessage]:
    system = SystemMessage(
        content=(
            "Você é um assistente curto e objetivo. Responda em português e em uma única frase."
        )
    )
    history: List[BaseMessage] = list(_MEMORY[user_id]) if user_id else []
    return [system, *history, HumanMessage(content=text)]


def run_chain(text: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Executa uma interação simples de chat com memória leve.

    Retorna: { reply, usage, context_size }
    """
    # Fallback amigável quando não há chave de API.
    if not settings.openai_api_key:
        reply = "IA indisponível no momento. Configure OPENAI_API_KEY."
        return {"reply": reply, "usage": None, "context_size": len(_MEMORY[user_id]) if user_id else 0}

    llm = _get_llm()
    messages = _build_messages(user_id, text)
    resp: AIMessage = llm.invoke(messages)
    reply = resp.content if isinstance(resp, AIMessage) else str(resp)

    # Atualiza memória do usuário.
    if user_id:
        mem = _MEMORY[user_id]
        mem.append(HumanMessage(content=text))
        mem.append(AIMessage(content=reply))

    usage = None
    try:
        # Alguns provedores expõem contagem de tokens no response_metadata
        usage = resp.response_metadata.get("token_usage")  # type: ignore[attr-defined]
    except Exception:
        usage = None

    return {"reply": reply, "usage": usage, "context_size": len(_MEMORY[user_id]) if user_id else 0}