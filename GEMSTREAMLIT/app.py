import uuid,time,streamlit as st,sys,os
sys.path.insert(0,os.path.dirname(__file__))
from core.client import GeminiClient
from core.session import SessionState
st.set_page_config(page_title="Gemini Chat",page_icon="✨",layout="wide")
@st.cache_resource
def gc():return GeminiClient()
def _i():
 for k,v in[("sid",str(uuid.uuid4())),("msg",[]),("gs",SessionState()),("eng",True),("fc",True)]:
  if k not in st.session_state:st.session_state[k]=v
_i();cl=gc();gs=st.session_state.gs
if not gs.bl:
 with st.spinner("Connessione..."):
  try:cl.bootstrap(gs)
  except Exception as e:st.error(f"Bootstrap fallito: {e}");st.stop()
with st.sidebar:
 st.markdown("## ✨ Gemini Chat");st.markdown("---")
 st.session_state.eng=st.toggle("Prompt Engineer",value=st.session_state.eng)
 st.session_state.fc=st.toggle("Auto-completa liste",value=st.session_state.fc)
 st.markdown("---");st.caption(f"Session: `{st.session_state.sid[:8]}...`")
 if st.button("🗑 Nuova chat",use_container_width=True):st.session_state.sid=str(uuid.uuid4());st.session_state.msg=[];st.session_state.gs=SessionState();st.rerun()
 st.markdown("---");st.success("Connesso ✓") if gs.bl else st.error("Non connesso")
st.markdown("## ✨ Gemini")
for m in st.session_state.msg:
 with st.chat_message(m["role"],avatar="🧑" if m["role"]=="user" else "🤖"):
  st.markdown(m["content"])
  if m.get("ms"):st.caption(f"⏱ {m['ms']}ms"+( f"  🔧 {', '.join(m['tags'])}" if m.get("tags") else ""))
if p:=st.chat_input("Scrivi a Gemini…"):
 st.session_state.msg.append({"role":"user","content":p})
 with st.chat_message("user",avatar="🧑"):st.markdown(p)
 with st.chat_message("assistant",avatar="🤖"):
  ph=st.empty();ph.markdown("_Elaboro…_ ⏳");t0=time.perf_counter()
  try:
   ans,tags=cl.chat(message=p,state=gs,use_engineer=st.session_state.eng,force_complete=st.session_state.fc)
   ms=int((time.perf_counter()-t0)*1000);ph.markdown(ans);st.caption(f"⏱ {ms}ms"+(f"  🔧 {', '.join(tags)}" if tags else ""))
   st.session_state.msg.append({"role":"assistant","content":ans,"ms":ms,"tags":tags})
  except RuntimeError as e:ph.error(str(e))
  except Exception as e:ph.error(f"Errore: {e}");st.session_state.gs=SessionState()
