import uuid,time,streamlit as st,sys,os,tempfile
sys.path.insert(0,os.path.dirname(__file__))
from core.client import GeminiClient
from core.session import SessionState
st.set_page_config(page_title="Gemini Chat",page_icon="✨",layout="wide")
@st.cache_resource
def gc():return GeminiClient()
def _i():
 for k,v in[("sid",str(uuid.uuid4())),("msg",[]),("gs",SessionState()),("eng",True),("fc",True),("files",[]),("upk",0)]:
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
 if st.button("🗑 Nuova chat",use_container_width=True):st.session_state.sid=str(uuid.uuid4());st.session_state.msg=[];st.session_state.gs=SessionState();st.session_state.files=[];st.session_state.upk+=1;st.rerun()
 st.markdown("---");st.success("Connesso ✓") if gs.bl else st.error("Non connesso")
 st.markdown("---");st.markdown("### 📎 Allegati")
 up=st.file_uploader("Carica file",type=["png","jpg","jpeg","webp","gif","pdf","txt","md","csv","json","py","js","html","css"],accept_multiple_files=True,key=f"up_{st.session_state.upk}",label_visibility="collapsed")
 if up:
  for f in up:
   if not any(x["name"]==f.name and x["size"]==f.size for x in st.session_state.files):
    st.session_state.files.append({"name":f.name,"size":f.size,"bytes":f.getvalue(),"mime":f.type or "application/octet-stream"})
 if st.session_state.files:
  for i,f in enumerate(st.session_state.files):
   c1,c2=st.columns([4,1])
   c1.caption(f"📄 {f['name']} · {f['size']/1024:.1f}KB")
   if c2.button("✕",key=f"rm_{i}"):st.session_state.files.pop(i);st.rerun()
  if st.button("🗑 Rimuovi tutti",use_container_width=True):st.session_state.files=[];st.session_state.upk+=1;st.rerun()
st.markdown("## ✨ Gemini")
for m in st.session_state.msg:
 with st.chat_message(m["role"],avatar="🧑" if m["role"]=="user" else "🤖"):
  st.markdown(m["content"])
  if m.get("files"):
   for fn in m["files"]:st.caption(f"📎 {fn}")
  if m.get("ms"):st.caption(f"⏱ {m['ms']}ms"+(f"  🔧 {', '.join(m['tags'])}" if m.get("tags") else ""))
if p:=st.chat_input("Scrivi a Gemini…"):
 attached=list(st.session_state.files);fnames=[f["name"] for f in attached]
 st.session_state.msg.append({"role":"user","content":p,"files":fnames})
 with st.chat_message("user",avatar="🧑"):
  st.markdown(p)
  for fn in fnames:st.caption(f"📎 {fn}")
 with st.chat_message("assistant",avatar="🤖"):
  ph=st.empty();info=st.empty()
  if attached:info.caption(f"⬆ Upload {len(attached)} file...")
  ph.markdown("_Elaboro…_ ⏳");t0=time.perf_counter()
  try:
   uploaded_ids=[]
   for f in attached:
    with tempfile.NamedTemporaryFile(delete=False,suffix=os.path.splitext(f["name"])[1]) as tmp:
     tmp.write(f["bytes"]);tmp_path=tmp.name
    try:
     fid=cl.upload_file(tmp_path,f["name"],f["mime"],gs);uploaded_ids.append({"id":fid,"name":f["name"],"mime":f["mime"],"size":f["size"]})
    finally:
     try:os.unlink(tmp_path)
     except:pass
   info.empty()
   ans,tags=cl.chat(message=p,state=gs,use_engineer=st.session_state.eng,force_complete=st.session_state.fc,files=uploaded_ids)
   ms=int((time.perf_counter()-t0)*1000);ph.markdown(ans);st.caption(f"⏱ {ms}ms"+(f"  🔧 {', '.join(tags)}" if tags else ""))
   st.session_state.msg.append({"role":"assistant","content":ans,"ms":ms,"tags":tags})
   st.session_state.files=[];st.session_state.upk+=1
  except RuntimeError as e:info.empty();ph.error(str(e))
  except Exception as e:info.empty();ph.error(f"Errore: {e}");st.session_state.gs=SessionState()
