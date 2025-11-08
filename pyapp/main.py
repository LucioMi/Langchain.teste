from fastapi import FastAPI, Request
from .config import settings, warn_missing
from .observability import langfuse
from .evolution import send_text

app = FastAPI()

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/debug/langfuse")
async def debug_langfuse():
    with langfuse.start_as_current_span(name="whatsapp_agent") as root:
        try:
            langfuse.update_current_trace(
                user_id="debug-user",
                input="ping",
                metadata={"messageId": "debug-msg"},
            )
        except Exception:
            try:
                root.update(input="ping", metadata={"messageId": "debug-msg"})
            except Exception:
                pass
        with langfuse.start_as_current_span(name="ping") as span:
            span.update(output="pong")
            # Root span will end automatically when exiting context
        return {"ok": True, "trace_id": getattr(root, "trace_id", None)}

@app.post("/webhook/teste.agente.codigo")
async def webhook(req: Request):
    body = await req.json()
    message = (
        body.get("data", {}).get("message", {}).get("conversation")
        or body.get("message")
        or ""
    )
    user_id = body.get("sender") or body.get("data", {}).get("key", {}).get("remoteJid") or "unknown"
    message_id = body.get("data", {}).get("key", {}).get("id") or "unknown"

    warn_missing()

    reply = f"Recebido: {message}"
    number = user_id.split('@')[0] if user_id else ""
    sent = False
    send_error = None
    trace = None
    try:
        with langfuse.start_as_current_span(name="whatsapp_agent") as trace:
            try:
                langfuse.update_current_trace(
                    user_id=user_id,
                    input=message,
                    metadata={"messageId": message_id},
                )
            except Exception:
                try:
                    trace.update(input=message, metadata={"messageId": message_id})
                except Exception:
                    pass

            with langfuse.start_as_current_span(name="llm_call") as span:
                span.update(output=reply)

            with langfuse.start_as_current_span(name="evolution_send") as send_span:
                try:
                    send_result = await send_text(number=number, text=reply)
                    send_span.update(output=send_result)
                    sent = True
                except Exception as e:
                    send_span.update(output={"error": str(e)})
                    sent = False
                    send_error = str(e)

            # Root span ends when context exits; set final output now
            trace.update(output={"reply": reply, "sent": sent})

            return {
                "status": "ok",
                "reply": reply,
                "sent": sent,
                "error": send_error,
                "trace_id": getattr(trace, "trace_id", None),
            }
    except Exception:
        try:
            await send_text(number=number, text=reply)
            sent = True
        except Exception as e:
            sent = False
            send_error = str(e)

        return {
            "status": "ok",
            "reply": reply,
            "sent": sent,
            "error": send_error,
            "trace_id": None,
        }