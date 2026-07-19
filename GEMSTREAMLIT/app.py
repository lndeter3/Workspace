"""
Streamlit frontend — chiama api.py via httpx
Avvio: streamlit run app.py
"""
import uuid, time
import streamlit as st
import httpx

# ------------------------------------------------------------------ #
#  Config                                                              #
# ------------------------------------------------------------------ #
API_BASE = "http://localhost:8000"   # cambia con URL deploy se remoto
TIMEOUT  = 60.0

st.set_page_config(
    page_title = "Gemini Chat",
    page_icon  = "✦",
    layout     = "wide",
)

# ------------------------------------------------------------------ #
#  Session state                                                       #
# ------------------------------------------------------------------ #
def _init():
    if "session_id"   not in st.session_state:
        st.session_state.session_id   = str(uuid.uuid4())
    if "messages"     not in st.session_state:
        st.session_state.messages     = []
    if "use_engineer" not in st.session_state:
        st.session_state.use_engineer = True
    if "force_complete" not in st.session_state:
        st.session_state.force_complete = True

_init()

# ------------------------------------------------------------------ #
#  Sidebar                                                             #
# ------------------------------------------------------------------ #
with st.sidebar:
    st.markdown("## ✦ Gemini Chat v13")
    st.markdown("---")

    st.session_state.use_engineer = st.toggle(
        "Prompt Engineer", value=st.session_state.use_engineer,
        help="Riscrive il prompt per ottenere risposte migliori"
    )
    st.session_state.force_complete = st.toggle(
        "Auto-completa liste", value=st.session_state.force_complete,
        help="Forza completamento di liste numeriche"
    )

    st.markdown("---")
    st.caption(f"Session: `{st.session_state.session_id[:8]}...`")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑 Nuova chat", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages   = []
            st.rerun()
    with col2:
        if st.button("🔄 Reset API", use_container_width=True):
            try:
                httpx.delete(
                    f"{API_BASE}/session/{st.session_state.session_id}",
                    timeout=5
                )
            except Exception:
                pass
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages   = []
            st.rerun()

    st.markdown("---")
    # Health check
    try:
        r = httpx.get(f"{API_BASE}/health", timeout=3)
        if r.status_code == 200:
            st.success("API online ✓", icon="✅")
        else:
            st.error(f"API errore {r.status_code}")
    except Exception as e:
        st.error(f"API offline: {e}")

# ------------------------------------------------------------------ #
#  Chat history                                                        #
# ------------------------------------------------------------------ #
st.markdown("## ✦ Gemini")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"],
                         avatar="🧑" if msg["role"] == "user" else "✦"):
        st.markdown(msg["content"])
        if msg.get("meta"):
            m = msg["meta"]
            cols = st.columns(3)
            cols[0].caption(f"⏱ {m.get('elapsed_ms',0)}ms")
            if m.get("enhancements"):
                cols[1].caption(f"🔧 {', '.join(m['enhancements'])}")
            cols[2].caption(f"🔑 {m.get('session_id','')[:8]}")

# ------------------------------------------------------------------ #
#  Input                                                               #
# ------------------------------------------------------------------ #
if prompt := st.chat_input("Scrivi a Gemini…"):
    # Mostra messaggio utente
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    # Chiamata API
    with st.chat_message("assistant", avatar="✦"):
        placeholder = st.empty()
        placeholder.markdown("_Gemini sta elaborando…_ ⏳")

        t0 = time.perf_counter()
        try:
            resp = httpx.post(
                f"{API_BASE}/ask",
                json={
                    "message":        prompt,
                    "session_id":     st.session_state.session_id,
                    "use_engineer":   st.session_state.use_engineer,
                    "force_complete": st.session_state.force_complete,
                },
                timeout=TIMEOUT,
            )
            if resp.status_code == 200:
                data   = resp.json()
                answer = data["answer"]
                meta   = {
                    "elapsed_ms":   data["elapsed_ms"],
                    "enhancements": data["enhancements"],
                    "session_id":   data["session_id"],
                }
                placeholder.markdown(answer)

                # Mostra meta sotto
                mcols = st.columns(3)
                mcols[0].caption(f"⏱ {data['elapsed_ms']}ms")
                if data["enhancements"]:
                    mcols[1].caption(f"🔧 {', '.join(data['enhancements'])}")
                mcols[2].caption(f"🔑 {data['session_id'][:8]}")

                st.session_state.messages.append({
                    "role":    "assistant",
                    "content": answer,
                    "meta":    meta,
                })
            else:
                detail = resp.json().get("detail", resp.text)
                placeholder.error(f"Errore {resp.status_code}: {detail}")

        except httpx.TimeoutException:
            placeholder.error("⏱ Timeout — la richiesta ha impiegato troppo")
        except httpx.ConnectError:
            placeholder.error("🔌 Impossibile connettersi all'API. È avviata?")
        except Exception as e:
            placeholder.error(f"Errore inatteso: {e}")