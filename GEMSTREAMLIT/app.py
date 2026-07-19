import uuid,time,streamlit as st,sys,os,traceback,json
sys.path.insert(0,os.path.dirname(__file__))
from core.client import GeminiClient
from core.session import SessionState
st.set_page_config(page_title="Gemini",page_icon="✨",layout="wide",initial_sidebar_state="expanded")
qp=st.query_params
API_MODE=("q" in qp) or (qp.get("mode")=="api")
if API_MODE:
 st.markdown("<style>#MainMenu,footer,header,section[data-testid='stSidebar'],[data-testid='stToolbar']{display:none!important;}.block-container{padding:0!important;max-width:100%!important;}.stApp{background:#0a0a0a;}</style>",unsafe_allow_html=True)
 t0=time.perf_counter()
 q=qp.get("q","").strip()
 sid=qp.get("session_id","") or qp.get("sid","")
 use_eng=qp.get("engineer","true").lower() not in("false","0","no")
 use_fc=qp.get("complete","true").lower() not in("false","0","no")
 result={}
 if not q:
  result={"status":"error","error":"Missing 'q' parameter","usage":"?q=your+question&session_id=optional"}
 else:
  try:
   if "api_sessions" not in st.session_state:st.session_state.api_sessions={}
   if sid and sid in st.session_state.api_sessions:state=st.session_state.api_sessions[sid]
   else:
    state=SessionState()
    if not sid:sid=str(uuid.uuid4())
    st.session_state.api_sessions[sid]=state
   client=GeminiClient()
   if not state.bl:client.bootstrap(state)
   ans,tags=client.chat(message=q,state=state,use_engineer=use_eng,force_complete=use_fc)
   result={"status":"success","answer":ans,"session_id":sid,"enhancements":tags,"elapsed_ms":int((time.perf_counter()-t0)*1000)}
  except Exception as e:
   result={"status":"error","error":str(e),"elapsed_ms":int((time.perf_counter()-t0)*1000)}
 st.code(json.dumps(result,ensure_ascii=False,indent=2),language="json")
 st.stop()
