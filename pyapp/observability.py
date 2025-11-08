from langfuse import get_client
from .config import settings

# Initialize via environment variables using the SDK's client factory
langfuse = get_client()

def create_message_trace(user_id: str, message: str, message_id: str):
    # Start a root span which creates the trace in Python SDK v3
    root = langfuse.start_as_current_span(name="whatsapp_agent")
    # Attach trace-level attributes via the client (preferred) or fall back to root update
    try:
        langfuse.update_current_trace(
            user_id=user_id,
            input=message,
            metadata={"messageId": message_id},
        )
    except Exception:
        try:
            root.update(
                input=message,
                metadata={"messageId": message_id},
            )
        except Exception:
            pass
    return root