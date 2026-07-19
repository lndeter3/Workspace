# app.py — STANDALONE per Streamlit Cloud
import uuid, time
import streamlit as st

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core.client  import GeminiClient
from core.session import SessionManager, SessionState

st.set_page_config(page_title="Gemini Chat", page_icon="✨", layout="wide")

# ------------------------------------------------------------------ #
#  Client singleton                                                    #
# ------------------------------------------------------------------ #
@st.cache_resource
def get_client() -> GeminiClient:
    return GeminiClient()

# ------------------------------------------------------------------ #
#  Session state                                                       #
# ------------------------------------------------------------------ #
def _init():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages"   not in st.session_state:
        st.session_state.messages   = []
    if "gem_state"  not in st.session_state:
        st.session_state.gem_state  = SessionState()
    if "use_engineer" not in st.session_state:
        st.session_state.use_engineer = True
    if "force_complete" not in st.session_state:
        st.session_state.force_complete = True

_init()

# ------------------------------------------------------------------ #
#  Bootstrap                                                           #
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
    st.markdown("## ✨ Gemini Chat")
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

    st.markdown("---")
    if state.bl:
        st.success("Gemini connesso ✓")
    else:
        st.error("Non connesso")

# ------------------------------------------------------------------ #
#  Chat                                                                #
# ------------------------------------------------------------------ #
st.markdown("## ✨ Gemini")

USER_AVATAR = "🧑"
BOT_AVATAR  = "🤖"

for msg in st.session_state.messages:
    avatar = USER_AVATAR if msg["role"] == "user" else BOT_AVATAR
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg.get("elapsed_ms"):
            extra = ""
            if msg.get("enhancements"):
                extra = f"  🔧 {', '.join(msg['enhancements'])}"
            st.caption(f"⏱ {msg['elapsed_ms']}ms{extra}")

if prompt := st.chat_input("Scrivi a Gemini…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=BOT_AVATAR):
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
            extra = f"  🔧 {', '.join(tags)}" if tags else ""
            st.caption(f"⏱ {elapsed}ms{extra}")

            st.session_state.messages.append({
                "role":         "assistant",
                "content":      answer,
                "elapsed_ms":   elapsed,
                "enhancements": tags,
            })
        except RuntimeError as e:
            placeholder.error(str(e))
        except Exception as e:
            placeholder.error(f"Errore: {e}")
            st.session_state.gem_state = SessionState()
