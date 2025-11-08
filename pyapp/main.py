from fastapi import FastAPI, Request
from .config import settings, warn_missing
from .observability import langfuse
from .chain import run_chain
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

@app.get("/debug/chain")
async def debug_chain(text: str):
    # Trace dedicado para testar a cadeia sem integração externa
    with langfuse.start_as_current_span(name="whatsapp_agent_chain") as root:
        try:
            langfuse.update_current_trace(
                user_id="debug-user",
                input=text,
                metadata={"messageId": "debug-chain"},
            )
        except Exception:
            try:
                root.update(input=text, metadata={"messageId": "debug-chain"})
            except Exception:
                pass

        result = {"reply": "", "usage": None, "context_size": 0, "events": []}
        with langfuse.start_as_current_span(name="llm_call") as span:
            try:
                rc = run_chain(text=text, user_id="debug-user")
                result = {
                    "reply": rc.get("reply", ""),
                    "usage": rc.get("usage"),
                    "context_size": rc.get("context_size", 0),
                    "events": rc.get("events", []),
                }
                span.update(output={"reply": result["reply"], "usage": result["usage"], "context_size": result["context_size"]})
            except Exception as e:
                span.update(output={"error": str(e)})
                result = {"reply": "Erro ao executar cadeia.", "usage": None, "context_size": 0, "events": []}

        # Log memory events
        for ev in result.get("events", []):
            with langfuse.start_as_current_span(name=ev.get("type", "memory_event")) as ev_span:
                ev_span.update(output=ev)

        root.update(output=result)
        return {
            "ok": True,
            "reply": result["reply"],
            "usage": result["usage"],
            "context_size": result["context_size"],
            "trace_id": getattr(root, "trace_id", None),
        }

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

    # Executa a cadeia para obter a resposta do agente
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
                try:
                    rc = run_chain(text=message, user_id=user_id)
                    reply = rc.get("reply", reply)
                    span.update(output={"reply": reply, "usage": rc.get("usage"), "context_size": rc.get("context_size")})
                except Exception as e:
                    span.update(output={"error": str(e)})

            # Log memory events
            for ev in (rc.get("events", []) if 'rc' in locals() else []):
                with langfuse.start_as_current_span(name=ev.get("type", "memory_event")) as ev_span:
                    ev_span.update(output=ev)

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