import uuid,time,streamlit as st,sys,os,traceback,json
sys.path.insert(0,os.path.dirname(__file__))
from core.client import GeminiClient
from core.session import SessionState
st.set_page_config(page_title="Gemini",page_icon="✨",layout="wide",initial_sidebar_state="expanded")
CSS="""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
*{font-family:'Inter',sans-serif;}
#MainMenu,footer,header,.stDeployButton{visibility:hidden;display:none;}
.block-container{padding:0.5rem 1rem 8rem;max-width:860px;}
.stApp{background:#0a0a0a;}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0f0f0f 0%,#141414 100%);border-right:1px solid rgba(255,255,255,0.06);width:280px;}
section[data-testid="stSidebar"] .stButton>button{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);color:#e0e0e0;border-radius:12px;font-weight:500;font-size:14px;padding:10px 16px;transition:all .2s cubic-bezier(.4,0,.2,1);}
section[data-testid="stSidebar"] .stButton>button:hover{background:rgba(139,92,246,0.12);border-color:rgba(139,92,246,0.3);transform:translateY(-1px);box-shadow:0 4px 12px rgba(139,92,246,0.15);}
[data-testid="stChatMessage"]{background:transparent!important;border:none!important;padding:1rem 0!important;margin:0!important;animation:msgIn .3s ease;}
@keyframes msgIn{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);}}
[data-testid="stChatMessage"] p{font-size:15px;line-height:1.75;color:#e8e8e8;letter-spacing:0.01em;}
.stChatInput{background:rgba(255,255,255,0.04)!important;border:1px solid rgba(255,255,255,0.08)!important;border-radius:24px!important;padding:6px 8px!important;backdrop-filter:blur(20px);transition:all .2s;}
.stChatInput:focus-within{border-color:rgba(139,92,246,0.5)!important;box-shadow:0 0 0 3px rgba(139,92,246,0.1),0 8px 32px rgba(0,0,0,0.3)!important;}
[data-testid="stChatInputTextArea"]{background:transparent!important;color:#e8e8e8!important;font-size:15px!important;font-family:'Inter',sans-serif!important;}
.stChatFloatingInputContainer{background:linear-gradient(180deg,transparent 0%,#0a0a0a 35%)!important;padding:2rem 0 1.5rem;}
.stMarkdown code{background:rgba(139,92,246,0.1);padding:2px 7px;border-radius:6px;color:#c4b5fd;font-size:13px;font-family:'JetBrains Mono',monospace;}
.stMarkdown pre{background:#111!important;border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:16px;overflow-x:auto;}
.stMarkdown pre code{background:transparent;padding:0;color:#e8e8e8;font-size:13px;}
.stMarkdown a{color:#818cf8;text-decoration:none;border-bottom:1px solid rgba(129,140,248,0.3);transition:all .15s;}
.stMarkdown a:hover{color:#a5b4fc;border-bottom-color:rgba(129,140,248,0.6);}
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3{color:#f5f5f5!important;font-weight:600;letter-spacing:-0.02em;}
.stMarkdown blockquote{border-left:3px solid #8B5CF6;padding-left:16px;color:#a0a0a0;}
.stMarkdown table{border-collapse:collapse;width:100%;}
.stMarkdown th{background:rgba(139,92,246,0.1);padding:10px 14px;text-align:left;font-weight:600;border-bottom:2px solid rgba(139,92,246,0.2);}
.stMarkdown td{padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.04);}
.stCaption{color:#666!important;font-size:12px!important;font-family:'JetBrains Mono',monospace!important;}
.stTabs [data-baseweb="tab-list"]{gap:0;background:rgba(255,255,255,0.02);border-radius:12px;padding:4px;}
.stTabs [data-baseweb="tab"]{background:transparent;border-radius:10px;color:#888;font-weight:500;font-size:14px;padding:8px 20px;border:none;}
.stTabs [aria-selected="true"]{background:rgba(139,92,246,0.15)!important;color:#c4b5fd!important;}
.stTabs [data-baseweb="tab-panel"]{padding-top:20px;}
[data-testid="stFileUploader"]{background:rgba(255,255,255,0.02);border:1px dashed rgba(255,255,255,0.1);border-radius:14px;padding:10px;transition:border-color .2s;}
[data-testid="stFileUploader"]:hover{border-color:rgba(139,92,246,0.3);}
[data-testid="stFileUploader"] button{background:rgba(139,92,246,0.1)!important;color:#c4b5fd!important;border:none!important;border-radius:8px!important;}
.stToggle label{color:#ccc!important;font-size:14px;}
.hero{text-align:center;padding:6rem 1rem 3rem;}
.hero-icon{font-size:3.5rem;margin-bottom:1rem;filter:drop-shadow(0 0 20px rgba(139,92,246,0.4));}
.hero-title{font-size:2.5rem;font-weight:700;background:linear-gradient(135deg,#8B5CF6 0%,#EC4899 50%,#F59E0B 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:0.5rem;letter-spacing:-0.03em;}
.hero-sub{color:#666;font-size:1rem;font-weight:400;}
.chip{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:7px 12px;margin:3px;font-size:13px;color:#d0d0d0;transition:all .15s;}
.chip:hover{background:rgba(139,92,246,0.08);border-color:rgba(139,92,246,0.2);}
.meta{display:flex;gap:12px;color:#555;font-size:12px;margin-top:8px;align-items:center;font-family:'JetBrains Mono',monospace;}
.meta-tag{background:rgba(139,92,246,0.08);padding:3px 10px;border-radius:8px;color:#a78bfa;font-size:11px;font-weight:500;}
.api-card{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:16px;padding:24px;margin:12px 0;transition:all .2s;}
.api-card:hover{border-color:rgba(139,92,246,0.2);background:rgba(139,92,246,0.02);}
.api-method{display:inline-block;padding:4px 12px;border-radius:6px;font-weight:700;font-size:12px;font-family:'JetBrains Mono',monospace;letter-spacing:0.05em;}
.api-get{background:rgba(16,185,129,0.15);color:#34d399;}
.api-post{background:rgba(59,130,246,0.15);color:#60a5fa;}
.api-url{color:#e8e8e8;font-family:'JetBrains Mono',monospace;font-size:14px;margin-left:10px;}
.api-desc{color:#888;font-size:14px;margin-top:8px;line-height:1.6;}
.api-param{display:grid;grid-template-columns:120px 80px 1fr;gap:8px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04);font-size:13px;}
.api-param-name{color:#c4b5fd;font-family:'JetBrains Mono',monospace;font-weight:500;}
.api-param-type{color:#666;font-family:'JetBrains Mono',monospace;}
.api-param-desc{color:#999;}
.api-required{color:#f87171;font-size:10px;font-weight:600;margin-left:4px;}
.status-pill{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:500;}
.status-online{background:rgba(16,185,129,0.1);color:#34d399;border:1px solid rgba(16,185,129,0.2);}
.status-offline{background:rgba(239,68,68,0.1);color:#f87171;border:1px solid rgba(239,68,68,0.2);}
.copy-btn{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:6px 14px;color:#999;font-size:12px;cursor:pointer;font-family:'JetBrains Mono',monospace;transition:all .15s;}
.copy-btn:hover{background:rgba(139,92,246,0.1);color:#c4b5fd;border-color:rgba(139,92,246,0.3);}
.section-title{font-size:11px;text-transform:uppercase;letter-spacing:1.5px;font-weight:600;color:#555;margin:24px 0 12px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.04);}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.08);border-radius:3px;}
::-webkit-scrollbar-thumb:hover{background:rgba(255,255,255,0.15);}
</style>
"""
st.markdown(CSS,unsafe_allow_html=True)
TEXT_EXT={".txt",".md",".csv",".json",".py",".js",".ts",".jsx",".tsx",".html",".css",".xml",".yaml",".yml",".sh",".bash",".sql",".c",".cpp",".h",".hpp",".java",".kt",".go",".rs",".rb",".php",".swift",".toml",".ini",".cfg",".log",".env"}
IMG_EXT={".png",".jpg",".jpeg",".webp",".gif",".bmp"}
LANG_MAP={"py":"python","js":"javascript","ts":"typescript","sh":"bash","cpp":"cpp","c":"c","java":"java","go":"go","rs":"rust","rb":"ruby","php":"php","sql":"sql","html":"html","css":"css","json":"json","yaml":"yaml","yml":"yaml","toml":"toml","xml":"xml","md":"markdown"}
MAX_TEXT_BYTES=500000
MAX_TEXT_LINES=5000
BASE_URL="https://sqxm2q7rdoyeglk8rbuqxm.streamlit.app"
def is_text(n,m):
 e=os.path.splitext(n)[1].lower()
 return e in TEXT_EXT or (m and(m.startswith("text/") or m in("application/json","application/xml","application/javascript")))
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
 if len(lines)>MAX_TEXT_LINES:content="\n".join(lines[:MAX_TEXT_LINES]);trunc=f", troncato a {MAX_TEXT_LINES}/{len(lines)}"
 return f"\n[FILE: {name} ({len(content)}B, {len(lines)} righe{trunc})]\n```{lang}\n{content}\n```\n"
