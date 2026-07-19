import uuid,time,json,os,requests,streamlit as st

API_BASE="https://web-production-3d4e4.up.railway.app"
API_TIMEOUT=(5,180)
UPLOAD_TIMEOUT=(5,60)
MAX_IMG_BYTES=262144
IMG_EXT={"png","jpg","jpeg","webp","gif","bmp"}
TEXT_EXT={"txt","md","csv","json","py","js","ts","html","css","xml","yaml","yml","sh","sql","c","cpp","h","java","kt","go","rs","rb","php","toml","ini","log","env"}
LANG_MAP={"py":"python","js":"javascript","ts":"typescript","sh":"bash","cpp":"cpp","c":"c","java":"java","go":"go","rs":"rust","rb":"ruby","php":"php","sql":"sql","html":"html","css":"css","json":"json","yaml":"yaml","yml":"yaml","toml":"toml","xml":"xml","md":"markdown"}
MAX_TEXT_BYTES=500000
MAX_TEXT_LINES=5000

st.set_page_config(page_title="Gemini",layout="wide",initial_sidebar_state="expanded")
st.markdown("""
<style>
#MainMenu,footer,header,.stDeployButton{display:none!important;}
.stApp{background:#0b0b0b;color:#eaeaea;}
.block-container{max-width:900px;padding-bottom:7rem;}
section[data-testid="stSidebar"]{background:#0f0f0f;border-right:1px solid #222;width:300px;}
section[data-testid="stSidebar"] .stButton>button{background:#151515;border:1px solid #222;color:#eaeaea;border-radius:10px;font-weight:500;}
section[data-testid="stSidebar"] .stButton>button:hover{background:#1a1a1a;border-color:#333;}
.stChatInput{border-radius:18px!important;border:1px solid #222!important;background:#101010!important;}
[data-testid="stChatMessage"]{padding:12px 0!important;}
.stMarkdown pre{background:#0f0f0f!important;border:1px solid #222;border-radius:10px;padding:12px;}
.stMarkdown code{background:#131313;padding:2px 6px;border-radius:6px;color:#c9c9ff;}
.stMarkdown a{color:#9aa6ff;}
small, .stCaption{color:#777!important;}
[data-testid="stFileUploader"]{background:#101010;border:1px dashed #2a2a2a;border-radius:10px;padding:8px;}
[data-testid="stFileUploader"] button{background:#151515!important;color:#ccc!important;border:1px solid #2a2a2a!important;border-radius:8px!important;}
.chip{display:inline-flex;align-items:center;gap:6px;background:#151515;border:1px solid #222;border-radius:8px;padding:5px 10px;margin:2px;font-size:12px;color:#ccc;}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px;}
.on{background:#10a37f;box-shadow:0 0 6px #10a37f;}
.off{background:#ef4444;}
.stTabs [data-baseweb="tab-list"]{gap:0;background:#101010;border-radius:10px;padding:3px;}
.stTabs [data-baseweb="tab"]{border-radius:8px;color:#888;padding:6px 16px;}
.stTabs [aria-selected="true"]{background:#1a1a1a!important;color:#eaeaea!important;}
</style>
""",unsafe_allow_html=True)

@st.cache_resource
def http():
 s=requests.Session();s.headers.update({"user-agent":"streamlit-ui"});return s

@st.cache_data(ttl=10)
def health():
 try:
  r=http().get(f"{API_BASE}/health",timeout=(3,5))
  return r.status_code==200,r.json() if r.status_code==200 else {}
 except:return False,{}

def sse_iter(resp):
 event="message";buf=[]
 for raw in resp.iter_lines(decode_unicode=True):
  if raw is None:continue
  line=raw.rstrip("\r")
  if not line:
   if buf:yield event,"\n".join(buf);event="message";buf=[]
   continue
  if line.startswith(":"):continue
  if line.startswith("event:"):event=line[6:].strip();continue
  if line.startswith("data:"):buf.append(line[5:].lstrip())
 if buf:yield event,"\n".join(buf)

def api_upload_image(data,name,mime,sid):
 files={"file":(name,data,mime)}
 form={"session_id":sid}
 r=http().post(f"{API_BASE}/upload",files=files,data=form,timeout=UPLOAD_TIMEOUT)
 j=r.json()
 if r.status_code==200 and j.get("status")=="success":return j
 raise RuntimeError(j.get("error",f"HTTP {r.status_code}"))

def api_clear_uploads(sid):
 try:http().delete(f"{API_BASE}/uploads/{sid}",timeout=(3,6))
 except:pass

