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
[data-testid="stChatInput"],[data-testid="stChatFloatingInputContainer"],.stChatFloatingInputContainer{display:none!important;}
*{-webkit-tap-highlight-color:transparent;box-sizing:border-box;}
html,body,.stApp{background:#0b0b0b!important;color:#eaeaea;overscroll-behavior:none;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;}
.block-container{max-width:820px;padding:1rem 1rem 12rem;}
section[data-testid="stSidebar"]{background:#0f0f0f;border-right:1px solid #1e1e1e;width:280px!important;}
section[data-testid="stSidebar"] .stButton>button{background:#151515;border:1px solid #222;color:#eaeaea;border-radius:10px;font-weight:500;font-size:14px;}
section[data-testid="stSidebar"] .stButton>button:hover{background:#1a1a1a;border-color:#333;}
[data-testid="stChatMessage"]{padding:14px 0!important;background:transparent!important;border:none!important;}
[data-testid="stChatMessage"] p{font-size:15px;line-height:1.65;color:#eaeaea;}
.stMarkdown pre{background:#0f0f0f!important;border:1px solid #1e1e1e;border-radius:12px;padding:12px;font-size:12.5px;overflow-x:auto;-webkit-overflow-scrolling:touch;}
.stMarkdown code{background:#161616;padding:2px 7px;border-radius:6px;color:#c9c9ff;font-size:13px;}
.stMarkdown a{color:#9aa6ff;}
small,.stCaption{color:#666!important;font-size:11px!important;}
.chip{display:inline-flex;align-items:center;gap:6px;background:#161616;border:1px solid #242424;border-radius:8px;padding:4px 10px;margin:2px;font-size:11px;color:#bbb;}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px;}
.on{background:#10a37f;box-shadow:0 0 6px #10a37f;}
.off{background:#ef4444;}
.stTabs [data-baseweb="tab-list"]{gap:0;background:#101010;border-radius:10px;padding:3px;}
.stTabs [data-baseweb="tab"]{border-radius:8px;color:#888;padding:6px 14px;font-size:13px;}
.stTabs [aria-selected="true"]{background:#1a1a1a!important;color:#eaeaea!important;}
[data-testid="stFileUploader"]{background:transparent;border:none;padding:0;}
[data-testid="stFileUploader"] section{background:#101010;border:1px dashed #2a2a2a;border-radius:10px;}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-thumb{background:#333;border-radius:2px;}
input,textarea{font-size:16px!important;}
.hero{text-align:center;padding:3rem 1rem 2rem;}
.hero h1{font-size:2rem;font-weight:600;background:linear-gradient(135deg,#a78bfa,#f472b6,#fbbf24);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0 0 8px;letter-spacing:-0.02em;}
.hero p{color:#666;font-size:14px;}
.hidden-btn-anchor{width:0;height:0;overflow:hidden;position:absolute;}
.hidden-btn-anchor + div{position:fixed!important;left:-99999px!important;top:-99999px!important;width:1px!important;height:1px!important;overflow:hidden!important;opacity:0!important;pointer-events:none!important;visibility:hidden!important;}
@media (max-width:768px){
 .block-container{padding:0.5rem 0.7rem 12rem!important;}
 section[data-testid="stSidebar"]{width:85vw!important;}
 [data-testid="stChatMessage"] p{font-size:14px;}
 .hero{padding:2rem 1rem 1.5rem;}
 .hero h1{font-size:1.6rem;}
}
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
if "auto_tts" not in st.session_state:st.session_state.auto_tts=False
if "show_up" not in st.session_state:st.session_state.show_up=False
if "last_msg_id" not in st.session_state:st.session_state.last_msg_id=""

qp=st.query_params
if "msg" in qp:
 msg_txt=qp.get("msg","").strip()
 msg_id=qp.get("mid","")
 if msg_txt and msg_id and msg_id!=st.session_state.last_msg_id:
  st.session_state.last_msg_id=msg_id
  st.session_state._new_msg=msg_txt
  st.query_params.clear()
  st.rerun()
if "plus" in qp:
 pid=qp.get("plus","")
 if pid and pid!=st.session_state.get("last_plus_id",""):
  st.session_state.last_plus_id=pid
  st.session_state.show_up=not st.session_state.show_up
  st.query_params.clear()
  st.rerun()

def composer(auto_tts=False,files_html=""):
 has_files=bool(files_html)
 return """
<style>
 #croot{position:fixed;bottom:0;left:0;right:0;padding:14px 12px 20px;background:linear-gradient(180deg,transparent,rgba(11,11,11,0.85) 30%,#0b0b0b 60%);z-index:99998;pointer-events:none;backdrop-filter:blur(8px);}
 #cwrap{max-width:820px;margin:0 auto;pointer-events:auto;}
 #cchips{margin-bottom:8px;display:flex;flex-wrap:wrap;gap:6px;}
 .cchip{display:inline-flex;align-items:center;gap:6px;background:#161616;border:1px solid #2a2a2a;border-radius:10px;padding:6px 10px;font-size:12px;color:#ccc;}
 #cbox{background:#141414;border:1px solid #2a2a2a;border-radius:26px;padding:6px 6px 6px 8px;display:flex;align-items:flex-end;gap:4px;box-shadow:0 10px 40px rgba(0,0,0,0.5);transition:border-color 0.15s;}
 #cbox:focus-within{border-color:#4a4a4a;box-shadow:0 10px 40px rgba(0,0,0,0.6),0 0 0 3px rgba(139,92,246,0.08);}
 #cta{flex:1;background:transparent;border:none;outline:none;color:#eaeaea;font-size:15px;font-family:inherit;padding:10px 8px;resize:none;min-height:24px;max-height:200px;line-height:1.5;overflow-y:auto;}
 #cta::placeholder{color:#555;}
 .cbtn{background:transparent;border:none;color:#8a8a8a;width:40px;height:40px;border-radius:50%;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;transition:all 0.15s;flex-shrink:0;padding:0;user-select:none;-webkit-user-select:none;touch-action:manipulation;}
 .cbtn:hover{background:#1e1e1e;color:#eaeaea;}
 .cbtn:active{transform:scale(0.92);}
 .cbtn svg{width:20px;height:20px;pointer-events:none;}
 .cbtn.send{background:#eaeaea;color:#0b0b0b;}
 .cbtn.send:hover{background:#fff;color:#000;}
 .cbtn.send.dis{background:#2a2a2a;color:#555;cursor:default;}
 .cbtn.send.dis:hover{background:#2a2a2a;transform:none;}
 .cbtn.rec{background:#dc2626!important;color:#fff!important;animation:crec 1.1s infinite;}
 @keyframes crec{0%,100%{box-shadow:0 0 0 0 rgba(220,38,38,0.55);}70%{box-shadow:0 0 0 12px rgba(220,38,38,0);}}
 #cind{position:fixed;top:14px;left:50%;transform:translateX(-50%);background:#dc2626;color:#fff;padding:8px 18px;border-radius:16px;font-size:13px;font-weight:500;z-index:100000;display:none;animation:crec 1.1s infinite;pointer-events:none;letter-spacing:0.02em;}
 #cind.on{display:block;}
 #ctrans{position:fixed;top:52px;left:50%;transform:translateX(-50%);background:rgba(20,20,20,0.95);color:#eaeaea;padding:8px 14px;border-radius:10px;font-size:12px;z-index:100000;display:none;max-width:75vw;text-align:center;border:1px solid #333;pointer-events:none;}
 #ctrans.on{display:block;}
 @media (max-width:768px){
  #croot{padding:10px 10px 14px;}
  .cbtn{width:38px;height:38px;}
  .cbtn svg{width:19px;height:19px;}
  #cta{font-size:16px;padding:9px 6px;}
 }
</style>
<div id="cind">Listening</div>
<div id="ctrans"></div>
<div id="croot">
 <div id="cwrap">
  """ + (f'<div id="cchips">{files_html}</div>' if has_files else '') + """
  <div id="cbox">
   <button id="cplus" class="cbtn" title="Attach files" aria-label="Attach">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
   </button>
   <textarea id="cta" placeholder="Message Gemini..." rows="1" autocomplete="off"></textarea>
   <button id="cvoice" class="cbtn" title="Hold to record" aria-label="Voice">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
   </button>
   <button id="csend" class="cbtn send dis" title="Send" aria-label="Send" disabled>
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>
   </button>
  </div>
 </div>
</div>

<script>
(function(){
 if(window.__composer_init)return;window.__composer_init=true;
 const AUTO_TTS=""" + ("true" if auto_tts else "false") + """;
 const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
 const SS=window.speechSynthesis;

 const cta=document.getElementById('cta');
 const cplus=document.getElementById('cplus');
 const cvoice=document.getElementById('cvoice');
 const csend=document.getElementById('csend');
 const cind=document.getElementById('cind');
 const ctrans=document.getElementById('ctrans');

 function autoResize(){
  cta.style.height='auto';
  cta.style.height=Math.min(cta.scrollHeight,200)+'px';
 }
 function toggleSend(){
  const has=cta.value.trim().length>0;
  csend.classList.toggle('dis',!has);
  csend.disabled=!has;
 }
 cta.addEventListener('input',()=>{autoResize();toggleSend();});
 cta.addEventListener('keydown',(e)=>{
  if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();if(!csend.disabled)doSend();}
 });

 function goWithParams(params){
  const win=window.parent||window;
  const url=new URL(win.location.href);
  Object.keys(params).forEach(k=>url.searchParams.set(k,params[k]));
  win.history.replaceState({},'',url.toString());
  win.location.reload();
 }
 function randId(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8);}

 function doSend(){
  const txt=cta.value.trim();
  if(!txt)return;
  cta.value='';autoResize();toggleSend();
  goWithParams({msg:txt,mid:randId()});
 }
 csend.addEventListener('click',doSend);

 cplus.addEventListener('click',()=>{goWithParams({plus:randId()});});

 let bestVoices={it:null,en:null};
 function pickVoice(lang){
  const voices=SS.getVoices();
  if(!voices||!voices.length)return null;
  const l=lang.toLowerCase().split('-')[0];
  const premium=['neural','natural','wavenet','enhanced','premium','online','samantha','alex','karen','moira','tessa','fiona','daniel','luca','alice','federica','paola','elsa','luciana'];
  const scored=voices.filter(v=>v.lang.toLowerCase().startsWith(l)).map(v=>{
   let s=0;const n=v.name.toLowerCase();
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
 if(SS){loadVoices();SS.onvoiceschanged=loadVoices;}
 function detectLang(text){
  const t=text.slice(0,300).toLowerCase();
  const w=[' e ',' il ',' la ',' che ',' di ',' un ',' una ',' per ',' con ',' non ',' sono ',' è ',' più ',' come ',' cosa ',' anche '];
  let s=0;w.forEach(x=>{if(t.includes(x))s++;});
  return s>=2?'it':'en';
 }
 let speaking=false;
 function stopSpeak(){if(SS){try{SS.cancel();}catch(e){}}speaking=false;}
 function speak(text){
  if(!SS||!text)return;stopSpeak();
  const clean=text.replace(/```[\\s\\S]*?```/g,'').replace(/`[^`]+`/g,'').replace(/\\*\\*/g,'').replace(/[*_#>~|]/g,'').replace(/https?:\\/\\/\\S+/g,'').replace(/\\[([^\\]]+)\\]\\([^\\)]+\\)/g,'$1').replace(/\\s+/g,' ').trim();
  if(!clean)return;
  const sentences=clean.match(/[^.!?]+[.!?]+|[^.!?]+$/g)||[clean];
  const chunks=[];let buf='';
  for(const s of sentences){if((buf+s).length>200){if(buf)chunks.push(buf.trim());buf=s;}else buf+=' '+s;}
  if(buf.trim())chunks.push(buf.trim());
  const lang=detectLang(clean);
  const voice=bestVoices[lang]||bestVoices.it||bestVoices.en;
  speaking=true;let idx=0;
  function next(){
   if(!speaking||idx>=chunks.length){speaking=false;return;}
   const u=new SpeechSynthesisUtterance(chunks[idx]);
   if(voice)u.voice=voice;
   u.lang=voice?voice.lang:(lang==='it'?'it-IT':'en-US');
   u.rate=1.02;u.pitch=1.0;u.volume=1.0;
   u.onend=()=>{idx++;next();};u.onerror=()=>{idx++;next();};
   SS.speak(u);
  }
  next();
 }
 window.__gemini_speak=speak;
 window.__gemini_stop_speak=stopSpeak;

 let rec=null,recording=false,accText='';
 function startRec(){
  if(!SR){ctrans.textContent='Voice not supported';ctrans.classList.add('on');setTimeout(()=>ctrans.classList.remove('on'),1500);return;}
  stopSpeak();
  if(recording)return;
  try{
   rec=new SR();
   rec.lang=navigator.language||'it-IT';
   rec.continuous=true;rec.interimResults=true;
   accText=cta.value;
   if(accText&&!accText.endsWith(' '))accText+=' ';
   rec.onstart=()=>{
    recording=true;cvoice.classList.add('rec');cind.classList.add('on');
    if(navigator.vibrate)navigator.vibrate(20);
   };
   rec.onresult=(e)=>{
    let interim='',final='';
    for(let i=e.resultIndex;i<e.results.length;i++){
     const t=e.results[i][0].transcript;
     if(e.results[i].isFinal)final+=t;else interim+=t;
    }
    if(final)accText+=final+' ';
    cta.value=(accText+interim).trim();
    autoResize();toggleSend();
    if(interim){ctrans.textContent=interim.slice(-60);ctrans.classList.add('on');}
   };
   rec.onerror=()=>{stopRec();};
   rec.onend=()=>{if(recording)stopRec();};
   rec.start();
  }catch(err){ctrans.textContent='Mic error';ctrans.classList.add('on');setTimeout(()=>ctrans.classList.remove('on'),1500);}
 }
 function stopRec(){
  if(rec){try{rec.stop();}catch(e){}rec=null;}
  recording=false;cvoice.classList.remove('rec');cind.classList.remove('on');
  setTimeout(()=>ctrans.classList.remove('on'),600);
  if(navigator.vibrate)navigator.vibrate(15);
 }

 let pt=null,lp=false;
 function ps(){lp=false;pt=setTimeout(()=>{lp=true;startRec();},350);}
 function pe(){if(pt){clearTimeout(pt);pt=null;}if(lp&&recording){setTimeout(()=>stopRec(),80);setTimeout(()=>{lp=false;},150);}}
 function pc(){if(pt){clearTimeout(pt);pt=null;}}
 cvoice.addEventListener('mousedown',ps);
 cvoice.addEventListener('touchstart',ps,{passive:true});
 cvoice.addEventListener('mouseup',pe);
 cvoice.addEventListener('touchend',pe);
 cvoice.addEventListener('mouseleave',pc);
 cvoice.addEventListener('touchcancel',pc);
 cvoice.addEventListener('click',(e)=>{
  if(lp){e.preventDefault();e.stopPropagation();return;}
  if(recording)stopRec();else{
   ctrans.textContent='Hold to record';ctrans.classList.add('on');
   setTimeout(()=>ctrans.classList.remove('on'),900);
  }
 });

 let spt=null,slp=false;
 function sps(){if(csend.disabled){slp=false;spt=setTimeout(()=>{slp=true;startRec();},350);}}
 function spe(){if(spt){clearTimeout(spt);spt=null;}if(slp&&recording){setTimeout(()=>stopRec(),80);setTimeout(()=>{slp=false;},150);}}
 csend.addEventListener('mousedown',sps);
 csend.addEventListener('touchstart',sps,{passive:true});
 csend.addEventListener('mouseup',spe);
 csend.addEventListener('touchend',spe);
 csend.addEventListener('mouseleave',()=>{if(spt){clearTimeout(spt);spt=null;}});

 window.addEventListener('beforeunload',()=>{stopSpeak();stopRec();});
 setTimeout(()=>cta.focus(),300);
})();
</script>
"""

def tts_inline(text,auto=False,key=""):
 safe=json.dumps(text)
 return f"""
<div style="margin-top:6px;display:flex;gap:6px;align-items:center;">
 <button id="pl_{key}" class="tbb" title="Read aloud">
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
 </button>
 <button id="stp_{key}" class="tbb" style="display:none;" title="Stop">
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
 </button>
</div>
<style>
.tbb{{background:transparent;border:1px solid #2a2a2a;color:#888;width:28px;height:28px;border-radius:6px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;padding:0;}}
.tbb:hover{{background:#1a1a1a;color:#eaeaea;border-color:#3a3a3a;}}
.tbb:active{{transform:scale(0.95);}}
</style>
<script>
(function(){{
 const txt={safe};
 const pl=document.getElementById('pl_{key}');
 const stp=document.getElementById('stp_{key}');
 function play(){{
  const fn=(window.parent&&window.parent.__gemini_speak)||window.__gemini_speak;
  if(fn){{fn(txt);pl.style.display='none';stp.style.display='inline-flex';}}
 }}
 function stop(){{
  const fn=(window.parent&&window.parent.__gemini_stop_speak)||window.__gemini_stop_speak;
  if(fn)fn();
  pl.style.display='inline-flex';stp.style.display='none';
 }}
 pl.onclick=play;stp.onclick=stop;
 {"setTimeout(play,400);" if auto else ""}
}})();
</script>
"""

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
   st.session_state.last_msg_id=""
   st.rerun()
  st.markdown("**Options**")
  st.session_state.engineer=st.toggle("Prompt engineer",value=st.session_state.engineer)
  st.session_state.complete=st.toggle("Auto complete",value=st.session_state.complete)
  st.session_state.stream=st.toggle("Stream (SSE)",value=st.session_state.stream)
  st.session_state.auto_tts=st.toggle("Auto TTS",value=st.session_state.auto_tts)
  st.divider()
  if st.button("Attach files",use_container_width=True):
   st.session_state.show_up=not st.session_state.show_up
   st.rerun()
 st.divider()
 status_class="on" if ok else "off"
 st.markdown(f"<div><span class='dot {status_class}'></span>API {'online' if ok else 'offline'}</div>",unsafe_allow_html=True)
 st.caption(f"sessions: {h.get('sessions',0)} · uploads: {h.get('uploads',0)}")

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
 with tab2:
  st.code(f'''const API="{API_BASE}";
const es=new EventSource(`${{API}}/ask/stream?q=${{encodeURIComponent("Ciao")}}`);
es.addEventListener("chunk",e=>console.log(e.data));
es.addEventListener("done",e=>es.close());''',language="javascript")
 with tab3:
  st.code(f'''curl "{API_BASE}/ask?q=Ciao"
curl -N "{API_BASE}/ask/stream?q=Storia"
curl -F "file=@photo.jpg" -F "session_id=my-1" "{API_BASE}/upload"''',language="bash")
 with tab4:
  st.markdown("""
| Method | Path | Description |
|---|---|---|
| GET | `/ask` | JSON response |
| GET | `/ask/stream` | SSE streaming |
| POST | `/upload` | Upload image |
| GET | `/health` | Server status |
""")
else:
 if not ok:
  st.error(f"API offline: {API_BASE}")
  st.stop()

 if not st.session_state.msgs:
  st.markdown("""<div class='hero'>
   <h1>Come posso aiutarti oggi?</h1>
   <p>Chiedi, allega file, o usa la voce</p>
  </div>""",unsafe_allow_html=True)

 for i,m in enumerate(st.session_state.msgs):
  with st.chat_message(m["role"]):
   if m.get("files"):
    chips="".join(f"<span class='chip'>[{('IMG' if fi['kind']=='image' else 'TXT' if fi['kind']=='text' else 'BIN')}] {fi['name']}</span>" for fi in m["files"])
    st.markdown(chips,unsafe_allow_html=True)
   st.markdown(m["content"])
   if m.get("meta"):st.caption(m["meta"])
   if m["role"]=="assistant" and m.get("content"):
    components.html(tts_inline(m["content"],auto=False,key=f"m{i}"),height=42)

 if st.session_state.show_up:
  with st.expander("Attach files",expanded=True):
   up=st.file_uploader("Upload",type=list(IMG_EXT|TEXT_EXT),accept_multiple_files=True,key=f"up_{st.session_state.upkey}",label_visibility="collapsed")
   if up:
    existing={(x["name"],x["size"]) for x in st.session_state.pending}
    for f in up:
     if (f.name,f.size) in existing:continue
     ext=os.path.splitext(f.name)[1].lower().lstrip(".")
     kind="image" if ext in IMG_EXT else "text" if ext in TEXT_EXT else "binary"
     st.session_state.pending.append({"name":f.name,"size":f.size,"bytes":f.getvalue(),"mime":f.type or "","kind":kind,"ext":ext})
    st.session_state.show_up=False
    st.rerun()
   if st.session_state.pending:
    for i,f in enumerate(list(st.session_state.pending)):
     cc1,cc2=st.columns([6,1])
     tag={"image":"IMG","text":"TXT","binary":"BIN"}[f["kind"]]
     cc1.markdown(f"<span class='chip'>[{tag}] {f['name']} · {f['size']/1024:.0f}KB</span>",unsafe_allow_html=True)
     if cc2.button("x",key=f"del_{i}"):
      st.session_state.pending.pop(i);st.rerun()
    ac1,ac2=st.columns(2)
    if ac1.button("Done",use_container_width=True,key="done_up"):
     st.session_state.show_up=False;st.rerun()
    if ac2.button("Clear all",use_container_width=True,key="clr_up"):
     st.session_state.pending=[];st.session_state.upkey+=1;st.session_state.show_up=False;st.rerun()

 files_html=""
 if st.session_state.pending:
  parts=[]
  for f in st.session_state.pending:
   tag="IMG" if f["kind"]=="image" else "TXT" if f["kind"]=="text" else "BIN"
   nm=f["name"][:24]+("..." if len(f["name"])>24 else "")
   parts.append(f"<span class='cchip'>[{tag}] {nm} · {f['size']/1024:.0f}KB</span>")
  files_html="".join(parts)

 components.html(composer(auto_tts=st.session_state.auto_tts,files_html=files_html),height=160)

 q=st.session_state.pop("_new_msg",None)

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
     if f["size"]>MAX_TEXT_BYTES:info.warning(f"{f['name']} too large");continue
     content=read_text_bytes(f["bytes"])
     text_blocks.append(fmt_text_file(f["name"],content))
    if text_blocks:final_q="".join(text_blocks)+"\n\n"+q
    uploaded_count=0
    for i,f in enumerate(image_files):
     info.markdown(f"<small>uploading {f['name']} ({i+1}/{len(image_files)})...</small>",unsafe_allow_html=True)
     if f["size"]>MAX_IMG_BYTES:info.error(f"{f['name']} too large");raise RuntimeError("too large")
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
       try:mm=json.loads(dat);tags=mm.get("enhancements",[]);files_sent=mm.get("files_sent",0)
       except:pass
      elif ev=="chunk":acc+=dat;box.markdown(acc)
      elif ev=="done":
       try:
        d=json.loads(dat);ms=d.get("elapsed_ms",int((time.perf_counter()-t0)*1000))
        extras=[]
        if tags:extras.append(", ".join(tags))
        if files_sent:extras.append(f"{files_sent} file")
        cap=f"{ms} ms"+(" · "+" · ".join(extras) if extras else "")
        meta.caption(cap)
       except:cap=f"{int((time.perf_counter()-t0)*1000)} ms";meta.caption(cap)
      elif ev=="error":
       try:box.error(json.loads(dat).get("error","error"))
       except:box.error(dat)
       acc="";break
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
     box.markdown(ans);meta.caption(cap);final_ans=ans
     st.session_state.msgs.append({"role":"assistant","content":ans,"meta":cap})
    if final_ans:
     components.html(tts_inline(final_ans,auto=st.session_state.auto_tts,key=f"live_{len(st.session_state.msgs)}"),height=42)
    st.session_state.pending=[]
    st.session_state.upkey+=1
    st.rerun()
   except Exception as e:
    info.empty();box.error(str(e));api_clear_uploads(st.session_state.sid)