CSS="""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
*{font-family:'Inter',sans-serif;}
#MainMenu,footer,header,.stDeployButton{visibility:hidden;display:none;}
.block-container{padding:0.5rem 1rem 8rem;max-width:860px;}
.stApp{background:#0a0a0a;}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0f0f0f,#141414);border-right:1px solid rgba(255,255,255,0.06);width:280px;}
section[data-testid="stSidebar"] .stButton>button{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);color:#e0e0e0;border-radius:12px;font-weight:500;font-size:14px;padding:10px 16px;transition:all .2s;}
section[data-testid="stSidebar"] .stButton>button:hover{background:rgba(139,92,246,0.12);border-color:rgba(139,92,246,0.3);}
[data-testid="stChatMessage"]{background:transparent!important;border:none!important;padding:1rem 0!important;margin:0!important;animation:msgIn .3s ease;}
@keyframes msgIn{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);}}
[data-testid="stChatMessage"] p{font-size:15px;line-height:1.75;color:#e8e8e8;}
.stChatInput{background:rgba(255,255,255,0.04)!important;border:1px solid rgba(255,255,255,0.08)!important;border-radius:24px!important;padding:6px 8px!important;}
.stChatInput:focus-within{border-color:rgba(139,92,246,0.5)!important;box-shadow:0 0 0 3px rgba(139,92,246,0.1)!important;}
[data-testid="stChatInputTextArea"]{background:transparent!important;color:#e8e8e8!important;font-size:15px!important;}
.stChatFloatingInputContainer{background:linear-gradient(180deg,transparent,#0a0a0a 35%)!important;padding:2rem 0 1.5rem;}
.stMarkdown code{background:rgba(139,92,246,0.1);padding:2px 7px;border-radius:6px;color:#c4b5fd;font-size:13px;font-family:'JetBrains Mono',monospace;}
.stMarkdown pre{background:#111!important;border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:16px;}
.stMarkdown pre code{background:transparent;padding:0;color:#e8e8e8;font-size:13px;}
.stMarkdown a{color:#818cf8;text-decoration:none;border-bottom:1px solid rgba(129,140,248,0.3);}
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3{color:#f5f5f5!important;font-weight:600;}
.stCaption{color:#666!important;font-size:12px!important;font-family:'JetBrains Mono',monospace!important;}
.stTabs [data-baseweb="tab-list"]{gap:0;background:rgba(255,255,255,0.02);border-radius:12px;padding:4px;}
.stTabs [data-baseweb="tab"]{background:transparent;border-radius:10px;color:#888;font-weight:500;padding:8px 20px;border:none;}
.stTabs [aria-selected="true"]{background:rgba(139,92,246,0.15)!important;color:#c4b5fd!important;}
[data-testid="stFileUploader"]{background:rgba(255,255,255,0.02);border:1px dashed rgba(255,255,255,0.1);border-radius:14px;padding:10px;}
[data-testid="stFileUploader"] button{background:rgba(139,92,246,0.1)!important;color:#c4b5fd!important;border:none!important;border-radius:8px!important;}
.stToggle label{color:#ccc!important;font-size:14px;}
.hero{text-align:center;padding:5rem 1rem 2rem;}
.hero-icon{font-size:3.5rem;margin-bottom:1rem;filter:drop-shadow(0 0 20px rgba(139,92,246,0.4));}
.hero-title{font-size:2.5rem;font-weight:700;background:linear-gradient(135deg,#8B5CF6,#EC4899,#F59E0B);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:0.5rem;letter-spacing:-0.03em;}
.hero-sub{color:#666;font-size:1rem;}
.chip{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:7px 12px;margin:3px;font-size:13px;color:#d0d0d0;}
.meta{display:flex;gap:12px;color:#555;font-size:12px;margin-top:8px;align-items:center;font-family:'JetBrains Mono',monospace;}
.meta-tag{background:rgba(139,92,246,0.08);padding:3px 10px;border-radius:8px;color:#a78bfa;font-size:11px;}
.api-card{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:16px;padding:24px;margin:12px 0;transition:all .2s;}
.api-card:hover{border-color:rgba(139,92,246,0.2);}
.api-method{display:inline-block;padding:4px 12px;border-radius:6px;font-weight:700;font-size:12px;font-family:'JetBrains Mono',monospace;}
.api-get{background:rgba(16,185,129,0.15);color:#34d399;}
.api-url{color:#e8e8e8;font-family:'JetBrains Mono',monospace;font-size:14px;margin-left:10px;}
.api-desc{color:#888;font-size:14px;margin-top:8px;}
.api-param{display:grid;grid-template-columns:120px 80px 1fr;gap:8px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04);font-size:13px;}
.api-param-name{color:#c4b5fd;font-family:'JetBrains Mono',monospace;}
.api-param-type{color:#666;font-family:'JetBrains Mono',monospace;}
.api-param-desc{color:#999;}
.api-required{color:#f87171;font-size:10px;margin-left:4px;}
.status-pill{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;font-size:12px;}
.status-online{background:rgba(16,185,129,0.1);color:#34d399;border:1px solid rgba(16,185,129,0.2);}
.status-offline{background:rgba(239,68,68,0.1);color:#f87171;border:1px solid rgba(239,68,68,0.2);}
.status-dot{width:8px;height:8px;border-radius:50%;display:inline-block;}
.status-on{background:#10a37f;box-shadow:0 0 6px #10a37f;}
.status-off{background:#ef4444;}
.section-title{font-size:11px;text-transform:uppercase;letter-spacing:1.5px;font-weight:600;color:#555;margin:24px 0 12px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.04);}
.warn-box{background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.2);border-radius:12px;padding:16px;margin:16px 0;color:#fbbf24;font-size:13px;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.08);border-radius:3px;}
</style>
"""
st.markdown(CSS,unsafe_allow_html=True)
TEXT_EXT={".txt",".md",".csv",".json",".py",".js",".ts",".jsx",".tsx",".html",".css",".xml",".yaml",".yml",".sh",".sql",".c",".cpp",".h",".hpp",".java",".kt",".go",".rs",".rb",".php",".toml",".ini",".log",".env"}
IMG_EXT={".png",".jpg",".jpeg",".webp",".gif",".bmp"}
LANG_MAP={"py":"python","js":"javascript","ts":"typescript","sh":"bash","cpp":"cpp","c":"c","java":"java","go":"go","rs":"rust","rb":"ruby","php":"php","sql":"sql","html":"html","css":"css","json":"json","yaml":"yaml","yml":"yaml","toml":"toml","xml":"xml","md":"markdown"}
def is_text(n,m):
 e=os.path.splitext(n)[1].lower()
 return e in TEXT_EXT or(m and(m.startswith("text/") or m in("application/json","application/xml")))