@st.cache_resource
def gc():return GeminiClient()
def _i():
 for k,v in[("sid",str(uuid.uuid4())),("msg",[]),("gs",SessionState()),("eng",True),("fc",True),("pending",[]),("upk",0),("debug",False),("page","chat")]:
  if k not in st.session_state:st.session_state[k]=v
_i()
cl=gc()
gs=st.session_state.gs
if not gs.bl:
 with st.spinner("⚡ Connessione..."):
  try:cl.bootstrap(gs)
  except Exception as e:st.error(f"Bootstrap: {e}");st.stop()
with st.sidebar:
 st.markdown("""<div style='padding:12px 4px 24px;'>
  <div style='font-size:22px;font-weight:700;background:linear-gradient(135deg,#8B5CF6,#EC4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:-0.02em;'>✨ Gemini</div>
  <div style='color:#555;font-size:11px;margin-top:4px;font-family:JetBrains Mono,monospace;'>v14 · API + Chat</div>
 </div>""",unsafe_allow_html=True)
 c1,c2=st.columns(2)
 if c1.button("💬 Chat",use_container_width=True,type="primary" if st.session_state.page=="chat" else "secondary"):st.session_state.page="chat"
 if c2.button("⚡ API",use_container_width=True,type="primary" if st.session_state.page=="api" else "secondary"):st.session_state.page="api"
 if st.session_state.page=="chat":
  st.markdown("")
  if st.button("＋ Nuova chat",use_container_width=True):
   st.session_state.sid=str(uuid.uuid4());st.session_state.msg=[];st.session_state.gs=SessionState();st.session_state.pending=[];st.session_state.upk+=1;st.rerun()
  st.markdown("<div class='section-title'>Impostazioni</div>",unsafe_allow_html=True)
  st.session_state.eng=st.toggle("🔧 Prompt Engineer",value=st.session_state.eng,help="Riscrive i prompt per risposte migliori")
  st.session_state.fc=st.toggle("📝 Auto-completa",value=st.session_state.fc,help="Forza completamento liste numeriche")
  st.session_state.debug=st.toggle("🐛 Debug",value=st.session_state.debug)
  st.markdown("<div class='section-title'>📎 Allegati</div>",unsafe_allow_html=True)
  up=st.file_uploader("Upload",type=["png","jpg","jpeg","webp","gif","bmp","txt","md","csv","json","py","js","ts","html","css","xml","yaml","yml","sh","sql","c","cpp","java","go","rs","rb","php","toml","log"],accept_multiple_files=True,key=f"up_{st.session_state.upk}",label_visibility="collapsed")
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
    c1.markdown(f"<div class='chip'>{ic} {f['name'][:20]}{'…' if len(f['name'])>20 else ''} <span style='color:#555;font-size:11px;'>{f['size']/1024:.0f}KB</span></div>",unsafe_allow_html=True)
    if c2.button("✕",key=f"rm_{i}"):st.session_state.pending.pop(i);st.rerun()
 dot="status-on" if gs.bl else "status-off"
 st.markdown(f"""<div style='position:absolute;bottom:16px;left:16px;right:16px;'>
  <div class='status-pill {"status-online" if gs.bl else "status-offline"}'><span class='status-dot {dot}'></span>{"Online" if gs.bl else "Offline"}</div>
  <div style='color:#444;font-size:10px;margin-top:6px;font-family:JetBrains Mono,monospace;'>{st.session_state.sid[:20]}</div>
 </div>""",unsafe_allow_html=True)
