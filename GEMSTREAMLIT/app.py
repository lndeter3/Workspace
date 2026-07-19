import uuid,time,streamlit as st,sys,os,traceback
sys.path.insert(0,os.path.dirname(__file__))
from core.client import GeminiClient
from core.session import SessionState
st.set_page_config(page_title="Gemini",page_icon="✨",layout="wide",initial_sidebar_state="expanded")
CSS="""
<style>
#MainMenu,footer,header{visibility:hidden;}
.stDeployButton{display:none;}
.block-container{padding-top:1rem;padding-bottom:8rem;max-width:820px;}
section[data-testid="stSidebar"]{background:#171717;border-right:1px solid #2a2a2a;}
section[data-testid="stSidebar"] .stButton>button{background:transparent;border:1px solid #333;color:#ececec;border-radius:10px;font-weight:500;}
section[data-testid="stSidebar"] .stButton>button:hover{background:#2a2a2a;border-color:#444;}
.stApp{background:#212121;color:#ececec;}
[data-testid="stChatMessage"]{background:transparent!important;border:none!important;padding:1.2rem 0!important;margin:0!important;}
.stChatInput{background:#2f2f2f!important;border:1px solid #444!important;border-radius:26px!important;padding:4px!important;}
.stChatInput:focus-within{border-color:#8B5CF6!important;}
[data-testid="stChatInputTextArea"]{background:transparent!important;color:#ececec!important;font-size:16px!important;}
.stChatFloatingInputContainer{background:linear-gradient(180deg,transparent 0%,#212121 40%)!important;padding-bottom:1.5rem;padding-top:2rem;}
h1,h2,h3{color:#ececec!important;font-weight:600;}
.stMarkdown p{color:#ececec;line-height:1.7;font-size:15.5px;}
.stMarkdown code{background:#2a2a2a;padding:2px 6px;border-radius:4px;color:#f8f8f2;font-size:14px;}
.stMarkdown pre{background:#0d0d0d!important;border:1px solid #2a2a2a;border-radius:10px;padding:14px;}
.stMarkdown a{color:#8B5CF6;text-decoration:none;}
.stCaption{color:#8e8e8e!important;font-size:12px!important;}
.hero{text-align:center;padding:4rem 1rem 2rem;}
.hero-title{font-size:2.2rem;font-weight:600;background:linear-gradient(135deg,#8B5CF6,#EC4899,#F59E0B);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:.5rem;}
.hero-sub{color:#8e8e8e;font-size:1rem;}
.file-chip{display:inline-flex;align-items:center;gap:6px;background:#2a2a2a;border:1px solid #3a3a3a;border-radius:8px;padding:6px 10px;margin:3px;font-size:13px;color:#ececec;}
.status-dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px;}
.status-on{background:#10a37f;box-shadow:0 0 6px #10a37f;}
.status-off{background:#ef4444;}
::-webkit-scrollbar{width:8px;}
::-webkit-scrollbar-thumb{background:#3a3a3a;border-radius:4px;}
</style>
"""
st.markdown(CSS,unsafe_allow_html=True)
@st.cache_resource
def gc():return GeminiClient()
def _i():
 for k,v in [("sid",str(uuid.uuid4())),("msg",[]),("gs",SessionState()),("eng",True),("fc",True),("pending",[]),("upk",0),("debug",False)]:
  if k not in st.session_state:st.session_state[k]=v
_i()
cl=gc()
gs=st.session_state.gs
if not gs.bl:
 with st.spinner("Connessione a Gemini..."):
  try:cl.bootstrap(gs)
  except Exception as e:st.error(f"Bootstrap fallito: {e}");st.stop()
with st.sidebar:
 st.markdown("<div style='padding:8px 4px 20px;'><div style='font-size:20px;font-weight:600;background:linear-gradient(135deg,#8B5CF6,#EC4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>✨ Gemini</div><div style='color:#8e8e8e;font-size:12px;'>Powered by Google</div></div>",unsafe_allow_html=True)
 if st.button("＋ Nuova chat",use_container_width=True,type="primary"):
  st.session_state.sid=str(uuid.uuid4())
  st.session_state.msg=[]
  st.session_state.gs=SessionState()
  st.session_state.pending=[]
  st.session_state.upk+=1
  st.rerun()
 st.markdown("<div style='margin:20px 0 10px;color:#8e8e8e;font-size:11px;text-transform:uppercase;letter-spacing:1px;font-weight:600;'>Impostazioni</div>",unsafe_allow_html=True)
 st.session_state.eng=st.toggle("🔧 Prompt Engineer",value=st.session_state.eng)
 st.session_state.fc=st.toggle("📝 Auto-completa liste",value=st.session_state.fc)
 st.session_state.debug=st.toggle("🐛 Debug",value=st.session_state.debug)
 st.markdown("<div style='margin:20px 0 10px;color:#8e8e8e;font-size:11px;text-transform:uppercase;letter-spacing:1px;font-weight:600;'>📎 Allegati</div>",unsafe_allow_html=True)
 up=st.file_uploader("Carica",type=["png","jpg","jpeg","webp","gif","pdf","txt","md","csv","json","py","js","html","css","xml","yaml","yml"],accept_multiple_files=True,key=f"up_{st.session_state.upk}",label_visibility="collapsed")
 if up:
  existing={(x["name"],x["size"]) for x in st.session_state.pending}
  for f in up:
   if (f.name,f.size) not in existing:
    st.session_state.pending.append({"name":f.name,"size":f.size,"bytes":f.getvalue(),"mime":f.type or "application/octet-stream","uploaded":False,"id":None})
 if st.session_state.pending:
  st.markdown(f"<div style='color:#8e8e8e;font-size:12px;margin:8px 0 4px;'>{len(st.session_state.pending)} file pronti</div>",unsafe_allow_html=True)
  for i,f in enumerate(st.session_state.pending):
   c1,c2=st.columns([5,1])
   ic="🖼" if f["mime"].startswith("image/") else "📄"
   status="✓" if f["uploaded"] else "○"
   c1.markdown(f"<div class='file-chip'>{ic} {f['name'][:22]}{'...' if len(f['name'])>22 else ''} <span style='color:#666;font-size:11px;'>{f['size']/1024:.0f}KB {status}</span></div>",unsafe_allow_html=True)
   if c2.button("✕",key=f"rm_{i}"):
    st.session_state.pending.pop(i)
    st.rerun()
 st.markdown("<div style='position:absolute;bottom:20px;left:20px;right:20px;'>",unsafe_allow_html=True)
 dot="status-on" if gs.bl else "status-off"
 st.markdown(f"<div style='color:#8e8e8e;font-size:12px;'><span class='status-dot {dot}'></span>{'Connesso' if gs.bl else 'Off'}</div><div style='color:#555;font-size:10px;margin-top:4px;font-family:monospace;'>{st.session_state.sid[:16]}</div></div>",unsafe_allow_html=True)