def is_image(n,m):
 e=os.path.splitext(n)[1].lower()
 return e in IMG_EXT or(m and m.startswith("image/"))
def read_text(data,name):
 for enc in["utf-8","latin-1","cp1252"]:
  try:return data.decode(enc,errors="replace")
  except:continue
 return data.decode("utf-8",errors="replace")
def fmt_file(name,content):
 ext=os.path.splitext(name)[1].lower().lstrip(".")
 lang=LANG_MAP.get(ext,ext)
 lines=content.split("\n")
 trunc=""
 if len(lines)>5000:content="\n".join(lines[:5000]);trunc=f", truncated {len(lines)}"
 return f"\n[FILE: {name}]\n```{lang}\n{content}\n```\n"
@st.cache_resource
def gc():return GeminiClient()
def _i():
 for k,v in[("sid",str(uuid.uuid4())),("msg",[]),("gs",SessionState()),("eng",True),("fc",True),("pending",[]),("upk",0),("debug",False),("page","chat")]:
  if k not in st.session_state:st.session_state[k]=v
_i()
cl=gc()
gs=st.session_state.gs
if not gs.bl:
 with st.spinner("⚡"):
  try:cl.bootstrap(gs)
  except Exception as e:st.error(f"Bootstrap: {e}");st.stop()
try:BASE_URL="https://"+st.context.headers.get("host","sqxm2q7rdoyeglk8rbuqxm.streamlit.app")
except:BASE_URL="https://sqxm2q7rdoyeglk8rbuqxm.streamlit.app"
with st.sidebar:
 st.markdown("""<div style='padding:12px 4px 24px;'>
  <div style='font-size:22px;font-weight:700;background:linear-gradient(135deg,#8B5CF6,#EC4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>✨ Gemini</div>
  <div style='color:#555;font-size:11px;margin-top:4px;font-family:JetBrains Mono,monospace;'>v14 · Chat + API</div>
 </div>""",unsafe_allow_html=True)
 c1,c2=st.columns(2)
 if c1.button("💬 Chat",use_container_width=True,type="primary" if st.session_state.page=="chat" else "secondary"):st.session_state.page="chat";st.rerun()
 if c2.button("⚡ API",use_container_width=True,type="primary" if st.session_state.page=="api" else "secondary"):st.session_state.page="api";st.rerun()
 if st.session_state.page=="chat":
  st.markdown("")
  if st.button("＋ Nuova chat",use_container_width=True):
   st.session_state.sid=str(uuid.uuid4());st.session_state.msg=[];st.session_state.gs=SessionState();st.session_state.pending=[];st.session_state.upk+=1;st.rerun()
  st.markdown("<div class='section-title'>Impostazioni</div>",unsafe_allow_html=True)
  st.session_state.eng=st.toggle("🔧 Prompt Engineer",value=st.session_state.eng)
  st.session_state.fc=st.toggle("📝 Auto-completa",value=st.session_state.fc)
  st.session_state.debug=st.toggle("🐛 Debug",value=st.session_state.debug)
  st.markdown("<div class='section-title'>📎 Allegati</div>",unsafe_allow_html=True)
  up=st.file_uploader("Upload",type=["png","jpg","jpeg","webp","gif","bmp","txt","md","csv","json","py","js","html","css","yaml","yml","sh","sql","c","cpp","java","go","rs","toml","log"],accept_multiple_files=True,key=f"up_{st.session_state.upk}",label_visibility="collapsed")
  if up:
   existing={(x["name"],x["size"]) for x in st.session_state.pending}
   for f in up:
    if(f.name,f.size) not in existing:
     mime=f.type or ""
     kind="text" if is_text(f.name,mime) else "image" if is_image(f.name,mime) else "binary"
     st.session_state.pending.append({"name":f.name,"size":f.size,"bytes":f.getvalue(),"mime":mime,"kind":kind})
  if st.session_state.pending:
   for i,f in enumerate(st.session_state.pending):
    c1,c2=st.columns([5,1])
    ic={"image":"🖼","text":"📝","binary":"📦"}.get(f["kind"],"📄")
    c1.markdown(f"<div class='chip'>{ic} {f['name'][:20]}{'…' if len(f['name'])>20 else ''}</div>",unsafe_allow_html=True)
    if c2.button("✕",key=f"rm_{i}"):st.session_state.pending.pop(i);st.rerun()
 dot="status-on" if gs.bl else "status-off"
 st.markdown(f"""<div style='position:absolute;bottom:16px;left:16px;right:16px;'>
  <div class='status-pill {"status-online" if gs.bl else "status-offline"}'><span class='status-dot {dot}'></span>{"Online" if gs.bl else "Offline"}</div>
 </div>""",unsafe_allow_html=True)