if st.session_state.page=="api":
 st.markdown("""<div style='padding:2rem 0 1rem;'>
  <h1 style='font-size:2rem;font-weight:700;background:linear-gradient(135deg,#8B5CF6,#EC4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;'>⚡ API Reference</h1>
  <p style='color:#666;font-size:14px;margin-top:8px;'>Chiama Gemini con una semplice GET. Gratis, senza API key.</p>
 </div>""",unsafe_allow_html=True)
 st.markdown(f"""<div class='api-card'>
  <div><span class='api-method api-get'>GET</span><span class='api-url'>/api/ask</span></div>
  <div class='api-desc'>Invia una domanda a Gemini e ricevi la risposta in JSON. Ultra-semplice.</div>
  <div style='margin-top:16px;'>
   <div style='color:#888;font-size:12px;font-weight:600;margin-bottom:8px;'>PARAMETRI</div>
   <div class='api-param'><span class='api-param-name'>q<span class='api-required'>*</span></span><span class='api-param-type'>string</span><span class='api-param-desc'>La domanda da inviare a Gemini</span></div>
   <div class='api-param'><span class='api-param-name'>session_id</span><span class='api-param-type'>string</span><span class='api-param-desc'>ID sessione per mantenere il contesto (opzionale)</span></div>
   <div class='api-param'><span class='api-param-name'>engineer</span><span class='api-param-type'>bool</span><span class='api-param-desc'>Attiva prompt engineering (default: true)</span></div>
   <div class='api-param'><span class='api-param-name'>complete</span><span class='api-param-type'>bool</span><span class='api-param-desc'>Auto-completa liste numeriche (default: true)</span></div>
  </div>
 </div>""",unsafe_allow_html=True)
 tab1,tab2,tab3,tab4=st.tabs(["cURL","Python","JavaScript","Response"])
 with tab1:
  st.code(f'''curl "{BASE_URL}/api/ask?q=Ciao+come+stai"''',language="bash")
  st.code(f'''# Con sessione
curl "{BASE_URL}/api/ask?q=Raccontami+una+storia&session_id=my-session-123"''',language="bash")
  st.code(f'''# Senza prompt engineering
curl "{BASE_URL}/api/ask?q=Ciao&engineer=false"''',language="bash")
 with tab2:
  st.code(f'''import requests

r = requests.get("{BASE_URL}/api/ask", params={{
    "q": "Spiegami la relatività in modo semplice",
    "session_id": "sessione-1"
}})
data = r.json()
print(data["answer"])
print(f"Tempo: {{data['elapsed_ms']}}ms")''',language="python")
  st.code(f'''# Conversazione multi-turno
import requests

session = "chat-" + str(uuid4())
questions = ["Ciao!", "Come ti chiami?", "Raccontami una barzelletta"]

for q in questions:
    r = requests.get("{BASE_URL}/api/ask", params={{
        "q": q,
        "session_id": session
    }})
    print(f"Q: {{q}}")
    print(f"A: {{r.json()['answer']}}")
    print()''',language="python")
 with tab3:
  st.code(f'''const r = await fetch("{BASE_URL}/api/ask?q=" + encodeURIComponent("Ciao!"));
const data = await r.json();
console.log(data.answer);''',language="javascript")
  st.code(f'''// Classe wrapper
class GeminiAPI {{
  constructor(baseUrl = "{BASE_URL}") {{
    this.baseUrl = baseUrl;
    this.sessionId = crypto.randomUUID();
  }}
  async ask(question) {{
    const url = new URL(this.baseUrl + "/api/ask");
    url.searchParams.set("q", question);
    url.searchParams.set("session_id", this.sessionId);
    const r = await fetch(url);
    return await r.json();
  }}
}}

const gemini = new GeminiAPI();
const {{ answer }} = await gemini.ask("Cos'è l'AI?");''',language="javascript")
 with tab4:
  st.code(json.dumps({"status":"success","answer":"Ciao! Come posso aiutarti oggi?","session_id":"abc-123-def","enhancements":[],"elapsed_ms":3420},indent=2,ensure_ascii=False),language="json")
  st.markdown("""<div style='margin-top:16px;'>
   <div style='color:#888;font-size:12px;font-weight:600;margin-bottom:8px;'>CAMPI RISPOSTA</div>
   <div class='api-param'><span class='api-param-name'>status</span><span class='api-param-type'>string</span><span class='api-param-desc'>"success" o "error"</span></div>
   <div class='api-param'><span class='api-param-name'>answer</span><span class='api-param-type'>string</span><span class='api-param-desc'>Risposta di Gemini in markdown</span></div>
   <div class='api-param'><span class='api-param-name'>session_id</span><span class='api-param-type'>string</span><span class='api-param-desc'>ID sessione (riusa per multi-turno)</span></div>
   <div class='api-param'><span class='api-param-name'>enhancements</span><span class='api-param-type'>array</span><span class='api-param-desc'>Tag delle ottimizzazioni applicate</span></div>
   <div class='api-param'><span class='api-param-name'>elapsed_ms</span><span class='api-param-type'>int</span><span class='api-param-desc'>Tempo di risposta in millisecondi</span></div>
  </div>""",unsafe_allow_html=True)
 st.markdown("""<div style='margin-top:32px;'>
  <h3 style='color:#e8e8e8;font-size:18px;font-weight:600;'>📋 Status Codes</h3>
 </div>""",unsafe_allow_html=True)
 cols=st.columns(3)
 cols[0].markdown("""<div class='api-card' style='text-align:center;'>
  <div style='font-size:24px;font-weight:700;color:#34d399;'>200</div>
  <div style='color:#888;font-size:13px;margin-top:4px;'>Risposta OK</div>
 </div>""",unsafe_allow_html=True)
 cols[1].markdown("""<div class='api-card' style='text-align:center;'>
  <div style='font-size:24px;font-weight:700;color:#fbbf24;'>429</div>
  <div style='color:#888;font-size:13px;margin-top:4px;'>Rate Limited</div>
 </div>""",unsafe_allow_html=True)
 cols[2].markdown("""<div class='api-card' style='text-align:center;'>
  <div style='font-size:24px;font-weight:700;color:#f87171;'>500</div>
  <div style='color:#888;font-size:13px;margin-top:4px;'>Server Error</div>
 </div>""",unsafe_allow_html=True)
 st.markdown("""<div style='margin-top:32px;'>
  <h3 style='color:#e8e8e8;font-size:18px;font-weight:600;'>🧪 Playground</h3>
  <p style='color:#666;font-size:14px;'>Testa l'API direttamente qui.</p>
 </div>""",unsafe_allow_html=True)
 pc1,pc2=st.columns([3,1])
 test_q=pc1.text_input("Domanda",value="Ciao, come stai?",label_visibility="collapsed",placeholder="Scrivi una domanda...")
 test_go=pc2.button("▶ Invia",use_container_width=True,type="primary")
 if test_go and test_q:
  with st.spinner("⚡"):
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
    result={"status":"error","error":str(e),"elapsed_ms":int((time.perf_counter()-t0)*1000)}
    st.code(json.dumps(result,indent=2,ensure_ascii=False),language="json")
 st.markdown(f"""<div style='margin-top:40px;padding:20px;background:rgba(139,92,246,0.04);border:1px solid rgba(139,92,246,0.1);border-radius:14px;'>
  <div style='color:#a78bfa;font-weight:600;font-size:14px;'>💡 Note</div>
  <ul style='color:#888;font-size:13px;line-height:2;margin-top:8px;'>
   <li>Nessuna API key richiesta — completamente gratuito</li>
   <li>Rate limit: ~30 richieste/minuto per IP</li>
   <li>Sessioni: durano finché il server è attivo (no persistenza)</li>
   <li>Risposte in italiano di default</li>
   <li>Max ~2500 token per prompt</li>
   <li>Supporta markdown nella risposta</li>
  </ul>
 </div>""",unsafe_allow_html=True)
