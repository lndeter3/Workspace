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
TEXT_EXT={".txt",".md",".csv",".json",".py",".js",".ts",".jsx",".tsx",".html",".css",".xml",".yaml",".yml",".sh",".bash",".sql",".c",".cpp",".h",".hpp",".java",".kt",".go",".rs",".rb",".php",".swift",".toml",".ini",".cfg",".log",".env",".gitignore",".dockerfile"}
IMG_EXT={".png",".jpg",".jpeg",".webp",".gif",".bmp"}
LANG_MAP={"py":"python","js":"javascript","ts":"typescript","sh":"bash","bash":"bash","cpp":"cpp","c":"c","cs":"csharp","java":"java","kt":"kotlin","go":"go","rs":"rust","rb":"ruby","php":"php","sql":"sql","html":"html","css":"css","json":"json","yaml":"yaml","yml":"yaml","toml":"toml","xml":"xml","md":"markdown"}
MAX_TEXT_BYTES=500000
MAX_TEXT_LINES=5000
def is_text_file(name,mime):
 ext=os.path.splitext(name)[1].lower()
 if ext in TEXT_EXT:return True
 if mime and (mime.startswith("text/") or mime in ("application/json","application/xml","application/javascript")):return True
 return False
def is_image_file(name,mime):
 ext=os.path.splitext(name)[1].lower()
 if ext in IMG_EXT:return True
 if mime and mime.startswith("image/"):return True
 return False
def read_text_bytes(data,name):
 for enc in ["utf-8","latin-1","cp1252"]:
  try:return data.decode(enc,errors="replace")
  except:continue
 return data.decode("utf-8",errors="replace")
def format_text_file(name,content):
 ext=os.path.splitext(name)[1].lower().lstrip(".")
 lang=LANG_MAP.get(ext,ext)
 lines=content.split("\n")
 trunc=""
 if len(lines)>MAX_TEXT_LINES:
  content="\n".join(lines[:MAX_TEXT_LINES])
  trunc=f", TRONCATO a {MAX_TEXT_LINES} righe di {len(lines)}"
 size=len(content.encode("utf-8"))
 return f"\n[FILE: {name} ({size}B, {len(lines)} righe{trunc})]\n```{lang}\n{content}\n```\n"
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
 up=st.file_uploader("Carica",type=["png","jpg","jpeg","webp","gif","bmp","txt","md","csv","json","py","js","ts","jsx","tsx","html","css","xml","yaml","yml","sh","sql","c","cpp","h","java","kt","go","rs","rb","php","toml","ini","cfg","log","env"],accept_multiple_files=True,key=f"up_{st.session_state.upk}",label_visibility="collapsed")
 if up:
  existing={(x["name"],x["size"]) for x in st.session_state.pending}
  for f in up:
   if (f.name,f.size) not in existing:
    mime=f.type or ""
    kind="text" if is_text_file(f.name,mime) else "image" if is_image_file(f.name,mime) else "binary"
    st.session_state.pending.append({"name":f.name,"size":f.size,"bytes":f.getvalue(),"mime":mime,"kind":kind})
 if st.session_state.pending:
  st.markdown(f"<div style='color:#8e8e8e;font-size:12px;margin:8px 0 4px;'>{len(st.session_state.pending)} file pronti</div>",unsafe_allow_html=True)
  for i,f in enumerate(st.session_state.pending):
   c1,c2=st.columns([5,1])
   