if st.session_state.page=="api":
 st.markdown("""<div style='padding:2rem 0 1rem;'>
  <h1 style='font-size:2rem;font-weight:700;background:linear-gradient(135deg,#8B5CF6,#EC4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;'>⚡ API Reference</h1>
  <p style='color:#666;font-size:14px;margin-top:8px;'>Chiama Gemini direttamente via HTTP GET. Nessuna API key.</p>
 </div>""",unsafe_allow_html=True)
 st.markdown(f"""<div class='api-card'>
  <div><span class='api-method api-get'>GET</span><span class='api-url'>{BASE_URL}/?q=YOUR_QUESTION</span></div>
  <div class='api-desc'>Ritorna JSON con la risposta di Gemini. Parse con regex o BeautifulSoup lato client (vedi esempi).</div>
  <div style='margin-top:20px;'>
   <div style='color:#888;font-size:12px;font-weight:600;margin-bottom:8px;'>QUERY PARAMS</div>
   <div class='api-param'><span class='api-param-name'>q<span class='api-required'>*</span></span><span class='api-param-type'>string</span><span class='api-param-desc'>Domanda per Gemini (URL-encoded)</span></div>
   <div class='api-param'><span class='api-param-name'>session_id</span><span class='api-param-type'>string</span><span class='api-param-desc'>Mantiene il contesto tra chiamate</span></div>
   <div class='api-param'><span class='api-param-name'>engineer</span><span class='api-param-type'>bool</span><span class='api-param-desc'>Prompt engineering (default: true)</span></div>
   <div class='api-param'><span class='api-param-name'>complete</span><span class='api-param-type'>bool</span><span class='api-param-desc'>Auto-completa liste (default: true)</span></div>
  </div>
 </div>""",unsafe_allow_html=True)
 st.markdown("""<div class='warn-box'>⚠ <b>Nota tecnica:</b> Streamlit non è un vero server API, quindi la risposta è HTML con il JSON dentro un &lt;code&gt;. Usa gli helper qui sotto per estrarlo.</div>""",unsafe_allow_html=True)
 tab1,tab2,tab3,tab4=st.tabs(["🐍 Python","🌐 JavaScript","🔧 cURL","📦 Response"])
 with tab1:
  st.code(f'''import requests, re, json

def ask_gemini(question, session_id=None, base="{BASE_URL}"):
    """Chiama Gemini via URL query e ritorna dict."""
    params = {{"q": question}}
    if session_id: params["session_id"] = session_id
    r = requests.get(base, params=params, timeout=60)
    # Estrai JSON dall'HTML di Streamlit
    m = re.search(r'<code[^>]*>(\\{{[^<]+\\}})</code>', r.text, re.DOTALL)
    if not m:
        # Fallback: cerca pre>code
        m = re.search(r'<pre[^>]*><code[^>]*>(\\{{.*?\\}})</code></pre>', r.text, re.DOTALL)
    if not m:
        raise Exception("JSON non trovato nella risposta")
    return json.loads(m.group(1))

# USO
data = ask_gemini("Ciao come stai?")
print(data["answer"])
print(f"Tempo: {{data['elapsed_ms']}}ms")

# Conversazione multi-turno
sid = "my-session-1"
data1 = ask_gemini("Ciao, mi chiamo Andrea", sid)
data2 = ask_gemini("Come mi chiamo?", sid)
print(data2["answer"])''',language="python")
 with tab2:
  st.code(f'''async function askGemini(question, sessionId = null) {{
  const url = new URL("{BASE_URL}/");
  url.searchParams.set("q", question);
  if (sessionId) url.searchParams.set("session_id", sessionId);
  const r = await fetch(url);
  const html = await r.text();
  // Estrai JSON dal blocco <code>
  const match = html.match(/<code[^>]*>(\\{{[\\s\\S]+?\\}})<\\/code>/);
  if (!match) throw new Error("JSON non trovato");
  return JSON.parse(match[1]);
}}

// USO
const data = await askGemini("Cos'è il quantum computing?");
console.log(data.answer);''',language="javascript")
 with tab3:
  st.code(f'''# Chiamata base
curl "{BASE_URL}/?q=Ciao+come+stai"

# Con jq per estrarre il JSON
curl -s "{BASE_URL}/?q=Ciao" | grep -oP '<code[^>]*>\\K[^<]+' | head -1 | jq

# Con Python one-liner
curl -s "{BASE_URL}/?q=Ciao" | python -c "import sys,re,json; m=re.search(r'<code[^>]*>({{[^<]+}})</code>',sys.stdin.read()); print(json.loads(m.group(1))['answer'])"''',language="bash")
 with tab4:
  st.code(json.dumps({"status":"success","answer":"Ciao! Sto benissimo, grazie. Come posso aiutarti?","session_id":"abc-123","enhancements":[],"elapsed_ms":3420},indent=2,ensure_ascii=False),language="json")
  st.markdown("""<div style='margin-top:16px;'>
   <div class='api-param'><span class='api-param-name'>status</span><span class='api-param-type'>str</span><span class='api-param-desc'>"success" o "error"</span></div>
   <div class='api-param'><span class='api-param-name'>answer</span><span class='api-param-type'>str</span><span class='api-param-desc'>Risposta Gemini (markdown)</span></div>
   <div class='api-param'><span class='api-param-name'>session_id</span><span class='api-param-type'>str</span><span class='api-param-desc'>ID sessione (riusa)</span></div>
   <div class='api-param'><span class='api-param-name'>enhancements</span><span class='api-param-type'>list</span><span class='api-param-desc'>Tag ottimizzazioni</span></div>
   <div class='api-param'><span class='api-param-name'>elapsed_ms</span><span class='api-param-type'>int</span><span class='api-param-desc'>Tempo di risposta</span></div>
  </div>""",unsafe_allow_html=True)
 st.markdown("<h3 style='color:#e8e8e8;font-size:18px;font-weight:600;margin-top:32px;'>🧪 Live Playground</h3>",unsafe_allow_html=True)
 pc1,pc2=st.columns([3,1])
 test_q=pc1.text_input("Domanda",value="Dimmi una curiosità sui polpi",label_visibility="collapsed")
 test_go=pc2.button("▶ Prova",use_container_width=True,type="primary")
 if test_go and test_q:
  st.markdown(f"<div style='color:#666;font-size:12px;margin:8px 0;'>Chiamando: <code>{BASE_URL}/?q={test_q.replace(' ','+')[:60]}...</code></div>",unsafe_allow_html=True)
  with st.spinner("⚡ In corso..."):
   t0=time.perf_counter()
   try:
    test_state=SessionState()
    cl.bootstrap(test_state)
    ans,tags=cl.chat(message=test_q,state=test_state,use_engineer=True,force_complete=False)
    ms=int((time.perf_counter()-t0)*1000)
    result={"status":"success","answer":ans,"session_id":str(uuid.uuid4())[:8],"enhancements":tags,"elapsed_ms":ms}
    st.code(json.dumps(result,indent=2,ensure_ascii=False),language="json")
    st.caption(f"⏱ {ms}ms")
   except Exception as e:
    st.code(json.dumps({"status":"error","error":str(e)},indent=2),language="json")
 st.markdown(f"""<div style='margin-top:32px;padding:20px;background:rgba(139,92,246,0.04);border:1px solid rgba(139,92,246,0.1);border-radius:14px;'>
  <div style='color:#a78bfa;font-weight:600;font-size:14px;'>💡 Come funziona</div>
  <ul style='color:#888;font-size:13px;line-height:2;margin-top:8px;'>
   <li>Aggiungi <code>?q=DOMANDA</code> all'URL base per attivare modalità API</li>
   <li>Streamlit renderizza SOLO il JSON, senza UI</li>
   <li>Estrai con regex <code>&lt;code&gt;(JSON)&lt;/code&gt;</code></li>
   <li>Rate limit: ~30 req/min per IP</li>
   <li>Sessioni: in RAM (persistono finché il server è attivo)</li>
   <li>Test in browser: <a href="{BASE_URL}/?q=Ciao" target="_blank">apri esempio</a></li>
  </ul>
 </div>""",unsafe_allow_html=True)