if not st.session_state.msg:
 st.markdown("<div class='hero'><div class='hero-title'>✨ Come posso aiutarti oggi?</div><div class='hero-sub'>Chiedi qualsiasi cosa, carica file, esplora idee</div></div>",unsafe_allow_html=True)
for m in st.session_state.msg:
 with st.chat_message(m["role"],avatar="👤" if m["role"]=="user" else "✨"):
  if m.get("files"):
   chips="".join(f"<span class='file-chip'>{'🖼' if fi.get('mime','').startswith('image/') else '📄'} {fi['name']}</span>" for fi in m["files"])
   st.markdown(f"<div style='margin-bottom:8px;'>{chips}</div>",unsafe_allow_html=True)
  st.markdown(m["content"])
  if m.get("ms"):
   tg=" · ".join(m.get("tags") or [])
   st.caption(f"⏱ {m['ms']}ms"+(f" · 🔧 {tg}" if tg else ""))
if p:=st.chat_input("Scrivi a Gemini..."):
 attached=list(st.session_state.pending)
 amt=[{"name":f["name"],"mime":f["mime"],"size":f["size"]} for f in attached]
 st.session_state.msg.append({"role":"user","content":p,"files":amt})
 with st.chat_message("user",avatar="👤"):
  if amt:
   chips="".join(f"<span class='file-chip'>{'🖼' if fi['mime'].startswith('image/') else '📄'} {fi['name']}</span>" for fi in amt)
   st.markdown(f"<div style='margin-bottom:8px;'>{chips}</div>",unsafe_allow_html=True)
  st.markdown(p)
 with st.chat_message("assistant",avatar="✨"):
  ph=st.empty()
  info=st.empty()
  t0=time.perf_counter()
  uploaded=[]
  try:
   if attached:
    for idx,f in enumerate(attached):
     info.markdown(f"<div style='color:#8e8e8e;font-size:13px;'>⬆ Upload {f['name']} ({idx+1}/{len(attached)})...</div>",unsafe_allow_html=True)
     try:
      result=cl.upload_bytes(f["bytes"],f["name"],f["mime"])
      uploaded.append(result)
      if st.session_state.debug:st.caption(f"✓ {f['name']} → ID: {result['id'][:20]}...")
     except Exception as ue:
      err_msg=f"❌ Upload {f['name']}: {ue}"
      if st.session_state.debug:err_msg+=f"\n```\n{traceback.format_exc()}\n```"
      info.error(err_msg)
      raise
    info.markdown(f"<div style='color:#10a37f;font-size:13px;'>✓ {len(uploaded)} file caricati</div>",unsafe_allow_html=True)
   ph.markdown("<div style='color:#8e8e8e;'>_Sto pensando..._ ⏳</div>",unsafe_allow_html=True)
   ans,tags=cl.chat(message=p,state=gs,use_engineer=st.session_state.eng,force_complete=st.session_state.fc,files=uploaded if uploaded else None)
   ms=int((time.perf_counter()-t0)*1000)
   info.empty()
   ph.markdown(ans)
   tg=" · ".join(tags) if tags else ""
   st.caption(f"⏱ {ms}ms"+(f" · 🔧 {tg}" if tg else ""))
   st.session_state.msg.append({"role":"assistant","content":ans,"ms":ms,"tags":tags})
   st.session_state.pending=[]
   st.session_state.upk+=1
  except RuntimeError as e:
   info.empty()
   ph.error(f"⚠ {e}")
   if st.session_state.debug:st.code(traceback.format_exc())
  except Exception as e:
   info.empty()
   ph.error(f"⚠ {type(e).__name__}: {e}")
   if st.session_state.debug:st.code(traceback.format_exc())
   st.session_state.gs=SessionState()
