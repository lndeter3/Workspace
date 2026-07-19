# app.py — STANDALONE per Streamlit Cloud
import uuid, time
import streamlit as st

# Importa core direttamente (no httpx, no API)
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core.client  import GeminiClient
from core.session import SessionManager, SessionState

API_BASE = None  # non serve

st.set_page_config(page_title="Gemini Chat", page_icon="✦", layout="wide")

# ------------------------------------------------------------------ #
#  Client singleton (una sola istanza per tutto Streamlit)            #
# ------------------------------------------------------------------ #
@st.cache_resource
def get_client() -> GeminiClient:
    client = GeminiClient()
    return client

# ------------------------------------------------------------------ #
#  Session state                                                       #
# ------------------------------------------------------------------ #
def _init():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages"   not in st.session_state:
        st.session_state.messages   = []
    if "gem_state"  not in st.session_state:
        # Stato Gemini per-utente
        st.session_state.gem_state  = SessionState()
    if "use_engineer" not in st.session_state:
        st.session_state.use_engineer = True
    if "force_complete" not in st.session_state:
        st.session_state.force_complete = True

_init()

# ------------------------------------------------------------------ #
#  Bootstrap automatico                                                #
# ------------------------------------------------------------------ #
client = get_client()
state: SessionState = st.session_state.gem_state

if not state.bl:
    with st.spinner("Connessione a Gemini..."):
        try:
            client.bootstrap(state)
        except Exception as e:
            st.error(f"Bootstrap fallito: {e}")
            st.stop()

# ------------------------------------------------------------------ #
#  Sidebar                                                             #
# ------------------------------------------------------------------ #
with st.sidebar:
    st.markdown("## ✦ Gemini Chat")
    st.markdown("---")

    st.session_state.use_engineer = st.toggle(
        "Prompt Engineer", value=st.session_state.use_engineer
    )
    st.session_state.force_complete = st.toggle(
        "Auto-completa liste", value=st.session_state.force_complete
    )

    st.markdown("---")
    st.caption(f"Session: `{st.session_state.session_id[:8]}...`")

    if st.button("🗑 Nuova chat", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages   = []
        st.session_state.gem_state  = SessionState()
        st.rerun()

    # Status
    st.markdown("---")
    if state.bl:
        st.success("Gemini connesso ✓")
    else:
        st.error("Non connesso")

# ------------------------------------------------------------------ #
#  Chat history                                                        #
# ------------------------------------------------------------------ #
st.markdown("## ✦ Gemini")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"],
                         avatar="🧑" if msg["role"] == "user" else "✦"):
        st.markdown(msg["content"])
        if msg.get("elapsed_ms"):
            st.caption(f"⏱ {msg['elapsed_ms']}ms"
                       + (f"  🔧 {', '.join(msg['enhancements'])}"
                          if msg.get("enhancements") else ""))

# ------------------------------------------------------------------ #
#  Input                                                               #
# ------------------------------------------------------------------ #
if prompt := st.chat_input("Scrivi a Gemini…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="✦"):
        placeholder = st.empty()
        placeholder.markdown("_Elaboro…_ ⏳")

        t0 = time.perf_counter()
        try:
            answer, tags = client.chat(
                message        = prompt,
                state          = state,
                use_engineer   = st.session_state.use_engineer,
                force_complete = st.session_state.force_complete,
            )
            elapsed = int((time.perf_counter() - t0) * 1000)
            placeholder.markdown(answer)
            st.caption(f"⏱ {elapsed}ms"
                       + (f"  🔧 {', '.join(tags)}" if tags else ""))

            st.session_state.messages.append({
                "role":        "assistant",
                "content":     answer,
                "elapsed_ms":  elapsed,
                "enhancements": tags,
            })

        except RuntimeError as e:
            placeholder.error(str(e))
        except Exception as e:
            placeholder.error(f"Errore: {e}")
            # Se sessione corrotta, reset automatico
            st.session_state.gem_state = SessionState()