elif st.session_state.page=="chat":
 if not st.session_state.msg:
  st.markdown("""<div class='hero'>
   <div class='hero-icon'>✨</div>
   <div class='hero-title'>Come posso aiutarti?</div>
   <div class='hero-sub'>Chat, analisi file, coding, ricerche — gratis</div>
  </div>""",unsafe_allow_html=True)
 for m in st.session_state.msg:
  with st.chat_message(m["role"],avatar="👤" if m["role"]=="user" else "✨"):
   if m.get("files"):
    chips="".join(f"<span class='chip'>{'🖼' if fi.get('kind')=='image' else '📝'} {fi['name']}</span>" for fi in m["files"])
    st.markdown(f"<div style='margin-bottom:8px;'>{chips}</div>",unsafe_allow_html=True)
   st.markdown(m["content"])
   if m.get("ms"):
    tags_html="".join(f"<span class='meta-tag'>{t}</span>" for t in(m.get("tags") or[]))
    st.markdown(f"<div class='meta'><span>⏱ {m['ms']}ms</span>{tags_html}</div>",unsafe_allow_html=True)
 if p:=st.chat_input("Scrivi a Gemini..."):
  attached=list(st.session_state.pending)
  amt=[{"name":f["name"],"kind":f["kind"],"size":f["size"]} for f in attached]
  st.session_state.msg.append({"role":"user","content":p,"files":amt})
  with st.chat_message("user",avatar="👤"):
   if amt:
    chips="".join(f"<span class='chip'>{'🖼' if fi['kind']=='image' else '📝'} {fi['name']}</span>" for fi in amt)
    st.markdown(f"<div style='margin-bottom:8px;'>{chips}</div>",unsafe_allow_html=True)
   st.markdown(p)
  with st.chat_message("assistant",avatar="✨"):
   ph=st.empty()
   info=st.empty()
   t0=time.perf_counter()
   final_prompt=p
   uploaded=[]
   text_blocks=[]
   try:
    text_files=[f for f in attached if f["kind"]=="text"]
    image_files=[f for f in attached if f["kind"]=="image"]
    for f in text_files:
     if f["size"]>500000:info.warning(f"⚠ {f['name']} troppo grande");continue
     content=read_text(f["bytes"],f["name"])
     text_blocks.append(fmt_file(f["name"],content))
    if text_blocks:final_prompt="".join(text_blocks)+"\n\n"+p
    if image_files:
     for idx,f in enumerate(image_files):
      info.markdown(f"<div style='color:#888;font-size:13px;'>⬆ {f['name']} ({idx+1}/{len(image_files)})…</div>",unsafe_allow_html=True)
      try:
       result=cl.upload_image(f["bytes"],f["name"],f["mime"] or"image/jpeg")
       uploaded.append(result)
      except Exception as ue:info.error(f"❌ {f['name']}: {ue}");raise
     info.markdown(f"<div style='color:#34d399;font-size:13px;'>✓ {len(uploaded)} immagini</div>",unsafe_allow_html=True)
    ph.markdown("<div style='color:#888;font-size:14px;'>Sto pensando ✨</div>",unsafe_allow_html=True)
    ans,tags=cl.chat(message=final_prompt,state=gs,use_engineer=st.session_state.eng,force_complete=st.session_state.fc,files=uploaded if uploaded else None)
    ms=int((time.perf_counter()-t0)*1000)
    info.empty()
    ph.markdown(ans)
    tags_html="".join(f"<span class='meta-tag'>{t}</span>" for t in tags)
    st.markdown(f"<div class='meta'><span>⏱ {ms}ms</span>{tags_html}</div>",unsafe_allow_html=True)
    st.session_state.msg.append({"role":"assistant","content":ans,"ms":ms,"tags":tags})
    st.session_state.pending=[]
    st.session_state.upk+=1
   except RuntimeError as e:
    info.empty();ph.error(f"⚠ {e}")
    if st.session_state.debug:st.code(traceback.format_exc())
   except Exception as e:
    info.empty();ph.error(f"⚠ {type(e).__name__}: {e}")
    if st.session_state.debug:st.code(traceback.format_exc())
    st.session_state.gs=SessionState()
