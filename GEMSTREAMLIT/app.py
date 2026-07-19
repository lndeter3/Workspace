import uuid,time,streamlit as st,os,traceback,json,requests
st.set_page_config(page_title="Gemini",page_icon="✨",layout="wide",initial_sidebar_state="expanded")
API_BASE="https://web-production-3d4e4.up.railway.app"
API_TIMEOUT=90
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
.api-delete{background:rgba(239,68,68,0.15);color:#f87171;}
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
.suggest-btn{background:rgba(255,255,255,0.03)!important;border:1px solid rgba(255,255,255,0.06)!important;border-radius:14px!important;padding:16px!important;text-align:left!important;font-size:13px!important;color:#c0c0c0!important;transition:all .2s!important;}
.suggest-btn:hover{background:rgba(139,92,246,0.08)!important;border-color:rgba(139,92,246,0.2)!important;color:#e8e8e8!important;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.08);border-radius:3px;}
</style>
"""
st.markdown(CSS,unsafe_allow_html=True)
@st.cache_data(ttl=30)
def check_api():
 try:
  r=requests.get(f"{API_BASE}/health",timeout=5)
  return r.status_code==200,r.json() if r.status_code==200 else {}
 except:return False,{}
def api_ask(question,session_id="",engineer=True,complete=True):
 try:
  params={"q":question,"engineer":str(engineer).lower(),"complete":str(complete).lower()}
  if session_id:params["session_id"]=session_id
  r=requests.get(f"{API_BASE}/ask",params=params,timeout=API_TIMEOUT)
  data=r.json()
  if r.status_code==200 and data.get("status")=="success":return data
  raise RuntimeError(data.get("error",f"HTTP {r.status_code}"))
 except requests.Timeout:raise RuntimeError(f"Timeout dopo {API_TIMEOUT}s")
 except requests.ConnectionError:raise RuntimeError("API non raggiungibile")
def api_reset(session_id):
 try:requests.post(f"{API_BASE}/session/{session_id}/reset",timeout=5)
 except:pass
def api_delete(session_id):
 try:requests.delete(f"{API_BASE}/session/{session_id}",timeout=5)
 except:pass
def _i():
 for k,v in[("sid",str(uuid.uuid4())),("msg",[]),("eng",True),("fc",True),("page","chat")]:
  if k not in st.session_state:st.session_state[k]=v
_i()
online,health=check_api()
with st.sidebar:
 st.markdown("""<div style='padding:12px 4px 24px;'>
  <div style='font-size:22px;font-weight:700;background:linear-gradient(135deg,#8B5CF6,#EC4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>✨ Gemini</div>
  <div style='color:#555;font-size:11px;margin-top:4px;font-family:JetBrains Mono,monospace;'>v15 · Cloud API</div>
 </div>""",unsafe_allow_html=True)
 c1,c2=st.columns(2)
 if c1.button("💬 Chat",use_container_width=True,type="primary" if st.session_state.page=="chat" else "secondary"):st.session_state.page="chat";st.rerun()
 if c2.button("⚡ API",use_container_width=True,type="primary" if st.session_state.page=="api" else "secondary"):st.session_state.page="api";st.rerun()
 if st.session_state.page=="chat":
  st.markdown("")
  if st.button("＋ Nuova chat",use_container_width=True):
   api_delete(st.session_state.sid)
   st.session_state.sid=str(uuid.uuid4())
   st.session_state.msg=[]
   st.rerun()
  st.markdown("<div class='section-title'>Impostazioni</div>",unsafe_allow_html=True)
  st.session_state.eng=st.toggle("🔧 Prompt Engineer",value=st.session_state.eng)
  st.session_state.fc=st.toggle("📝 Auto-completa",value=st.session_state.fc)
  if st.button("🔄 Reset contesto",use_container_width=True):
   api_reset(st.session_state.sid)
   st.toast("Contesto resettato")
 dot="status-on" if online else "status-off"
 sess_count=health.get("sessions",0) if online else 0
 st.markdown(f"""<div style='position:absolute;bottom:16px;left:16px;right:16px;'>
  <div class='status-pill {"status-online" if online else "status-offline"}'><span class='status-dot {dot}'></span>{"API Online" if online else "API Offline"}</div>
  <div style='color:#555;font-size:10px;margin-top:6px;font-family:JetBrains Mono,monospace;'>
   {sess_count} sessioni attive<br>
   {st.session_state.sid[:20]}
  </div>
 </div>""",unsafe_allow_html=True)
if st.session_state.page=="api":
 st.markdown(f"""<div style='padding:2rem 0 1rem;'>
  <div class='status-pill {"status-online" if online else "status-offline"}' style='margin-bottom:16px;'><span class='status-dot {"status-on" if online else "status-off"}'></span>{"ONLINE" if online else "OFFLINE"}</div>
  <h1 style='font-size:2.2rem;font-weight:700;background:linear-gradient(135deg,#8B5CF6,#EC4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;'>⚡ API Reference</h1>
  <p style='color:#666;font-size:14px;margin-top:8px;'>Free · No auth · No API key · Powered by Railway</p>
  <div style='margin-top:12px;padding:12px 16px;background:rgba(139,92,246,0.05);border:1px solid rgba(139,92,246,0.15);border-radius:10px;font-family:JetBrains Mono,monospace;font-size:13px;color:#c4b5fd;'>{API_BASE}</div>
 </div>""",unsafe_allow_html=True)
 st.markdown(f"""<div class='api-card'>
  <div><span class='api-method api-get'>GET</span><span class='api-url'>/ask</span></div>
  <div class='api-desc'>Chiedi qualsiasi cosa a Gemini. Ritorna JSON con la risposta.</div>
  <div style='margin-top:20px;'>
   <div style='color:#888;font-size:12px;font-weight:600;margin-bottom:8px;'>QUERY PARAMS</div>
   <div class='api-param'><span class='api-param-name'>q<span class='api-required'>*</span></span><span class='api-param-type'>string</span><span class='api-param-desc'>Domanda per Gemini (URL-encoded)</span></div>
   <div class='api-param'><span class='api-param-name'>session_id</span><span class='api-param-type'>string</span><span class='api-param-desc'>ID sessione per mantenere il contesto</span></div>
   <div class='api-param'><span class='api-param-name'>engineer</span><span class='api-param-type'>bool</span><span class='api-param-desc'>Prompt engineering (default: true)</span></div>
   <div class='api-param'><span class='api-param-name'>complete</span><span class='api-param-type'>bool</span><span class='api-param-desc'>Auto-completa liste (default: true)</span></div>
  </div>
 </div>""",unsafe_allow_html=True)
 st.markdown(f"""<div class='api-card'>
  <div><span class='api-method api-get'>GET</span><span class='api-url'>/health</span></div>
  <div class='api-desc'>Status server e conteggio sessioni attive</div>
 </div>
 <div class='api-card'>
  <div><span class='api-method api-get'>GET</span><span class='api-url'>/sessions</span></div>
  <div class='api-desc'>Lista sessioni attive (max 50)</div>
 </div>
 <div class='api-card'>
  <div><span class='api-method api-delete'>DELETE</span><span class='api-url'>/session/{{sid}}</span></div>
  <div class='api-desc'>Cancella una sessione</div>
 </div>""",unsafe_allow_html=True)
 tab1,tab2,tab3,tab4=st.tabs(["🐍 Python","🌐 JavaScript","🔧 cURL","📦 Response"])
 with tab1:
  st.code(f'''import requests

API = "{API_BASE}"

# Semplice
r = requests.get(f"{{API}}/ask", params={{"q": "Ciao come stai?"}})
data = r.json()
print(data["answer"])
print(f"Tempo: {{data['elapsed_ms']}}ms")

# Multi-turno con session_id
sid = data["session_id"]
r2 = requests.get(f"{{API}}/ask", params={{
    "q": "Cosa mi hai detto prima?",
    "session_id": sid
}})
print(r2.json()["answer"])''',language="python")
  st.code(f'''# Classe wrapper con context management
import requests
from uuid import uuid4

class Gemini:
    def __init__(self, api="{API_BASE}"):
        self.api = api
        self.sid = str(uuid4())
    
    def ask(self, question, **kwargs):
        r = requests.get(f"{{self.api}}/ask", params={{
            "q": question, "session_id": self.sid, **kwargs
        }}, timeout=90)
        return r.json()
    
    def reset(self):
        requests.post(f"{{self.api}}/session/{{self.sid}}/reset")
    
    def clear(self):
        requests.delete(f"{{self.api}}/session/{{self.sid}}")
        self.sid = str(uuid4())

# Uso
gem = Gemini()
print(gem.ask("Ciao!")["answer"])
print(gem.ask("Come mi chiamo?")["answer"])''',language="python")
 with tab2:
  st.code(f'''const API = "{API_BASE}";

// Chiamata base
const r = await fetch(`${{API}}/ask?q=${{encodeURIComponent("Ciao!")}}`);
const data = await r.json();
console.log(data.answer);''',language="javascript")
  st.code(f'''// Classe wrapper
class Gemini {{
  constructor(api = "{API_BASE}") {{
    this.api = api;
    this.sid = crypto.randomUUID();
  }}
  
  async ask(question, opts = {{}}) {{
    const url = new URL(this.api + "/ask");
    url.searchParams.set("q", question);
    url.searchParams.set("session_id", this.sid);
    Object.entries(opts).forEach(([k,v]) => url.searchParams.set(k, v));
    const r = await fetch(url);
    return await r.json();
  }}
  
  async reset() {{
    await fetch(`${{this.api}}/session/${{this.sid}}/reset`, {{method:"POST"}});
  }}
}}

const gem = new Gemini();
const {{answer}} = await gem.ask("Cos'è il quantum computing?");
console.log(answer);''',language="javascript")
 with tab3:
  st.code(f'''# Base
curl "{API_BASE}/ask?q=Ciao+come+stai"

# Con jq per estrarre solo la risposta
curl -s "{API_BASE}/ask?q=Ciao" | jq -r '.answer'

# Multi-turno
SID="my-session-123"
curl "{API_BASE}/ask?q=Ciao&session_id=$SID"
curl "{API_BASE}/ask?q=Come+mi+chiamo?&session_id=$SID"

# Health check
curl "{API_BASE}/health"

# Cancella sessione
curl -X DELETE "{API_BASE}/session/$SID"''',language="bash")
 with tab4:
  st.code(json.dumps({"status":"success","answer":"Ciao! Sto benissimo, grazie...","session_id":"abc-123-def","enhancements":[],"elapsed_ms":3420},indent=2,ensure_ascii=False),language="json")
  st.markdown("""<div style='margin-top:16px;'>
   <div class='api-param'><span class='api-param-name'>status</span><span class='api-param-type'>str</span><span class='api-param-desc'>"success" o "error"</span></div>
   <div class='api-param'><span class='api-param-name'>answer</span><span class='api-param-type'>str</span><span class='api-param-desc'>Risposta Gemini (markdown)</span></div>
   <div class='api-param'><span class='api-param-name'>session_id</span><span class='api-param-type'>str</span><span class='api-param-desc'>ID sessione (riusa)</span></div>
   <div class='api-param'><span class='api-param-name'>enhancements</span><span class='api-param-type'>list</span><span class='api-param-desc'>Tag ottimizzazioni</span></div>
   <div class='api-param'><span class='api-param-name'>elapsed_ms</span><span class='api-param-type'>int</span><span class='api-param-desc'>Tempo di risposta</span></div>
  </div>""",unsafe_allow_html=True)
 st.markdown("<h3 style='color:#e8e8e8;font-size:18px;font-weight:600;margin-top:32px;'>🧪 Live Playground</h3>",unsafe_allow_html=True)
 pc1,pc2=st.columns([3,1])
 test_q=pc1.text_input("Domanda",value="Dimmi una curiosità sui polpi",label_visibility="collapsed",placeholder="Scrivi una domanda...")
 test_go=pc2.button("▶ Prova",use_container_width=True,type="primary")
 if test_go and test_q:
  st.markdown(f"<div style='color:#666;font-size:12px;margin:8px 0;font-family:JetBrains Mono,monospace;'>GET {API_BASE}/ask?q={test_q[:60].replace(' ','+')}</div>",unsafe_allow_html=True)
  with st.spinner("⚡ Chiamata all'API..."):
   try:
    data=api_ask(test_q,engineer=True,complete=False)
    st.code(json.dumps(data,indent=2,ensure_ascii=False),language="json")
   except Exception as e:
    st.code(json.dumps({"status":"error","error":str(e)},indent=2),language="json")
 st.markdown(f"""<div style='margin-top:32px;padding:20px;background:rgba(139,92,246,0.04);border:1px solid rgba(139,92,246,0.1);border-radius:14px;'>
  <div style='color:#a78bfa;font-weight:600;font-size:14px;'>💡 Note</div>
  <ul style='color:#888;font-size:13px;line-height:2;margin-top:8px;padding-left:20px;'>
   <li>API pubblica gratuita — no rate limit noto</li>
   <li>Sessioni in RAM · auto-cleanup dopo 2h</li>
   <li>Risposte in italiano di default</li>
   <li>Max ~2500 token per prompt</li>
   <li>Test browser: <a href="{API_BASE}/ask?q=Ciao" target="_blank" style='color:#a78bfa;'>{API_BASE}/ask?q=Ciao</a></li>
  </ul>
 </div>""",unsafe_allow_html=True)
elif st.session_state.page=="chat":
 if not online:
  st.error(f"⚠ API offline: {API_BASE}")
  st.info("L'API su Railway non risponde. Controlla lo status del deploy.")
  st.stop()
 if not st.session_state.msg:
  st.markdown("""<div class='hero'>
   <div class='hero-icon'>✨</div>
   <div class='hero-title'>Come posso aiutarti?</div>
   <div class='hero-sub'>Chat, coding, ricerche, idee — tutto gratis</div>
  </div>""",unsafe_allow_html=True)
  cols=st.columns(3)
  suggestions=[("💡","Spiegami il machine learning in modo semplice"),("🐍","Scrivi un web scraper Python"),("📊","Dammi 20 idee per un progetto AI")]
  for i,(ic,txt) in enumerate(suggestions):
   if cols[i].button(f"{ic}  {txt}",use_container_width=True,key=f"sug_{i}"):
    st.session_state._pending_msg=txt
    st.rerun()
 for m in st.session_state.msg:
  with st.chat_message(m["role"],avatar="👤" if m["role"]=="user" else "✨"):
   st.markdown(m["content"])
   if m.get("ms"):
    tags_html="".join(f"<span class='meta-tag'>{t}</span>" for t in(m.get("tags") or[]))
    st.markdown(f"<div class='meta'><span>⏱ {m['ms']}ms</span>{tags_html}</div>",unsafe_allow_html=True)
 pending=st.session_state.pop("_pending_msg",None)
 p=pending or st.chat_input("Scrivi a Gemini...")
 if p:
  st.session_state.msg.append({"role":"user","content":p})
  with st.chat_message("user",avatar="👤"):st.markdown(p)
  with st.chat_message("assistant",avatar="✨"):
   ph=st.empty()
   ph.markdown("<div style='color:#888;font-size:14px;'>Sto pensando ✨</div>",unsafe_allow_html=True)
   t0=time.perf_counter()
   try:
    data=api_ask(p,session_id=st.session_state.sid,engineer=st.session_state.eng,complete=st.session_state.fc)
    ans=data["answer"]
    tags=data.get("enhancements",[])
    ms=data.get("elapsed_ms",int((time.perf_counter()-t0)*1000))
    if data.get("session_id"):st.session_state.sid=data["session_id"]
    ph.markdown(ans)
    tags_html="".join(f"<span class='meta-tag'>{t}</span>" for t in tags)
    st.markdown(f"<div class='meta'><span>⏱ {ms}ms</span>{tags_html}</div>",unsafe_allow_html=True)
    st.session_state.msg.append({"role":"assistant","content":ans,"ms":ms,"tags":tags})
   except RuntimeError as e:ph.error(f"⚠ {e}")
   except Exception as e:ph.error(f"⚠ {type(e).__name__}: {e}")
 if pending:st.rerun()