elif st.session_state.page=="chat":
 if not st.session_state.msg:
  st.markdown("""<div class='hero'>
   <div class='hero-icon'>✨</div>
   <div class='hero-title'>Come posso aiutarti?</div>
   <div class='hero-sub'>Chat, analisi file, coding, ricerche — tutto gratis</div>
  </div>""",unsafe_allow_html=True)
  cols=st.columns(3)
  suggestions=["💡 Spiegami il machine learning","🐍 Scrivi un web scraper Python","📊 Analizza questo CSV"]
  for i,s in enumerate(suggestions):
   if cols[i].button(s,use_container_width=True,key=f"sug_{i}"):
    st.session_state.msg.append({"role":"user","content":s.split(" ",1)[1]})
    st.rerun()
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
     if f["size"]>MAX_TEXT_BYTES:info.warning(f"⚠ {f['name']} troppo grande");continue
     content=read_text(f["bytes"],f["name"])
     text_blocks.append(fmt_file(f["name"],content))
    if text_blocks:
     final_prompt="".join(text_blocks)+"\n\n"+p
     if st.session_state.debug:st.caption(f"📝 {len(text_files)} file inlined ({len(final_prompt)} char)")
    if image_files:
     for idx,f in enumerate(image_files):
      info.markdown(f"<div style='color:#888;font-size:13px;'>⬆ {f['name']} ({idx+1}/{len(image_files)})…</div>",unsafe_allow_html=True)
      try:
       result=cl.upload_image(f["bytes"],f["name"],f["mime"] or"image/jpeg")
       uploaded.append(result)
      except Exception as ue:
       info.error(f"❌ {f['name']}: {ue}");raise
     info.markdown(f"<div style='color:#34d399;font-size:13px;'>✓ {len(uploaded)} immagini</div>",unsafe_allow_html=True)
    ph.markdown("<div style='color:#888;font-size:14px;'>Sto pensando<span style='animation:pulse 1s infinite;'> ✨</span></div>",unsafe_allow_html=True)
    ans,tags=cl.chat(message=final_prompt,state=gs,use_engineer=st.session_state.eng,force_complete=st.session_state.fc,files=uploaded if uploaded else None)
    ms=int((time.perf_counter()-t0)*1000)
    info.empty()
    ph.markdown(ans)
    tags_html="".join(f"<span class='meta-tag'>{t}</span>" for t in tags)
    extra=[]
    if text_blocks:extra.append(f"📝{len(text_blocks)}")
    if uploaded:extra.append(f"🖼{len(uploaded)}")
    ex=" · ".join(extra)
    st.markdown(f"<div class='meta'><span>⏱ {ms}ms</span>{tags_html}{' · '+ex if ex else ''}</div>",unsafe_allow_html=True)
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
