"""
FastAPI backend — endpoint GET + POST
Chiamabile da Streamlit, curl, browser
"""
import uuid, time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from core.client  import GeminiClient
from core.session import SessionManager, SessionState

# ------------------------------------------------------------------ #
#  App lifecycle                                                       #
# ------------------------------------------------------------------ #
_client: GeminiClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _client
    _client = GeminiClient()
    # Bootstrap con sessione temporanea per pre-scaldare la connessione
    _tmp = SessionState()
    try:
        _client.bootstrap(_tmp)
    except Exception as e:
        print(f"[WARN] bootstrap startup fallito: {e}")
    yield
    _client = None

app = FastAPI(
    title="Gemini API",
    version="13.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #
def _get_or_create_state(session_id: str) -> SessionState:
    state = SessionManager.get(session_id)
    # bootstrap se manca bl
    if not state.bl:
        _client.bootstrap(state)
    return state

# ------------------------------------------------------------------ #
#  Schemas                                                             #
# ------------------------------------------------------------------ #
class AskBody(BaseModel):
    message:        str
    session_id:     Optional[str] = None
    use_engineer:   bool = True
    force_complete: bool = True

class AskResponse(BaseModel):
    answer:       str
    session_id:   str
    enhancements: list[str]
    elapsed_ms:   int

# ------------------------------------------------------------------ #
#  Routes                                                              #
# ------------------------------------------------------------------ #
@app.get("/health")
async def health():
    return {"status": "ok", "version": "13.0"}


@app.get("/ask")
async def ask_get(
    q:              str  = Query(..., description="Messaggio"),
    session_id:     str  = Query(default="", description="ID sessione (vuoto = nuova)"),
    engineer:       bool = Query(default=True),
    complete:       bool = Query(default=True),
):
    """
    GET /ask?q=Ciao&session_id=abc
    Ultra-veloce per chiamate semplici da browser/curl.
    """
    if not _client:
        raise HTTPException(503, "Client non inizializzato")

    sid   = session_id or str(uuid.uuid4())
    state = _get_or_create_state(sid)
    t0    = time.perf_counter()

    try:
        answer, tags = _client.chat(
            message        = q,
            state          = state,
            use_engineer   = engineer,
            force_complete = complete,
        )
    except RuntimeError as e:
        raise HTTPException(429 if "Rate limit" in str(e) else 500, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))

    return AskResponse(
        answer       = answer,
        session_id   = sid,
        enhancements = tags,
        elapsed_ms   = int((time.perf_counter() - t0) * 1000),
    )


@app.post("/ask")
async def ask_post(body: AskBody):
    """POST /ask  con JSON body — per messaggi lunghi / paste."""
    if not _client:
        raise HTTPException(503, "Client non inizializzato")

    sid   = body.session_id or str(uuid.uuid4())
    state = _get_or_create_state(sid)
    t0    = time.perf_counter()

    try:
        answer, tags = _client.chat(
            message        = body.message,
            state          = state,
            use_engineer   = body.use_engineer,
            force_complete = body.force_complete,
        )
    except RuntimeError as e:
        raise HTTPException(429 if "Rate limit" in str(e) else 500, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))

    return AskResponse(
        answer       = answer,
        session_id   = sid,
        enhancements = tags,
        elapsed_ms   = int((time.perf_counter() - t0) * 1000),
    )


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Cancella una sessione."""
    with SessionManager._lock:
        dropped = SessionManager._store.pop(session_id, None)
    return {"deleted": dropped is not None, "session_id": session_id}


@app.get("/sessions")
async def list_sessions():
    with SessionManager._lock:
        ids = list(SessionManager._store.keys())
    return {"count": len(ids), "sessions": ids}