def api_ask_json(q,sid,engineer,complete):
 p={"q":q,"session_id":sid,"engineer":str(engineer).lower(),"complete":str(complete).lower()}
 r=http().get(f"{API_BASE}/ask",params=p,timeout=API_TIMEOUT)
 j=r.json()
 if r.status_code==200 and j.get("status")=="success":return j
 raise RuntimeError(j.get("error",f"HTTP {r.status_code}"))

def api_ask_sse(q,sid,engineer,complete,chunk_size=220):
 p={"q":q,"session_id":sid,"engineer":str(engineer).lower(),"complete":str(complete).lower(),"chunk_size":chunk_size}
 with http().get(f"{API_BASE}/ask/stream",params=p,stream=True,timeout=API_TIMEOUT) as r:
  if r.status_code!=200:raise RuntimeError(f"HTTP {r.status_code}")
  for ev,dat in sse_iter(r):yield ev,dat

def read_text_bytes(data):
 for enc in ["utf-8","latin-1","cp1252"]:
  try:return data.decode(enc,errors="replace")
  except:continue
 return data.decode("utf-8",errors="replace")

def fmt_text_file(name,content):
 ext=os.path.splitext(name)[1].lower().lstrip(".")
 lang=LANG_MAP.get(ext,ext)
 lines=content.split("\n")
 trunc=""
 if len(lines)>MAX_TEXT_LINES:content="\n".join(lines[:MAX_TEXT_LINES]);trunc=f", truncated {len(lines)}"
 return f"\n[FILE: {name}]\n```{lang}\n{content}\n```\n"

if "sid" not in st.session_state:st.session_state.sid=str(uuid.uuid4())
if "msgs" not in st.session_state:st.session_state.msgs=[]
if "engineer" not in st.session_state:st.session_state.engineer=True
if "complete" not in st.session_state:st.session_state.complete=True
if "stream" not in st.session_state:st.session_state.stream=True
if "pending" not in st.session_state:st.session_state.pending=[]
if "upkey" not in st.session_state:st.session_state.upkey=0
if "page" not in st.session_state:st.session_state.page="chat"

ok,h=health()

with st.sidebar:
 st.markdown("### Gemini")
 st.caption(API_BASE)
 c1,c2=st.columns(2)
 if c1.button("Chat",use_container_width=True,type="primary" if st.session_state.page=="chat" else "secondary"):
  st.session_state.page="chat";st.rerun()
 if c2.button("API",use_container_width=True,type="primary" if st.session_state.page=="api" else "secondary"):
  st.session_state.page="api";st.rerun()
 st.divider()
 if st.session_state.page=="chat":
  if st.button("New chat",use_container_width=True):
   try:http().delete(f"{API_BASE}/session/{st.session_state.sid}",timeout=(3,6))
   except:pass
   st.session_state.sid=str(uuid.uuid4())
   st.session_state.msgs=[]
   st.session_state.pending=[]
   st.session_state.upkey+=1
   st.rerun()
  st.session_state.engineer=st.toggle("Prompt engineer",value=st.session_state.engineer)
  st.session_state.complete=st.toggle("Auto complete",value=st.session_state.complete)
  st.session_state.stream=st.toggle("Stream (SSE)",value=st.session_state.stream)
  st.divider()
  st.markdown("**Attachments**")
  up=st.file_uploader("upload",type=list(IMG_EXT|TEXT_EXT),accept_multiple_files=True,key=f"up_{st.session_state.upkey}",label_visibility="collapsed")
  if up:
   existing={(x["name"],x["size"]) for x in st.session_state.pending}
   for f in up:
    if (f.name,f.size) in existing:continue
    ext=os.path.splitext(f.name)[1].lower().lstrip(".")
    kind="image" if ext in IMG_EXT else "text" if ext in TEXT_EXT else "binary"
    st.session_state.pending.append({"name":f.name,"size":f.size,"bytes":f.getvalue(),"mime":f.type or "","kind":kind,"ext":ext})
  if st.session_state.pending:
   for i,f in enumerate(st.session_state.pending):
    c1,c2=st.columns([5,1])
    tag={"image":"IMG","text":"TXT","binary":"BIN"}[f["kind"]]
    c1.markdown(f"<span class='chip'>[{tag}] {f['name'][:22]}{'...' if len(f['name'])>22 else ''} · {f['size']/1024:.0f}KB</span>",unsafe_allow_html=True)
    if c2.button("x",key=f"rm_{i}"):st.session_state.pending.pop(i);st.rerun()
   if st.button("Clear all",use_container_width=True):
    st.session_state.pending=[];st.session_state.upkey+=1;st.rerun()
 st.divider()
 status_class="on" if ok else "off"
 st.markdown(f"<div><span class='dot {status_class}'></span>API {'online' if ok else 'offline'}</div>",unsafe_allow_html=True)
 st.caption(f"sessions: {h.get('sessions',0)} · uploads: {h.get('uploads',0)}")
 st.caption(f"sid: {st.session_state.sid[:20]}")

