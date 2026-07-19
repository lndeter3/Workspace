import uuid,time,json,os,requests,streamlit as st
import streamlit.components.v1 as components

API_BASE="https://web-production-3d4e4.up.railway.app"
API_TIMEOUT=(5,180)
UPLOAD_TIMEOUT=(5,60)
MAX_IMG_BYTES=262144
IMG_EXT={"png","jpg","jpeg","webp","gif","bmp"}
TEXT_EXT={"txt","md","csv","json","py","js","ts","html","css","xml","yaml","yml","sh","sql","c","cpp","h","java","kt","go","rs","rb","php","toml","ini","log","env"}
LANG_MAP={"py":"python","js":"javascript","ts":"typescript","sh":"bash","cpp":"cpp","c":"c","java":"java","go":"go","rs":"rust","rb":"ruby","php":"php","sql":"sql","html":"html","css":"css","json":"json","yaml":"yaml","yml":"yaml","toml":"toml","xml":"xml","md":"markdown"}
MAX_TEXT_BYTES=500000
MAX_TEXT_LINES=5000

st.set_page_config(page_title="Gemini",layout="wide",initial_sidebar_state="collapsed",menu_items=None)

st.markdown("""
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#0b0b0b">
<style>
#MainMenu,footer,header,.stDeployButton,[data-testid="stToolbar"]{display:none!important;}
*{-webkit-tap-highlight-color:transparent;}
html,body,.stApp{background:#0b0b0b!important;color:#eaeaea;overscroll-behavior:none;}
.block-container{max-width:900px;padding:0.5rem 0.8rem 9rem;}
section[data-testid="stSidebar"]{background:#0f0f0f;border-right:1px solid #222;width:300px!important;min-width:280px!important;}
section[data-testid="stSidebar"] .stButton>button{background:#151515;border:1px solid #222;color:#eaeaea;border-radius:10px;font-weight:500;font-size:14px;}
section[data-testid="stSidebar"] .stButton>button:hover{background:#1a1a1a;border-color:#333;}
.stChatInput{border-radius:22px!important;border:1px solid #222!important;background:#101010!important;}
.stChatInput textarea{font-size:16px!important;color:#eaeaea!important;}
[data-testid="stChatMessage"]{padding:10px 0!important;}
[data-testid="stChatMessage"] p{font-size:15px;line-height:1.6;}
.stMarkdown pre{background:#0f0f0f!important;border:1px solid #222;border-radius:10px;padding:10px;font-size:12px;overflow-x:auto;-webkit-overflow-scrolling:touch;}
.stMarkdown code{background:#131313;padding:2px 6px;border-radius:6px;color:#c9c9ff;font-size:13px;}
.stMarkdown a{color:#9aa6ff;}
small,.stCaption{color:#777!important;font-size:11px!important;}
[data-testid="stFileUploader"]{background:#101010;border:1px dashed #2a2a2a;border-radius:10px;padding:6px;}
[data-testid="stFileUploader"] button{background:#151515!important;color:#ccc!important;border:1px solid #2a2a2a!important;border-radius:8px!important;font-size:13px!important;}
.chip{display:inline-flex;align-items:center;gap:6px;background:#151515;border:1px solid #222;border-radius:8px;padding:4px 10px;margin:2px;font-size:11px;color:#ccc;}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px;}
.on{background:#10a37f;box-shadow:0 0 6px #10a37f;}
.off{background:#ef4444;}
.stTabs [data-baseweb="tab-list"]{gap:0;background:#101010;border-radius:10px;padding:3px;overflow-x:auto;}
.stTabs [data-baseweb="tab"]{border-radius:8px;color:#888;padding:6px 14px;font-size:13px;white-space:nowrap;}
.stTabs [aria-selected="true"]{background:#1a1a1a!important;color:#eaeaea!important;}
@media (max-width:768px){
 .block-container{padding-top:0.5rem!important;padding-bottom:10rem!important;}
 section[data-testid="stSidebar"]{width:85vw!important;}
 [data-testid="stSidebarCollapsedControl"]{top:12px!important;left:12px!important;background:#151515!important;border:1px solid #222!important;border-radius:8px!important;padding:6px!important;}
 .stChatFloatingInputContainer{padding-bottom:0.5rem!important;}
 [data-testid="stChatMessage"] p{font-size:14px;}
 .stMarkdown pre{font-size:11px;padding:8px;}
 h1{font-size:1.6rem!important;}
 h2{font-size:1.3rem!important;}
}
::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-thumb{background:#333;border-radius:2px;}
input,textarea{font-size:16px!important;}
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

def voice_master(auto_tts=False):
 return """
<style>
 #vmaster{position:fixed;bottom:0;left:0;right:0;background:linear-gradient(180deg,transparent,#0b0b0b 30%);padding:8px;z-index:99999;pointer-events:none;}
 #vmwrap{max-width:900px;margin:0 auto;display:flex;justify-content:flex-end;gap:8px;pointer-events:auto;padding-right:8px;}
 .vbtn{background:#151515;border:1px solid #2a2a2a;color:#eaeaea;padding:10px 16px;border-radius:20px;font-size:13px;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:6px;user-select:none;-webkit-user-select:none;touch-action:manipulation;transition:all 0.15s;min-height:40px;}
 .vbtn:hover{background:#1e1e1e;border-color:#3a3a3a;}
 .vbtn:active{transform:scale(0.94);}
 .vbtn.rec{background:#5a1a1a;border-color:#a03030;color:#ffdddd;animation:vpulse 0.8s infinite;}
 .vbtn.speak{background:#1a3a5a;border-color:#3080a0;color:#ddeeff;}
 @keyframes vpulse{0%,100%{box-shadow:0 0 0 0 rgba(255,80,80,0.5);}50%{box-shadow:0 0 0 12px rgba(255,80,80,0);}}
 #vind{position:fixed;top:12px;left:50%;transform:translateX(-50%);background:#5a1a1a;color:#fff;padding:8px 20px;border-radius:20px;font-size:13px;z-index:100000;display:none;animation:vpulse 0.8s infinite;pointer-events:none;}
 #vind.on{display:block;}
 #vlog{position:fixed;top:52px;left:50%;transform:translateX(-50%);background:rgba(20,20,20,0.95);color:#eaeaea;padding:10px 16px;border-radius:12px;font-size:13px;z-index:100000;display:none;max-width:80vw;text-align:center;border:1px solid #333;pointer-events:none;}
 #vlog.on{display:block;}
</style>
<div id="vind">Listening...</div>
<div id="vlog"></div>
<div id="vmaster">
 <div id="vmwrap">
  <button id="vspk" class="vbtn" style="display:none;" title="Stop reading">Stop</button>
  <button id="vmic" class="vbtn" title="Tap or long-press send arrow to record">Voice</button>
 </div>
</div>

<script>
(function(){
 if(window.__vmaster_init)return;window.__vmaster_init=true;
 const AUTO_TTS=""" + ("true" if auto_tts else "false") + """;
 const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
 const SS=window.speechSynthesis;
 const mic=document.getElementById('vmic');
 const spk=document.getElementById('vspk');
 const ind=document.getElementById('vind');
 const log=document.getElementById('vlog');
 let rec=null,recording=false,accText="",currentUtter=null,speaking=false;
 let bestVoices={it:null,en:null};

 function pickVoice(lang){
  const voices=SS.getVoices();
  if(!voices||!voices.length)return null;
  const l=lang.toLowerCase().split('-')[0];
  const premium=['neural','natural','wavenet','enhanced','premium','online','siri','samantha','alex','karen','moira','tessa','fiona','daniel','martha','arthur','luca','alice','federica','paola','elsa','luciana'];
  const scored=voices.filter(v=>v.lang.toLowerCase().startsWith(l)).map(v=>{
   let s=0;
   const n=v.name.toLowerCase();
   premium.forEach(k=>{if(n.includes(k))s+=10;});
   if(v.localService===false)s+=5;
   if(n.includes('google'))s+=8;
   if(n.includes('microsoft')&&n.includes('online'))s+=9;
   return {v,s};
  }).sort((a,b)=>b.s-a.s);
  return scored.length?scored[0].v:voices[0];
 }
 function loadVoices(){
  bestVoices.it=pickVoice('it-IT')||pickVoice('it');
  bestVoices.en=pickVoice('en-US')||pickVoice('en-GB')||pickVoice('en');
 }
 if(SS){
  loadVoices();
  SS.onvoiceschanged=loadVoices;
 }

 function detectLang(text){
  const t=text.slice(0,200).toLowerCase();
  const itWords=[' e ',' il ',' la ',' che ',' di ',' un ',' una ',' per ',' con ',' non ',' sono ',' ho ',' hai ',' è ',' più ',' molto ',' quando ',' come ',' cosa '];
  let itScore=0;
  itWords.forEach(w=>{if(t.includes(w))itScore++;});
  return itScore>=2?'it':'en';
 }

 function stopSpeak(){
  if(SS){try{SS.cancel();}catch(e){}}
  speaking=false;currentUtter=null;
  spk.style.display='none';
 }
 function speak(text){
  if(!SS||!text)return;
  stopSpeak();
  const clean=text.replace(/```[\\s\\S]*?```/g,'').replace(/`[^`]+`/g,'').replace(/\\*\\*/g,'').replace(/[*_#>~|]/g,'').replace(/https?:\\/\\/\\S+/g,'').replace(/\\[([^\\]]+)\\]\\([^\\)]+\\)/g,'$1').replace(/\\s+/g,' ').trim();
  if(!clean)return;
  const chunks=[];
  const sentences=clean.match(/[^.!?]+[.!?]+|[^.!?]+$/g)||[clean];
  let buf='';
  for(const s of sentences){
   if((buf+s).length>200){if(buf)chunks.push(buf.trim());buf=s;}
   else buf+=' '+s;
  }
  if(buf.trim())chunks.push(buf.trim());
  const lang=detectLang(clean);
  const voice=bestVoices[lang]||bestVoices.it||bestVoices.en;
  speaking=true;spk.style.display='inline-flex';
  let idx=0;
  function speakNext(){
   if(!speaking||idx>=chunks.length){stopSpeak();return;}
   const u=new SpeechSynthesisUtterance(chunks[idx]);
   if(voice)u.voice=voice;
   u.lang=voice?voice.lang:(lang==='it'?'it-IT':'en-US');
   u.rate=1.02;
   u.pitch=1.0;
   u.volume=1.0;
   u.onend=()=>{idx++;speakNext();};
   u.onerror=()=>{idx++;speakNext();};
   currentUtter=u;
   SS.speak(u);
  }
  speakNext();
 }
 spk.onclick=stopSpeak;

 window.__gemini_speak=speak;
 window.__gemini_stop_speak=stopSpeak;

 function findChatInput(){
  const doc=window.parent?window.parent.document:document;
  const areas=doc.querySelectorAll('textarea');
  return areas[areas.length-1]||null;
 }
 function findSendBtn(){
  const doc=window.parent?window.parent.document:document;
  const btns=doc.querySelectorAll('[data-testid="stChatInputSendButton"], button[kind="header"], button[aria-label*="end"], .stChatInput button');
  return btns[btns.length-1]||null;
 }
 function setInputValue(txt){
  const el=findChatInput();
  if(!el)return false;
  const setter=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
  setter.call(el,txt);
  el.dispatchEvent(new Event('input',{bubbles:true}));
  return true;
 }
 function getInputValue(){
  const el=findChatInput();
  return el?el.value:'';
 }

 function startRec(){
  if(!SR){log.textContent='Voice not supported';log.classList.add('on');setTimeout(()=>log.classList.remove('on'),2000);return;}
  stopSpeak();
  if(recording)return;
  try{
   rec=new SR();
   rec.lang=navigator.language||'it-IT';
   rec.continuous=true;
   rec.interimResults=true;
   accText=getInputValue();
   if(accText&&!accText.endsWith(' '))accText+=' ';
   rec.onstart=()=>{
    recording=true;
    mic.classList.add('rec');
    mic.textContent='Stop';
    ind.classList.add('on');
   };
   rec.onresult=(e)=>{
    let interim='',final='';
    for(let i=e.resultIndex;i<e.results.length;i++){
     const t=e.results[i][0].transcript;
     if(e.results[i].isFinal)final+=t;
     else interim+=t;
    }
    if(final)accText+=final+' ';
    setInputValue((accText+interim).trim());
    if(interim){log.textContent=interim.slice(-60);log.classList.add('on');}
   };
   rec.onerror=(e)=>{
    log.textContent='Error: '+e.error;
    log.classList.add('on');
    setTimeout(()=>log.classList.remove('on'),1500);
    stopRec();
   };
   rec.onend=()=>{if(recording)stopRec();};
   rec.start();
  }catch(err){log.textContent='Mic error';log.classList.add('on');setTimeout(()=>log.classList.remove('on'),1500);}
 }
 function stopRec(){
  if(rec){try{rec.stop();}catch(e){}rec=null;}
  recording=false;
  mic.classList.remove('rec');
  mic.textContent='Voice';
  ind.classList.remove('on');
  setTimeout(()=>log.classList.remove('on'),800);
 }
 function toggleRec(){recording?stopRec():startRec();}
 mic.onclick=toggleRec;

 window.__gemini_rec_toggle=toggleRec;
 window.__gemini_rec_start=startRec;
 window.__gemini_rec_stop=stopRec;

 let pressTimer=null,longPressed=false;
 function bindSendLongPress(){
  const doc=window.parent?window.parent.document:document;
  const btn=findSendBtn();
  if(!btn||btn.__gemini_bound)return;
  btn.__gemini_bound=true;
  const start=(e)=>{
   longPressed=false;
   pressTimer=setTimeout(()=>{
    longPressed=true;
    if(navigator.vibrate)navigator.vibrate(30);
    toggleRec();
   },450);
  };
  const cancel=()=>{if(pressTimer){clearTimeout(pressTimer);pressTimer=null;}};
  const click=(e)=>{
   if(longPressed){e.preventDefault();e.stopPropagation();longPressed=false;}
  };
  btn.addEventListener('mousedown',start);
  btn.addEventListener('touchstart',start,{passive:true});
  btn.addEventListener('mouseup',cancel);
  btn.addEventListener('mouseleave',cancel);
  btn.addEventListener('touchend',cancel);
  btn.addEventListener('touchcancel',cancel);
  btn.addEventListener('click',click,true);
 }
 setInterval(bindSendLongPress,600);

 if('mediaSession' in navigator){
  try{navigator.mediaSession.setActionHandler('play',()=>{});}catch(e){}
 }

 window.addEventListener('beforeunload',()=>{stopSpeak();stopRec();});
})();
</script>
"""

def tts_message(text,auto=False,key=""):
 safe=json.dumps(text)
 return f"""
<div style="margin-top:4px;">
 <button id="pl_{key}" class="tb">Play</button>
 <button id="stp_{key}" class="tb" style="display:none;">Stop</button>
</div>
<style>
.tb{{background:#151515;border:1px solid #222;color:#aaa;padding:4px 12px;border-radius:6px;font-size:11px;cursor:pointer;font-family:inherit;margin-right:4px;min-height:26px;}}
.tb:hover{{background:#1a1a1a;color:#eaeaea;}}
.tb:active{{transform:scale(0.96);}}
</style>
<script>
(function(){{
 const txt={safe};
 const pl=document.getElementById('pl_{key}');
 const stp=document.getElementById('stp_{key}');
 function play(){{
  const fn=window.parent&&window.parent.__gemini_speak;
  if(fn){{fn(txt);pl.style.display='none';stp.style.display='inline-block';}}
  else{{const fn2=window.__gemini_speak;if(fn2){{fn2(txt);pl.style.display='none';stp.style.display='inline-block';}}}}
 }}
 function stop(){{
  const fn=window.parent&&window.parent.__gemini_stop_speak;
  if(fn)fn();else if(window.__gemini_stop_speak)window.__gemini_stop_speak();
  pl.style.display='inline-block';stp.style.display='none';
 }}
 pl.onclick=play;stp.onclick=stop;
 {"setTimeout(play,300);" if auto else ""}
}})();
</script>
"""

if "sid" not in st.session_state:st.session_state.sid=str(uuid.uuid4())
if "msgs" not in st.session_state:st.session_state.msgs=[]
if "engineer" not in st.session_state:st.session_state.engineer=True
if "complete" not in st.session_state:st.session_state.complete=True
if "stream" not in st.session_state:st.session_state.stream=True
if "pending" not in st.session_state:st.session_state.pending=[]
if "upkey" not in st.session_state:st.session_state.upkey=0
if "page" not in st.session_state:st.session_state.page="chat"
if "auto_tts" not in st.session_state:st.session_state.auto_tts=False
if "show_uploader" not in st.session_state:st.session_state.show_uploader=False

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
  st.markdown("**Options**")
  st.session_state.engineer=st.toggle("Prompt engineer",value=st.session_state.engineer)
  st.session_state.complete=st.toggle("Auto complete",value=st.session_state.complete)
  st.session_state.stream=st.toggle("Stream (SSE)",value=st.session_state.stream)
  st.session_state.auto_tts=st.toggle("Auto TTS",value=st.session_state.auto_tts,help="Auto-read replies")
  st.caption("Tap 'Voice' button or long-press send arrow to record")
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
  st.code(f'''import requests
API="{API_BASE}"
with requests.get(f"{{API}}/ask/stream",params={{"q":"Storia","session_id":"my-1"}},stream=True,timeout=(5,180)) as r:
    for line in r.iter_lines(decode_unicode=True):
        if line:print(line)''',language="python")
  st.code(f'''import requests
API="{API_BASE}"
sid="my-1"
with open("photo.jpg","rb") as f:
    requests.post(f"{{API}}/upload",files={{"file":("photo.jpg",f,"image/jpeg")}},data={{"session_id":sid}})
q=requests.get(f"{{API}}/ask",params={{"q":"Descrivi","session_id":sid}})
print(q.json()["answer"])''',language="python")
 with tab2:
  st.code(f'''const API="{API_BASE}";
const r=await fetch(`${{API}}/ask?q=${{encodeURIComponent("Ciao")}}&session_id=my-1`);
console.log((await r.json()).answer);''',language="javascript")
  st.code(f'''const API="{API_BASE}";
const es=new EventSource(`${{API}}/ask/stream?q=${{encodeURIComponent("Storia")}}&session_id=my-1`);
let text="";
es.addEventListener("chunk",e=>{{text+=e.data;console.log(text);}});
es.addEventListener("done",e=>es.close());''',language="javascript")
 with tab3:
  st.code(f'''curl "{API_BASE}/ask?q=Ciao&session_id=my-1"
curl -N "{API_BASE}/ask/stream?q=Storia&session_id=my-1"
curl -F "file=@photo.jpg" -F "session_id=my-1" "{API_BASE}/upload"''',language="bash")
 with tab4:
  st.markdown("""
| Method | Path | Description |
|---|---|---|
| GET | `/ask` | JSON response |
| GET | `/ask/stream` | SSE streaming |
| POST | `/upload` | Upload image (multipart) |
| DELETE | `/uploads/{sid}` | Clear pending uploads |
| GET | `/health` | Server status |
| DELETE | `/session/{sid}` | Delete session |
""")
else:
 if not ok:
  st.error(f"API offline: {API_BASE}")
  st.stop()
 if not st.session_state.msgs:
  st.markdown("### Gemini")
  st.caption("Message, attach files, or use voice.")

 for i,m in enumerate(st.session_state.msgs):
  with st.chat_message(m["role"]):
   if m.get("files"):
    chips="".join(f"<span class='chip'>[{('IMG' if fi['kind']=='image' else 'TXT' if fi['kind']=='text' else 'BIN')}] {fi['name']}</span>" for fi in m["files"])
    st.markdown(chips,unsafe_allow_html=True)
   st.markdown(m["content"])
   if m.get("meta"):st.caption(m["meta"])
   if m["role"]=="assistant" and m.get("content"):
    components.html(tts_message(m["content"],auto=False,key=f"m{i}"),height=40)

 c1,c2=st.columns([1,10])
 with c1:
  if st.button("+",use_container_width=True,help="Attach files"):
   st.session_state.show_uploader=not st.session_state.show_uploader
   st.rerun()
 with c2:
  if st.session_state.pending:
   chips="".join(f"<span class='chip'>[{('IMG' if f['kind']=='image' else 'TXT' if f['kind']=='text' else 'BIN')}] {f['name'][:20]}{'...' if len(f['name'])>20 else ''}</span>" for f in st.session_state.pending)
   st.markdown(chips,unsafe_allow_html=True)

 if st.session_state.show_uploader:
  up=st.file_uploader("Attach files",type=list(IMG_EXT|TEXT_EXT),accept_multiple_files=True,key=f"up_{st.session_state.upkey}",label_visibility="collapsed")
  if up:
   existing={(x["name"],x["size"]) for x in st.session_state.pending}
   for f in up:
    if (f.name,f.size) in existing:continue
    ext=os.path.splitext(f.name)[1].lower().lstrip(".")
    kind="image" if ext in IMG_EXT else "text" if ext in TEXT_EXT else "binary"
    st.session_state.pending.append({"name":f.name,"size":f.size,"bytes":f.getvalue(),"mime":f.type or "","kind":kind,"ext":ext})
   st.session_state.show_uploader=False
   st.rerun()
  if st.session_state.pending:
   cc1,cc2=st.columns([1,1])
   if cc1.button("Done",use_container_width=True):
    st.session_state.show_uploader=False;st.rerun()
   if cc2.button("Clear all",use_container_width=True):
    st.session_state.pending=[];st.session_state.upkey+=1;st.session_state.show_uploader=False;st.rerun()

 q=st.chat_input("Message Gemini...")

 components.html(voice_master(auto_tts=st.session_state.auto_tts),height=80)

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

   final_ans=""
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
     api_upload_image(f["bytes"],f["name"],mime,st.session_state.sid)
     uploaded_count+=1

    if uploaded_count:info.markdown(f"<small>{uploaded_count} image(s) uploaded</small>",unsafe_allow_html=True)
    else:info.empty()

    box.markdown("_thinking..._")

    if st.session_state.stream:
     acc="";tags=[];files_sent=0;cap=""
     for ev,dat in api_ask_sse(final_q,st.session_state.sid,st.session_state.engineer,st.session_state.complete):
      if ev=="meta":
       try:
        mm=json.loads(dat)
        tags=mm.get("enhancements",[])
        files_sent=mm.get("files_sent",0)
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
       except:
        cap=f"{int((time.perf_counter()-t0)*1000)} ms"
        meta.caption(cap)
      elif ev=="error":
       try:box.error(json.loads(dat).get("error","error"))
       except:box.error(dat)
       acc=""
       break
     final_ans=acc
     if final_ans:st.session_state.msgs.append({"role":"assistant","content":final_ans,"meta":cap})
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
     final_ans=ans
     st.session_state.msgs.append({"role":"assistant","content":ans,"meta":cap})

    if final_ans:
     components.html(tts_message(final_ans,auto=st.session_state.auto_tts,key=f"live_{len(st.session_state.msgs)}"),height=40)

    st.session_state.pending=[]
    st.session_state.upkey+=1

   except Exception as e:
    info.empty()
    box.error(str(e))
    api_clear_uploads(st.session_state.sid)