if st.session_state.page=="api":
 st.markdown(f"# API Reference\n`{API_BASE}`")
 status_class="on" if ok else "off"
 st.markdown(f"<span class='chip'><span class='dot {status_class}'></span>{'online' if ok else 'offline'}</span>",unsafe_allow_html=True)
 tab1,tab2,tab3,tab4=st.tabs(["Python","JavaScript","cURL","Endpoints"])
 with tab1:
  st.code(f'''import requests
API="{API_BASE}"
r=requests.get(f"{{API}}/ask",params={{"q":"Ciao","session_id":"my-1"}},timeout=90)
print(r.json()["answer"])''',language="python")
  st.code(f'''# streaming SSE
import requests
API="{API_BASE}"
with requests.get(f"{{API}}/ask/stream",params={{"q":"Raccontami una storia","session_id":"my-1"}},stream=True,timeout=(5,180)) as r:
    for line in r.iter_lines(decode_unicode=True):
        if line:print(line)''',language="python")
  st.code(f'''# upload immagine
import requests
API="{API_BASE}"
sid="my-1"
with open("photo.jpg","rb") as f:
    r=requests.post(f"{{API}}/upload",files={{"file":("photo.jpg",f,"image/jpeg")}},data={{"session_id":sid}})
print(r.json())
q=requests.get(f"{{API}}/ask",params={{"q":"Descrivi l'immagine","session_id":sid}})
print(q.json()["answer"])''',language="python")
 with tab2:
  st.code(f'''const API="{API_BASE}";
const r=await fetch(`${{API}}/ask?q=${{encodeURIComponent("Ciao")}}&session_id=my-1`);
const data=await r.json();
console.log(data.answer);''',language="javascript")
  st.code(f'''// SSE con EventSource
const API="{API_BASE}";
const url=`${{API}}/ask/stream?q=${{encodeURIComponent("Storia lunga")}}&session_id=my-1`;
const es=new EventSource(url);
let text="";
es.addEventListener("chunk",e=>{{text+=e.data;console.log(text);}});
es.addEventListener("done",e=>{{console.log("done",e.data);es.close();}});
es.addEventListener("error",e=>{{console.log("err",e.data);es.close();}});''',language="javascript")
  st.code(f'''// upload
const API="{API_BASE}";
const fd=new FormData();
fd.append("file",fileInput.files[0]);
fd.append("session_id","my-1");
await fetch(`${{API}}/upload`,{{method:"POST",body:fd}});''',language="javascript")
 with tab3:
  st.code(f'''curl "{API_BASE}/ask?q=Ciao&session_id=my-1"
curl -N "{API_BASE}/ask/stream?q=Storia&session_id=my-1"
curl -F "file=@photo.jpg" -F "session_id=my-1" "{API_BASE}/upload"
curl "{API_BASE}/health"
curl -X DELETE "{API_BASE}/session/my-1"''',language="bash")
 with tab4:
  st.markdown("""
| Method | Path | Description |
|---|---|---|
| GET | `/ask` | JSON response |
| GET | `/ask/stream` | SSE streaming |
| POST | `/upload` | Upload image (multipart) |
| DELETE | `/uploads/{sid}` | Clear pending uploads |
| GET | `/health` | Server status |
| GET | `/sessions` | Active sessions |
| DELETE | `/session/{sid}` | Delete session |
| POST | `/session/{sid}/reset` | Reset context |

**Query params (`/ask` and `/ask/stream`):**
- `q` (required) — question
- `session_id` (optional) — multi-turn context
- `engineer` (bool) — prompt enhancement (default true)
- `complete` (bool) — auto-complete lists (default true)
- `chunk_size` (int, stream only) — bytes per SSE chunk (default 220)

**SSE events:**
- `open` — connection ready
- `status` — processing stage
- `meta` — enhancements + files_sent
- `chunk` — content piece
- `done` — final metadata
- `error` — failure info
""")
else:
 if not ok:
  st.error(f"API offline: {API_BASE}")
  st.stop()
 if not st.session_state.msgs:
  st.markdown("### Gemini")
  st.caption("Ask anything, attach files, or explore.")

 for m in st.session_state.msgs:
  with st.chat_message(m["role"]):
   if m.get("files"):
    chips="".join(f"<span class='chip'>[{('IMG' if fi['kind']=='image' else 'TXT' if fi['kind']=='text' else 'BIN')}] {fi['name']}</span>" for fi in m["files"])
    st.markdown(chips,unsafe_allow_html=True)
   st.markdown(m["content"])
   if m.get("meta"):st.caption(m["meta"])

 q=st.chat_input("Write a message")
 if q:
  attached=list(st.session_state.pending)
  amt=[{"name":f["name"],"kind":f["kind"],"size":f["size"]} for f in attached]
  st.session_state.msgs.append({"role":"user","content":q,"files":amt})
  with st.chat_message("user"):
   if amt:
    chips="".join(f"<span class='chip'>[{('IMG' if fi['kind']=='image' else 'TXT' if fi['kind']=='text' else 'BIN')}] {fi['name']}</span>" for fi in amt)
    st.markdown(chips,unsafe_allow_html=True)
   st.markdown(q)

  with st.chat_message("assistant"):
   box=st.empty()
   info=st.empty()
   meta=st.empty()
   t0=time.perf_counter()

   final_q=q
   text_blocks=[]
   image_files=[f for f in attached if f["kind"]=="image"]
   text_files=[f for f in attached if f["kind"]=="text"]

   try:
    for f in text_files:
     if f["size"]>MAX_TEXT_BYTES:
      info.warning(f"{f['name']} too large, skipped")
      continue
     content=read_text_bytes(f["bytes"])
     text_blocks.append(fmt_text_file(f["name"],content))
    if text_blocks:final_q="".join(text_blocks)+"\n\n"+q

    uploaded_count=0
    for i,f in enumerate(image_files):
     info.markdown(f"<small>uploading {f['name']} ({i+1}/{len(image_files)})...</small>",unsafe_allow_html=True)
     if f["size"]>MAX_IMG_BYTES:
      info.error(f"{f['name']} too large ({f['size']} > {MAX_IMG_BYTES})")
      raise RuntimeError("image too large")
     mime=f["mime"] or f"image/{f['ext']}"
     res=api_upload_image(f["bytes"],f["name"],mime,st.session_state.sid)
     uploaded_count+=1

    if uploaded_count:info.markdown(f"<small>{uploaded_count} image(s) uploaded</small>",unsafe_allow_html=True)
    else:info.empty()

    box.markdown("_thinking..._")

    if st.session_state.stream:
     acc="";tags=[];files_sent=0
     for ev,dat in api_ask_sse(final_q,st.session_state.sid,st.session_state.engineer,st.session_state.complete):
      if ev=="meta":
       try:
        m=json.loads(dat)
        tags=m.get("enhancements",[])
        files_sent=m.get("files_sent",0)
       except:pass
      elif ev=="chunk":
       acc+=dat
       box.markdown(acc)
      elif ev=="done":
       try:
        d=json.loads(dat)
        ms=d.get("elapsed_ms",int((time.perf_counter()-t0)*1000))
        extras=[]
        if tags:extras.append(", ".join(tags))
        if files_sent:extras.append(f"{files_sent} file")
        cap=f"{ms} ms"+(" · "+" · ".join(extras) if extras else "")
        meta.caption(cap)
        st.session_state.msgs.append({"role":"assistant","content":acc,"meta":cap,"files":None})
       except:
        cap=f"{int((time.perf_counter()-t0)*1000)} ms"
        meta.caption(cap)
        st.session_state.msgs.append({"role":"assistant","content":acc,"meta":cap})
      elif ev=="error":
       try:box.error(json.loads(dat).get("error","error"))
       except:box.error(dat)
       break
    else:
     d=api_ask_json(final_q,st.session_state.sid,st.session_state.engineer,st.session_state.complete)
     ans=d["answer"];tags=d.get("enhancements",[]);files_sent=d.get("files_sent",0)
     ms=d.get("elapsed_ms",int((time.perf_counter()-t0)*1000))
     extras=[]
     if tags:extras.append(", ".join(tags))
     if files_sent:extras.append(f"{files_sent} file")
     cap=f"{ms} ms"+(" · "+" · ".join(extras) if extras else "")
     box.markdown(ans)
     meta.caption(cap)
     st.session_state.msgs.append({"role":"assistant","content":ans,"meta":cap})

    st.session_state.pending=[]
    st.session_state.upkey+=1

   except Exception as e:
    info.empty()
    box.error(str(e))
    api_clear_uploads(st.session_state.sid)
