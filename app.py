"""AI Video Assistant - single-file Streamlit UI.  Run: streamlit run app.py
Uses your existing modules (utils/, core/) unchanged. Requires streamlit>=1.40."""
from __future__ import annotations

import html, importlib, inspect, json, math, os, re, shutil, subprocess, threading, time, uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="AI Video Assistant", page_icon=":material/graphic_eq:", layout="wide")

APP = "AI Video Assistant"
DATA = Path(os.getenv("VIDEO_ASSISTANT_DATA", "data")).resolve()
LIB, UPL, SETF = DATA / "library", DATA / "uploads", DATA / "settings.json"
EXT = ["mp4", "mkv", "mov", "webm", "avi", "m4v", "mp3", "wav", "m4a", "aac", "flac", "ogg", "opus"]
MAX_MB, LANGS = 1024, ["english", "hinglish"]
SUGGEST = ["Summarize this video.", "What are the key takeaways?", "Explain the most important concepts.",
           "What examples were discussed?", "Give me a detailed explanation of the video."]
EXTRAS = {"takeaways": ("Key takeaways", "List the key takeaways of this video as concise bullet points. Use only the transcript."),
          "concepts": ("Important concepts", "List the most important concepts explained, each with a one-sentence explanation. Use only the transcript."),
          "discussion": ("Main discussion points", "Outline the main discussion points in the order they appear. Use only the transcript.")}
STAGES = [("validate", "Validating input", "Checking the source and reading metadata"),
          ("audio", "Preparing audio", "Extracting, converting and splitting audio into chunks"),
          ("transcribe", "Transcribing", "Converting speech to text"),
          ("summary", "Title and summary", "Summarizing with the LLM"),
          ("insights", "Extracting insights", "Action items, decisions, open questions"),
          ("index", "Building vector index", "Creating embeddings and preparing the assistant")]

CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700&family=Sora:wght@500;600;700&display=swap');
:root{--bg:#06070D;--navy:#0A0F24;--card:#10121C;--c2:#161927;--c3:#1D2135;--line:rgba(255,255,255,.08);--line2:rgba(255,255,255,.15);
--text:#ECEEF8;--muted:#9097B4;--vio:#8B5CF6;--ind:#6366F1;--cyan:#22D3EE;--ok:#34D399;--warn:#FBBF24;--err:#F87171;--ease:cubic-bezier(.2,.7,.2,1)}
html,body,.stApp,button,input,textarea{font-family:'DM Sans',system-ui,sans-serif}
h1,h2,h3,h4,.disp{font-family:'Sora','DM Sans',sans-serif;letter-spacing:-.02em}
.stApp{background:linear-gradient(180deg,var(--bg),var(--navy));color:var(--text)}
.stApp::before,.stApp::after{content:"";position:fixed;z-index:0;pointer-events:none;border-radius:50%;filter:blur(90px)}
.stApp::before{width:520px;height:520px;top:-170px;right:-120px;opacity:.32;background:radial-gradient(circle,var(--vio),transparent 65%);animation:d1 28s ease-in-out infinite alternate}
.stApp::after{width:460px;height:460px;bottom:-190px;left:14%;opacity:.24;background:radial-gradient(circle,var(--ind),transparent 65%);animation:d2 34s ease-in-out infinite alternate}
[data-testid="stAppViewContainer"],[data-testid="stSidebar"]{position:relative;z-index:1}
header[data-testid="stHeader"]{background:transparent}
[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer{display:none!important}
.block-container{max-width:1240px;padding-top:2rem;padding-bottom:4rem}
:focus-visible{outline:2px solid var(--cyan)!important;outline-offset:2px}
mark{background:rgba(34,211,238,.22);color:#C4F5FF;border-radius:4px;padding:0 2px}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#080A14,#0A0E1E);border-right:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:12px;padding:6px 6px 18px}.brand b{font-family:Sora,sans-serif;font-size:1rem;line-height:1.15}
.brand small{display:block;color:var(--muted);font-size:.74rem;font-weight:400}
.logo{width:38px;height:38px;border-radius:11px;display:grid;place-items:center;background:linear-gradient(135deg,var(--vio),var(--ind));box-shadow:0 8px 24px -10px var(--vio)}
.logo i{display:inline-block;width:3px;margin:0 1.5px;border-radius:3px;background:#fff;height:16px;animation:eq 1.1s ease-in-out infinite}
.logo i:nth-child(1){animation-delay:-.2s;height:10px}.logo i:nth-child(2){animation-delay:-.5s}.logo i:nth-child(3){animation-delay:-.8s;height:20px}.logo i:nth-child(4){animation-delay:-.35s;height:12px}
[class*="st-key-nav_"] button,[class*="st-key-navon_"] button{justify-content:flex-start;border:1px solid transparent;background:transparent;color:var(--muted);padding:.55rem .85rem;border-radius:12px;font-weight:500;transition:all .25s var(--ease)}
[class*="st-key-nav_"] button:hover{background:rgba(139,92,246,.1);color:var(--text);transform:translateX(3px)}
[class*="st-key-navon_"] button{background:linear-gradient(90deg,rgba(139,92,246,.24),rgba(99,102,241,.07));border-color:rgba(139,92,246,.38);color:#fff}
.side{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin:6px 0 10px}.side s{text-decoration:none;display:block;color:var(--muted);font-size:.76rem}
.side b{font-size:.88rem;line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.status{display:flex;align-items:center;gap:7px;font-size:.78rem;color:var(--muted);margin-top:6px}.status::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--c,var(--ok))}
.hero{position:relative;text-align:center;padding:2.6rem 1rem 1rem;animation:rise .7s var(--ease) both}
.hero h1{font-size:clamp(2.3rem,5vw,3.9rem);font-weight:700;line-height:1.05;margin:0 0 .9rem}.hero p{color:var(--muted);font-size:1.1rem;max-width:52ch;margin:0 auto 1.3rem;line-height:1.55}
.pt{position:absolute;inset:0;overflow:hidden;pointer-events:none}.pt i{position:absolute;left:var(--x);top:var(--y);width:var(--s);height:var(--s);border-radius:50%;background:var(--cyan);opacity:.45;animation:fl var(--d) ease-in-out infinite alternate}
.wave{display:flex;align-items:center;justify-content:center;gap:4px;height:74px;max-width:640px;margin:0 auto}
.wave span{flex:1;max-width:6px;height:100%;border-radius:6px;background:linear-gradient(180deg,var(--cyan),var(--vio));transform:scaleY(var(--h));animation:wv 1.4s ease-in-out infinite;animation-delay:calc(var(--i)*-70ms)}
.wave.s{height:34px;max-width:260px;margin:0}
.card,[class*="st-key-card_"]{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px 22px;transition:transform .3s var(--ease),border-color .3s,box-shadow .3s}
[class*="st-key-card_"]:hover{transform:translateY(-3px);border-color:var(--line2);box-shadow:0 18px 44px -22px rgba(99,102,241,.55)}
.st-key-input{max-width:780px;margin:0 auto 1.6rem;padding:22px 24px;background:linear-gradient(180deg,var(--c2),var(--card));border:1px solid rgba(139,92,246,.3);border-radius:20px;box-shadow:0 30px 70px -40px rgba(99,102,241,.7)}
.ht{font-family:Sora,sans-serif;font-size:1.4rem;font-weight:600;margin:.2rem 0}.hs{color:var(--muted);margin:0 0 1rem}
.chip{display:inline-flex;padding:3px 10px;border-radius:999px;font-size:.76rem;font-weight:500;background:var(--c3);color:var(--muted);border:1px solid var(--line);margin:0 6px 6px 0}
.chip.ok{color:var(--ok);border-color:rgba(52,211,153,.3);background:rgba(52,211,153,.08)}.chip.warn{color:var(--warn);border-color:rgba(251,191,36,.3);background:rgba(251,191,36,.08)}
.chip.v{color:#C4B5FD;border-color:rgba(139,92,246,.35);background:rgba(139,92,246,.1)}.chip.c{color:var(--cyan);border-color:rgba(34,211,238,.3);background:rgba(34,211,238,.08)}
.msg{font-size:.88rem;margin:-.2rem 0 .6rem}.msg.ok{color:var(--ok)}.msg.err{color:var(--err)}
.file{display:flex;gap:14px;align-items:center;background:var(--c2);border:1px solid var(--line);border-radius:14px;padding:12px 16px;margin:10px 0}
.file .ico{width:40px;height:40px;border-radius:10px;display:grid;place-items:center;background:rgba(139,92,246,.15);color:#C4B5FD;font-weight:700;font-size:.72rem;text-transform:uppercase}
.file b{display:block;word-break:break-all}.file small{color:var(--muted)}
.how{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:1.2rem 0 2rem}.how .n{font-family:Sora;color:var(--cyan);font-weight:600;margin-bottom:6px}.how p{margin:4px 0 0;color:var(--muted);font-size:.92rem}
[data-baseweb="input"],[data-baseweb="base-input"]{background:var(--c2)!important;border-radius:12px!important;border-color:var(--line)!important}
[data-baseweb="input"]:focus-within{border-color:var(--ind)!important;box-shadow:0 0 0 3px rgba(99,102,241,.25)}
[data-baseweb="select"]>div{background:var(--c2)!important;border-color:var(--line)!important;border-radius:12px!important}
.st-key-mode [role="radiogroup"]{display:inline-flex;gap:4px;padding:4px;background:var(--c2);border:1px solid var(--line);border-radius:14px;margin-bottom:.8rem}
.st-key-mode label{margin:0!important;padding:.45rem 1.2rem;border-radius:10px;cursor:pointer;transition:background .3s var(--ease)}.st-key-mode label>div:first-child{display:none}
.st-key-mode label:has(input:checked){background:linear-gradient(135deg,var(--vio),var(--ind));color:#fff}
[data-testid="stFileUploaderDropzone"]{background:var(--c2);border:1.5px dashed rgba(139,92,246,.5);border-radius:16px;padding:1.6rem;transition:border-color .25s}
[data-testid="stFileUploaderDropzone"]:hover{border-color:var(--cyan)}
.stButton>button,.stDownloadButton>button{border-radius:12px;font-weight:600;border:1px solid var(--line2);background:var(--c2);color:var(--text);transition:transform .2s var(--ease),border-color .2s,background .2s}
.stButton>button:hover,.stDownloadButton>button:hover{transform:translateY(-1px);border-color:var(--ind);background:var(--c3)}
.stButton>button:active{transform:scale(.97)}
button[data-testid="stBaseButton-primary"]{background:linear-gradient(135deg,var(--vio),var(--ind));border:0;color:#fff;box-shadow:0 10px 24px -12px var(--vio)}
button:disabled{opacity:.45!important}
[class*="st-key-sg_"] button{justify-content:flex-start;text-align:left;border-radius:999px;font-weight:500;padding:.4rem 1rem;color:var(--muted)}
.stTabs [data-baseweb="tab-list"]{gap:2px;border-bottom:1px solid var(--line)}.stTabs [data-baseweb="tab"]{padding:.7rem 1.1rem;font-weight:500;color:var(--muted);background:transparent}
.stTabs [aria-selected="true"]{color:#fff}.stTabs [data-baseweb="tab-highlight"]{background:linear-gradient(90deg,var(--vio),var(--cyan));height:2px}
.stTabs [data-baseweb="tab-panel"]{animation:fi .4s var(--ease) both;padding-top:1rem}
.ph{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}.clock{font-family:Sora;font-size:1.5rem;font-weight:600;font-variant-numeric:tabular-nums}
.steps{display:flex;flex-direction:column;gap:6px;margin-top:12px}
.step{display:grid;grid-template-columns:30px 1fr auto;gap:14px;align-items:center;padding:12px 14px;border-radius:14px;border:1px solid transparent;opacity:.5;transition:all .4s var(--ease)}
.step .t{font-weight:600}.step .d{color:var(--muted);font-size:.85rem}.step .r{color:var(--muted);font-size:.82rem;font-variant-numeric:tabular-nums}
.step.active{opacity:1;background:rgba(99,102,241,.1);border-color:rgba(99,102,241,.4)}.step.done,.step.warn{opacity:.92}.step.error{opacity:1;background:rgba(248,113,113,.08);border-color:rgba(248,113,113,.45)}
.dot{width:26px;height:26px;border-radius:50%;border:2px solid var(--line2);display:grid;place-items:center}
.step.active .dot{border-color:rgba(34,211,238,.25);border-top-color:var(--cyan);animation:sp .9s linear infinite}
.step.done .dot{background:var(--ok);border-color:var(--ok)}.step.warn .dot{background:var(--warn);border-color:var(--warn)}.step.error .dot{background:var(--err);border-color:var(--err)}
.bar{height:4px;border-radius:4px;background:var(--c3);overflow:hidden;margin-top:9px}.bar>i{display:block;height:100%;background:linear-gradient(90deg,var(--ind),var(--cyan));transition:width .5s}
.bar.ind>i{width:34%;animation:sl 1.5s ease-in-out infinite}.note{color:var(--muted);font-size:.82rem;margin-top:12px;line-height:1.5}
.ok-anim{text-align:center;padding:1.6rem 1rem .6rem}.ok-anim svg{width:90px;height:90px}
.ok-anim circle{stroke:var(--ok);stroke-width:3;fill:rgba(52,211,153,.08);stroke-dasharray:166;stroke-dashoffset:166;animation:dr .7s var(--ease) forwards}
.ok-anim path{stroke:var(--ok);stroke-width:4;fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:48;stroke-dashoffset:48;animation:dr .5s .55s var(--ease) forwards}
.alert{border-radius:14px;padding:14px 16px;margin:10px 0;border:1px solid;font-size:.92rem;line-height:1.5}.alert.err{background:rgba(248,113,113,.08);border-color:rgba(248,113,113,.4)}.alert.warn{background:rgba(251,191,36,.07);border-color:rgba(251,191,36,.3)}
.thumb{height:130px;border-radius:12px;margin-bottom:12px;background:linear-gradient(135deg,rgba(139,92,246,.35),rgba(34,211,238,.18));overflow:hidden;display:grid;place-items:center;color:var(--muted);font-size:.8rem}.thumb img{width:100%;height:100%;object-fit:cover}
.vt{font-weight:600;line-height:1.35;min-height:2.7em;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;margin-bottom:8px}
.wh{display:flex;gap:18px;align-items:center;margin-bottom:1rem}.wh img{width:150px;height:84px;object-fit:cover;border-radius:12px;border:1px solid var(--line)}.wh h2{font-size:1.7rem;margin:0 0 6px;line-height:1.2}
.para{display:grid;grid-template-columns:44px 1fr;gap:12px;padding:14px 6px;border-bottom:1px solid var(--line)}.para .n{color:#5F6580;font-size:.78rem;padding-top:.3rem}.para p{margin:0;line-height:1.8;max-width:74ch}
.prose{font-size:1.05rem;line-height:1.8;max-width:74ch}.sec{font-family:Sora;font-weight:600;margin:1.2rem 0 .6rem}
.mom{border-left:3px solid var(--tone,var(--cyan));background:var(--card);border-radius:4px 14px 14px 4px;padding:12px 16px;margin-bottom:8px;line-height:1.55}
.snip{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 14px;margin:6px 0;font-size:.88rem;color:var(--muted);line-height:1.6}.snip b{display:block;color:var(--text);font-size:.76rem}
[data-testid="stChatMessage"]{border-radius:16px;padding:1rem 1.1rem;border:1px solid var(--line);background:var(--card);animation:rise .4s var(--ease) both}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]){background:linear-gradient(135deg,rgba(99,102,241,.16),rgba(139,92,246,.08));border-color:rgba(99,102,241,.32)}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]){border-left:3px solid var(--cyan)}
.typing{display:inline-flex;gap:5px;padding:6px 2px}.typing i{width:8px;height:8px;border-radius:50%;background:var(--cyan);animation:bn 1.1s ease-in-out infinite}.typing i:nth-child(2){animation-delay:.15s}.typing i:nth-child(3){animation-delay:.3s}
.empty{text-align:center;padding:2.2rem 1rem;color:var(--muted)}.empty h4{color:var(--text);margin:.8rem 0 .3rem}.empty p{margin:0 auto;max-width:42ch}
.orb{width:60px;height:60px;margin:0 auto;border-radius:50%;background:radial-gradient(circle at 35% 30%,var(--cyan),var(--vio) 70%);animation:fl 3.2s ease-in-out infinite alternate}
.sk{border-radius:10px;height:14px;margin:12px 0;background:linear-gradient(90deg,var(--c2) 25%,var(--c3) 37%,var(--c2) 63%);background-size:400% 100%;animation:sh 1.4s ease infinite}
[data-testid="stExpander"]{border:1px solid var(--line)!important;border-radius:12px!important;background:var(--card)}
@keyframes d1{to{transform:translate(-90px,70px) scale(1.15)}}@keyframes d2{to{transform:translate(110px,-60px) scale(1.1)}}
@keyframes eq{0%,100%{transform:scaleY(.45)}50%{transform:scaleY(1)}}@keyframes wv{0%,100%{transform:scaleY(calc(var(--h)*.3))}50%{transform:scaleY(var(--h))}}
@keyframes fl{to{transform:translate(14px,-22px)}}@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}@keyframes fi{from{opacity:0}to{opacity:1}}
@keyframes sp{to{transform:rotate(360deg)}}@keyframes sl{0%{margin-left:-35%}100%{margin-left:100%}}@keyframes dr{to{stroke-dashoffset:0}}
@keyframes bn{0%,60%,100%{transform:translateY(0);opacity:.5}30%{transform:translateY(-6px);opacity:1}}@keyframes sh{0%{background-position:100% 0}100%{background-position:0 0}}
@media(max-width:760px){.wh{flex-direction:column;align-items:flex-start}.wh img{width:100%;height:auto}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}}
</style>"""
st.markdown(CSS, unsafe_allow_html=True)

# ------------------------------------------------------------------ helpers
esc = lambda s: html.escape("" if s is None else str(s), quote=True)
def md(h): st.markdown("\n".join(l.strip() for l in h.splitlines() if l.strip()), unsafe_allow_html=True)
def chip(t, c=""): return f'<span class="chip {c}">{esc(t)}</span>'
def clock(s): s = max(0, int(s)); return f"{s // 60:02d}:{s % 60:02d}"
def dur(s):
    if not s: return ""
    s = int(s); h, r = divmod(s, 3600); m, x = divmod(r, 60); return f"{h}:{m:02d}:{x:02d}" if h else f"{m}:{x:02d}"
def size(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB": return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}"
        n /= 1024
def slug(s, n=40): return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:n] or "video"
def txt(v): return "" if v is None else ("\n".join(map(str, v)) if isinstance(v, (list, tuple)) else str(v)).strip()
def items(v):
    out = []
    for l in txt(v).splitlines():
        l = re.sub(r"^\s*(?:[-*\u2022]+|\d+[.)])\s*", "", l).replace("**", "").strip()
        if l and not l.endswith(":") and l.lower().strip(". ") not in {"none", "n/a"}: out.append(l)
    return out
def mask(m): return re.sub(r"(sk-[A-Za-z0-9_\-]{6,}|(?i:api[_-]?key)[\"'=:\s]+[A-Za-z0-9_\-]{8,})", "[hidden]", m or "")
def paras(t, mx=700):
    out = []
    for b in [x.strip() for x in re.split(r"\n+", (t or "").strip()) if x.strip()]:
        if len(b) <= mx: out.append(b); continue
        cur = ""
        for s in re.split(r"(?<=[.!?])\s+", b):
            while len(s) > mx * 1.5:
                c = s.rfind(" ", 0, mx) or mx
                if cur: out.append(cur); cur = ""
                out.append(s[:c].strip()); s = s[c:].strip()
            if cur and len(cur) + len(s) > mx: out.append(cur); cur = s
            else: cur = f"{cur} {s}".strip()
        if cur: out.append(cur)
    return out
def hl(t, q):
    t = esc(t); q = (q or "").strip()
    return re.sub("(" + re.escape(esc(q)) + ")", r"<mark>\1</mark>", t, flags=re.I) if q else t
def flash(m): st.session_state.setdefault("flash", []).append(m)
def go(page, vid=None):
    st.session_state.page = page
    if vid: st.session_state.active = vid

def empty(title, body):
    md(f'<div class="empty"><div class="orb"></div><h4>{esc(title)}</h4><p>{esc(body)}</p></div>')

def copy_btn(text, label="Copy", h=42):
    page = """<!doctype html><meta charset=utf-8><style>html,body{margin:0;background:transparent}
button{font:600 14px 'DM Sans',system-ui,sans-serif;color:#ECEEF8;background:#161927;border:1px solid rgba(255,255,255,.15);border-radius:12px;height:38px;width:100%;cursor:pointer;transition:.2s}
button:hover{border-color:#6366F1;background:#1D2135}button:active{transform:scale(.97)}button.ok{border-color:#34D399;color:#34D399}</style>
<button id=b type=button></button><script>const T=__T__,L=__L__,b=document.getElementById('b');b.textContent=L;
b.onclick=async()=>{try{await navigator.clipboard.writeText(T)}catch(e){const a=document.createElement('textarea');a.value=T;a.style.cssText='position:fixed;opacity:0';document.body.appendChild(a);a.select();try{document.execCommand('copy')}catch(_){}a.remove()}
b.textContent='Copied';b.classList.add('ok');setTimeout(()=>{b.textContent=L;b.classList.remove('ok')},1600)}</script>"""
    j = lambda v: json.dumps(v).replace("</", "<\\/")
    doc = page.replace("__T__", j(text)).replace("__L__", j(label))
    if hasattr(st, "iframe"): st.iframe(doc, height=h)  # newer Streamlit
    else: components.html(doc, height=h)

# ------------------------------------------------------------------ backend adapter (YOUR modules)
_CAND = {"process_input": [("utils.audio_processor", "process_input")], "transcribe_all": [("core.transcriber", "transcribe_all")],
         "summarize": [("core.summarizer", "summarize"), ("core.summarize", "summarize")],
         "generate_title": [("core.summarizer", "generate_title"), ("core.summarize", "generate_title")],
         "extract_action_items": [("core.extractor", "extract_action_items")], "extract_key_decisions": [("core.extractor", "extract_key_decisions")],
         "extract_questions": [("core.extractor", "extract_questions")], "build_rag_chain": [("core.rag_engine", "build_rag_chain")],
         "ask_question": [("core.rag_engine", "ask_question")]}
_BE = {"fns": {}, "missing": {}}
def backend():
    if _BE["fns"] and not _BE["missing"]: return _BE
    fns, miss = {}, {}
    for n, opts in _CAND.items():
        why = []
        for m, a in opts:
            try: fns[n] = getattr(importlib.import_module(m), a); break
            except Exception as e: why.append(f"{m}: {type(e).__name__}: {e}")
        else: miss[n] = mask(" | ".join(why))
    _BE.update(fns=fns, missing=miss); return _BE
def sig(n):
    try: return set(inspect.signature(backend()["fns"][n]).parameters)
    except Exception: return set()
def norm_answer(raw):
    if isinstance(raw, str): return raw.strip(), []
    if isinstance(raw, tuple) and raw: return str(raw[0]).strip(), [str(getattr(d, "page_content", d)) for d in (raw[1] if len(raw) > 1 else [])]
    if isinstance(raw, dict):
        t = next((raw[k] for k in ("answer", "result", "output_text", "text", "output") if raw.get(k)), "")
        docs = raw.get("source_documents") or raw.get("context") or []
        return str(t).strip(), [str(getattr(d, "page_content", d)) for d in docs] if isinstance(docs, (list, tuple)) else []
    return str(getattr(raw, "content", raw)).strip(), []

# ------------------------------------------------------------------ storage (local JSON)
def lib_list():
    out = []
    for p in LIB.glob("*/meta.json") if LIB.exists() else []:
        try: out.append(json.loads(p.read_text("utf-8")))
        except Exception: pass
    return sorted(out, key=lambda v: v.get("created_at", ""), reverse=True)
def lib_get(i):
    try: return json.loads((LIB / i / "meta.json").read_text("utf-8")) if i and re.fullmatch(r"[a-f0-9]{6,32}", i) else None
    except Exception: return None
def lib_save(r):
    p = LIB / r["id"] / "meta.json"; p.parent.mkdir(parents=True, exist_ok=True)
    t = p.with_suffix(".tmp"); t.write_text(json.dumps(r, ensure_ascii=False, indent=2), "utf-8"); t.replace(p)
def lib_del(i):
    if re.fullmatch(r"[a-f0-9]{6,32}", i or ""):
        shutil.rmtree(LIB / i, ignore_errors=True); shutil.rmtree(UPL / i, ignore_errors=True)

DEFAULTS = {"language": "english", "whisper_model": "base", "translate": False, "actions": True, "decisions": True, "questions": True}
def load_settings():
    s = dict(DEFAULTS)
    try: s.update({k: v for k, v in json.loads(SETF.read_text("utf-8")).items() if k in DEFAULTS})
    except Exception: pass
    return s

# ------------------------------------------------------------------ background jobs
class Runtime:
    def __init__(self): self.jobs, self.chains, self.lock, self.chain_lock = {}, {}, threading.RLock(), threading.Lock()
@st.cache_resource(show_spinner=False)
def rt(): return Runtime()

def friendly(e):
    m = mask(str(e) or e.__class__.__name__)[:600]; l = m.lower(); h = ""
    if "ffmpeg" in l or "ffprobe" in l: h = "FFmpeg is missing or failed. Install it and add it to PATH."
    elif "api key" in l or "401" in l or "unauthorized" in l: h = "The AI provider rejected the request. Check the key in your .env file."
    elif "429" in l or "rate limit" in l: h = "Rate limited by the provider. Wait a minute and retry."
    elif any(x in l for x in ("private", "unavailable", "sign in", "not available")): h = "This video isn't accessible (private, restricted or removed)."
    elif any(x in l for x in ("connection", "timed out", "network")): h = "A network request failed. Check your connection."
    elif "out of memory" in l or "cuda" in l: h = "Whisper ran out of memory. Try a smaller model."
    return m, h

def run_job(jid, be):
    R = rt(); J = R.jobs[jid]; fns = be["fns"]; o = J["opts"]
    def S(k): return next(s for s in J["stages"] if s["key"] == k)
    def start(k):
        with R.lock: s = S(k); s.update(state="active", t0=time.time()); J["where"] = s["label"]
    def end(k, state="done", detail=None, prog="keep"):
        with R.lock:
            s = S(k); s.update(state=state, t1=time.time())
            if detail is not None: s["detail"] = detail
            if prog != "keep": s["prog"] = prog
    def check():
        if J["cancel"].is_set(): raise InterruptedError
    def attempt(label, fn, *a):
        try: return fn(*a)
        except Exception as e: J["warnings"].append(f"{label} could not be generated: {friendly(e)[0]}")
    try:
        J["status"], J["t0"] = "running", time.time()
        if not be["fns"] or be["missing"]: raise RuntimeError("Backend functions could not be imported: " + ", ".join(be["missing"]))
        start("validate"); meta = {}
        if J["type"] == "youtube":
            import yt_dlp
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True, "socket_timeout": 20}) as y:
                i = y.extract_info(J["source"], download=False)
            meta = {"title": i.get("title"), "duration": i.get("duration"), "uploader": i.get("uploader"), "thumbnail": i.get("thumbnail")}
        else:
            if not Path(J["source"]).exists(): raise FileNotFoundError("The uploaded file was not found on disk.")
            try: meta = {"duration": float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", J["source"]], capture_output=True, text=True, timeout=30).stdout.strip())}
            except Exception: pass
        end("validate", detail=meta.get("title") or "OK"); check()
        start("audio"); chunks = fns["process_input"](J["source"]); n = len(chunks) if hasattr(chunks, "__len__") else None
        if n == 0: raise RuntimeError("No audio could be extracted from this source.")
        end("audio", detail=f"{n} chunk(s)" if n else "Done"); check()
        start("transcribe"); kw = {}
        p = sig("transcribe_all")
        wk = next((k for k in ("model_name", "whisper_model", "model") if k in p), None)
        if wk and o.get("whisper_model"): kw[wk] = o["whisper_model"]
        if o.get("translate"):
            if "translate" in p: kw["translate"] = True
            elif "task" in p: kw["task"] = "translate"
        transcript = txt(fns["transcribe_all"](chunks, J["lang"], **kw))
        if not transcript: raise RuntimeError("No speech was detected in this video.")
        end("transcribe", detail=f"{len(transcript.split()):,} words"); check()
        start("summary"); S("summary")["prog"] = (0, 2)
        title = attempt("Title", fns["generate_title"], transcript); S("summary")["prog"] = (1, 2)
        summary = attempt("Summary", fns["summarize"], transcript); S("summary")["prog"] = (2, 2)
        end("summary", "warn" if title is None or summary is None else "done", "Finished with errors" if title is None or summary is None else ""); check()
        tasks = [(k, f) for k, f, on in (("action_items", "extract_action_items", o["actions"]), ("key_decisions", "extract_key_decisions", o["decisions"]), ("open_questions", "extract_questions", o["questions"])) if on]
        ins = {"action_items": None, "key_decisions": None, "open_questions": None}; start("insights")
        for i, (k, f) in enumerate(tasks):
            check(); S("insights")["prog"] = (i, len(tasks)); ins[k] = attempt(k.replace("_", " ").capitalize(), fns[f], transcript)
        bad = any(ins[k] is None for k, _ in tasks)
        end("insights", "warn" if bad else "done", "Finished with errors" if bad else ("" if tasks else "Skipped in settings"), (len(tasks), len(tasks)) if tasks else None); check()
        vid = uuid.uuid4().hex[:12]; chain = None; start("index")
        try: chain = fns["build_rag_chain"](transcript); end("index", detail="Ready")
        except Exception as e:
            J["warnings"].append("The search index could not be built. It will be rebuilt when you open the chat."); end("index", "warn", "Will retry on first question")
        if J["type"] == "upload":
            d = UPL / vid; d.mkdir(parents=True, exist_ok=True)
            try: Path(J["source"]).replace(d / Path(J["source"]).name)
            except Exception: pass
        g = lambda k: txt(ins[k]) if ins[k] is not None else None
        lib_save({"id": vid, "title": txt(title) or meta.get("title") or J["name"], "source": J["source"] if J["type"] == "youtube" else J["name"],
                  "source_type": J["type"], "created_at": datetime.now().isoformat(timespec="seconds"), "duration": meta.get("duration"),
                  "uploader": meta.get("uploader"), "thumbnail": meta.get("thumbnail"), "language": J["lang"], "transcript": transcript,
                  "word_count": len(transcript.split()), "summary": txt(summary) or None, "action_items": g("action_items"),
                  "key_decisions": g("key_decisions"), "open_questions": g("open_questions"), "extras": {}, "warnings": list(J["warnings"])})
        if chain is not None: R.chains[vid] = chain
        J["vid"], J["status"], J["t1"] = vid, "done", time.time()
    except InterruptedError: J["status"], J["t1"] = "cancelled", time.time()
    except Exception as e:
        with R.lock:
            for s in J["stages"]:
                if s["state"] == "active": s["state"], s["t1"] = "error", time.time()
        J["error"], J["hint"] = friendly(e); J["status"], J["t1"] = "error", time.time()

def start_job(source, typ, name, lang, opts):
    R, jid = rt(), uuid.uuid4().hex[:10]
    R.jobs[jid] = {"id": jid, "source": source, "type": typ, "name": name, "lang": lang, "opts": opts, "status": "queued", "cancel": threading.Event(),
                   "stages": [{"key": k, "label": l, "desc": d, "state": "pending", "detail": "", "prog": None, "t0": None, "t1": None} for k, l, d in STAGES],
                   "warnings": [], "error": "", "hint": "", "where": "", "t0": None, "t1": None, "vid": None}
    threading.Thread(target=run_job, args=(jid, backend()), daemon=True).start()
    return jid

# ------------------------------------------------------------------ RAG
def get_chain(v):
    R = rt()
    with R.chain_lock:
        if v["id"] not in R.chains:
            if not (v.get("transcript") or "").strip(): raise RuntimeError("This video has no transcript to search.")
            be = backend()
            if "build_rag_chain" not in be["fns"]: raise RuntimeError("build_rag_chain could not be imported.")
            R.chains[v["id"]] = be["fns"]["build_rag_chain"](v["transcript"])
    return R.chains[v["id"]]
def ask(v, q):
    chain = get_chain(v); text, docs = norm_answer(backend()["fns"]["ask_question"](chain, q))
    if not text: raise RuntimeError("The assistant returned an empty answer.")
    if docs: return text, [("Retrieved passage", d) for d in docs[:5]], "retriever"
    tok = lambda s: {w for w in re.findall(r"[a-z0-9']{4,}", s.lower())}
    qt, sc = tok(q + " " + text), []
    for i, p in enumerate(paras(v["transcript"])):
        o = len(qt & tok(p))
        if o >= 3: sc.append((o / math.sqrt(len(p) + 1), i, p))
    return text, [(f"Transcript part {i + 1}", p) for _, i, p in sorted(sc, reverse=True)[:3]], "keyword"

# ------------------------------------------------------------------ shared views
def transcript_view(v, key):
    t = v.get("transcript") or ""
    if not t.strip(): return empty("No transcript yet", "The transcript appears here once transcription finishes.")
    ps = paras(t); c1, c2, c3 = st.columns([3, 1, 1], vertical_alignment="bottom")
    q = c1.text_input("Search", key=f"ts_{key}", placeholder="Search within the transcript", label_visibility="collapsed")
    with c2: copy_btn(t, "Copy transcript")
    c3.download_button("Download TXT", t, f"{slug(v['title'])}.txt", "text/plain", key=f"dl_{key}", icon=":material/download:", use_container_width=True)
    box = st.container(height=520, border=False)
    if q.strip():
        hits = [(i, p) for i, p in enumerate(ps) if q.lower() in p.lower()]
        box.caption(f"{t.lower().count(q.lower())} matches in {len(hits)} parts")
        for i, p in hits[:40]: box.markdown(f'<div class="para"><div class="n">{i + 1}</div><p>{hl(p, q)}</p></div>', unsafe_allow_html=True)
        if not hits: box.info("No matches.")
        return
    PG, pk = 12, f"tp_{key}"; st.session_state.setdefault(pk, 0); pages = max(1, math.ceil(len(ps) / PG))
    pg = min(st.session_state[pk], pages - 1)
    for i, p in enumerate(ps[pg * PG:(pg + 1) * PG], pg * PG + 1): box.markdown(f'<div class="para"><div class="n">{i}</div><p>{esc(p)}</p></div>', unsafe_allow_html=True)
    a, b, c = st.columns([1, 2, 1], vertical_alignment="center")
    a.button("Previous", key=f"pv_{key}", disabled=pg == 0, icon=":material/chevron_left:", on_click=lambda: st.session_state.update({pk: pg - 1}), use_container_width=True)
    b.caption(f"Parts {pg * PG + 1}-{min(len(ps), (pg + 1) * PG)} of {len(ps)}  |  {len(t.split()):,} words. Timestamps unavailable: the backend returns plain text.")
    c.button("Next", key=f"nx_{key}", disabled=pg >= pages - 1, icon=":material/chevron_right:", on_click=lambda: st.session_state.update({pk: pg + 1}), use_container_width=True)

def summary_md(v):
    out = f"# {v['title']}\n\n## Overview\n{v.get('summary') or '_Not available_'}\n"
    for k, (lab, _) in EXTRAS.items():
        if v.get("extras", {}).get(k): out += f"\n## {lab}\n{v['extras'][k]}\n"
    for lab, k in (("Action items", "action_items"), ("Key decisions", "key_decisions"), ("Open questions", "open_questions")):
        if items(v.get(k)): out += f"\n## {lab}\n" + "\n".join(f"- {i}" for i in items(v[k])) + "\n"
    return out

def summary_view(v, key):
    s = v.get("summary")
    if not s:
        empty("No summary available", "Summarization did not complete for this video, so nothing has been made up.")
        if v.get("transcript") and st.button("Try summarizing again", key=f"rs_{key}", icon=":material/refresh:"):
            try:
                with st.spinner("Summarizing..."):
                    r = txt(backend()["fns"]["summarize"](v["transcript"]))
                if r: v = {**v, "summary": r}; lib_save(v); st.rerun()
            except Exception as e: st.error(f"Summary failed: {friendly(e)[0]}")
        return
    c1, c2, c3, _ = st.columns([1, 1, 1, 2], vertical_alignment="bottom")
    with c1: copy_btn(summary_md(v), "Copy summary")
    c2.download_button("Markdown", summary_md(v), f"{slug(v['title'])}-summary.md", "text/markdown", key=f"smd_{key}", icon=":material/download:", use_container_width=True)
    c3.download_button("TXT", summary_md(v), f"{slug(v['title'])}-summary.txt", "text/plain", key=f"stx_{key}", icon=":material/download:", use_container_width=True)
    md('<div class="sec">Overview</div>'); st.markdown(f'<div class="prose">{esc(s).replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    for k, (lab, prompt) in EXTRAS.items():
        md(f'<div class="sec">{lab}</div>'); saved = v.get("extras", {}).get(k)
        if saved: st.markdown(saved)
        elif st.button(f"Generate {lab.lower()}", key=f"ex_{k}_{key}", icon=":material/auto_awesome:", help="Asked through your RAG pipeline using the transcript only."):
            try:
                with st.spinner("Asking the transcript..."): a, _, _ = ask(v, prompt)
                ex = {**v.get("extras", {}), k: a}; lib_save({**v, "extras": ex}); st.rerun()
            except Exception as e: st.error(f"Could not generate: {friendly(e)[0]}")
    acts = items(v.get("action_items"))
    if acts:
        md('<div class="sec">Action items</div>')
        for a in acts: md(f'<div class="mom" style="--tone:var(--warn)">{esc(a)}</div>')

def moments_view(v, key):
    groups = [("Action items", "action_items", "var(--warn)"), ("Key decisions", "key_decisions", "var(--vio)"), ("Open questions", "open_questions", "#FF8097")]
    if not any(items(v.get(k)) for _, k, _ in groups): return empty("No key moments extracted", "No action items, decisions or open questions were found or extraction was skipped.")
    st.caption("Timestamps are not shown because the transcription backend returns plain text.")
    for lab, k, tone in groups:
        its = items(v.get(k))
        if not its: continue
        md(f'<div class="sec">{lab}</div>')
        for j, it in enumerate(its):
            if k == "action_items": st.checkbox(it, key=f"ck_{key}_{j}")
            else:
                md(f'<div class="mom" style="--tone:{tone}">{esc(it)}</div>')
                if k == "open_questions": st.button("Ask in chat", key=f"aq_{key}_{j}", icon=":material/forum:", on_click=lambda q=it: st.session_state.update({f"pend_{v['id']}": q}))

def chat_view(v, key, height=520):
    vid, hist = v["id"], st.session_state.chats.setdefault(v["id"], [])
    h1, h2 = st.columns([3, 1], vertical_alignment="center")
    h1.markdown("#### Ask this video")
    h2.button("Clear chat", key=f"cl_{key}", disabled=not hist, icon=":material/delete_sweep:", on_click=lambda: hist.clear(), use_container_width=True)
    ok = bool((v.get("transcript") or "").strip())
    box = st.container(height=height, border=False)
    with box:
        if not hist:
            if not ok: empty("Chat unavailable", "There is no transcript for this video, so there is nothing to answer from.")
            else:
                empty("Ask anything", "Answers come only from this video's transcript.")
                for i, q in enumerate(SUGGEST): st.button(q, key=f"sg_{key}_{i}", on_click=lambda q=q: st.session_state.update({f"pend_{vid}": q}), use_container_width=True)
        for i, m in enumerate(hist):
            with st.chat_message(m["role"], avatar=":material/person:" if m["role"] == "user" else ":material/auto_awesome:"):
                st.markdown(m["content"])
                if m["role"] == "assistant" and not m.get("err"):
                    if m.get("src"):
                        with st.expander(f"Sources ({len(m['src'])})"):
                            if m["kind"] == "keyword": st.caption("Closest transcript passages by keyword match. The RAG engine did not return its retrieved documents.")
                            for lab, p in m["src"]: st.markdown(f'<div class="snip"><b>{esc(lab)}</b>{esc(p[:500])}{"..." if len(p) > 500 else ""}</div>', unsafe_allow_html=True)
                    copy_btn(m["content"], "Copy answer", 40)
        live = st.container()
    fu = [q for q in items(v.get("open_questions"))[:3]] if hist else []
    for i, q in enumerate(fu): st.button(q[:110], key=f"fu_{key}_{i}", on_click=lambda q=q: st.session_state.update({f"pend_{vid}": q}), icon=":material/subdirectory_arrow_right:")
    typed = st.chat_input("Ask anything about this video", key=f"ci_{key}", disabled=not ok)
    q = typed or st.session_state.pop(f"pend_{vid}", None)
    if q:
        hist.append({"role": "user", "content": q})
        with live:
            with st.chat_message("user", avatar=":material/person:"): st.markdown(q)
            with st.chat_message("assistant", avatar=":material/auto_awesome:"):
                ph = st.empty(); ph.markdown('<div class="typing"><i></i><i></i><i></i></div>', unsafe_allow_html=True)
                if vid not in rt().chains: ph.markdown(f'{"".join(f"<div class=sk style=width:{w}%></div>" for w in (90, 70, 80))}<small>Rebuilding the search index for this video...</small>', unsafe_allow_html=True)
                try: a, src, kind = ask(v, q); hist.append({"role": "assistant", "content": a, "src": src, "kind": kind})
                except Exception as e: hist.append({"role": "assistant", "content": f"I couldn't answer that. {friendly(e)[0]}", "err": True})
        st.rerun()

def vheader(v):
    img = f'<img src="{esc(v["thumbnail"])}" alt="">' if v.get("thumbnail") else ""
    chips = chip("YouTube" if v["source_type"] == "youtube" else "Upload", "v") + chip("Ready", "ok") + chip(f'{v.get("word_count", 0):,} words', "c")
    if v.get("duration"): chips += chip(dur(v["duration"]))
    md(f'<div class="wh">{img}<div><h2>{esc(v["title"])}</h2>{chips}<div style="color:var(--muted);font-size:.85rem">{esc(v.get("source", ""))}{" - " + esc(v["uploader"]) if v.get("uploader") else ""}</div></div></div>')

def picker(label, key):
    vs = lib_list()
    if not vs: empty("No videos yet", "Process a video from the dashboard first."); st.button("Go to dashboard", type="primary", on_click=go, args=("dashboard",)); return None
    ids = [x["id"] for x in vs]; cur = st.session_state.active
    pick = st.selectbox(label, ids, index=ids.index(cur) if cur in ids else 0, key=key, format_func=lambda i: next(x["title"] for x in vs if x["id"] == i)[:90])
    st.session_state.active = pick; return next(x for x in vs if x["id"] == pick)

# ------------------------------------------------------------------ pages
def wave(n=56, small=False):
    sp = "".join(f'<span style="--i:{i};--h:{0.28 + 0.72 * abs(math.sin(i * .55) * math.cos(i * .21)):.2f}"></span>' for i in range(n))
    return f'<div class="wave{" s" if small else ""}" aria-hidden="true">{sp}</div>'

def steps_html(stages):
    ck = '<svg viewBox="0 0 24 24" width="14" height="14"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="#06150F" stroke-width="3" stroke-linecap="round"/></svg>'
    out, now = [], time.time()
    for s in stages:
        e = ((s["t1"] or now) - s["t0"]) if s["t0"] else 0; right = extra = ""; d = s["desc"]
        if s["state"] == "active":
            if s["prog"]: a, b = s["prog"]; right = f"{a} of {b}"; extra = f'<div class="bar"><i style="width:{a / b * 100 if b else 0:.0f}%"></i></div>'
            else: right = clock(e); extra = '<div class="bar ind"><i></i></div>'
        elif s["state"] in ("done", "warn", "error"): right = f"{e:.1f}s"; d = s["detail"] or d
        out.append(f'<div class="step {s["state"]}"><div class="dot">{ck if s["state"] == "done" else ""}</div><div><div class="t">{esc(s["label"])}</div><div class="d">{esc(d)}</div>{extra}</div><div class="r">{right}</div></div>')
    return f'<div class="steps">{"".join(out)}</div>'

@st.fragment(run_every=1.0)
def progress_panel(jid):
    J = rt().jobs.get(jid)
    if not J or J["status"] not in ("queued", "running"): st.rerun(); return
    el = (time.time() - J["t0"]) if J["t0"] else 0
    with st.container(key="card_proc"):
        md(f'<div class="ph"><div>{chip(J["name"][:70], "v")}<div style="font-weight:600">{"Cancelling after the current step" if J["cancel"].is_set() else esc(J["where"] or "Starting")}</div></div><div class="clock">{clock(el)}</div></div>')
        md(wave(48, True)); md(steps_html(J["stages"]))
        md('<div class="note">Whisper and the vector index each run as one backend call, so they show a moving indicator instead of a percentage. Percentages only appear where a real count exists.</div>')
        st.button("Cancel", key="cancel", icon=":material/close:", disabled=J["cancel"].is_set(), on_click=J["cancel"].set, help="Stops after the current backend call. A running Whisper call can't be interrupted midway.")

def page_dashboard():
    ss, R = st.session_state, rt(); J = R.jobs.get(ss.job)
    if J:
        if J["status"] in ("queued", "running"):
            md('<div class="ht">Processing your video</div><p class="hs">You can switch pages while this runs.</p>'); return progress_panel(J["id"])
        if J["status"] == "done":
            md('<div class="ok-anim"><svg viewBox="0 0 60 60"><circle cx="30" cy="30" r="26"/><path d="M18 31l8 8 16-17"/></svg><div class="ht" style="margin-top:12px">Your video is ready</div><p class="hs">Transcript, summary and chat are in the workspace.</p></div>')
            for w in J["warnings"]: md(f'<div class="alert warn"><b>Heads up. </b>{esc(w)}</div>')
            with st.container(key="card_done"): md(steps_html(J["stages"]))
            a, b, _ = st.columns([1.2, 1, 2])
            a.button("Open workspace", type="primary", icon=":material/arrow_forward:", use_container_width=True, on_click=lambda: (ss.update(job=None), go("workspace", J["vid"])))
            b.button("Process another", use_container_width=True, on_click=lambda: ss.update(job=None)); return
        md(f'<div class="ht">{"Processing was cancelled" if J["status"] == "cancelled" else "Processing failed"}</div>')
        if J["status"] == "error": md(f'<div class="alert err"><b>Failed during: {esc(J["where"])}</b>{esc(J["error"])}{"<br><span style=color:var(--muted)>" + esc(J["hint"]) + "</span>" if J["hint"] else ""}</div>')
        with st.container(key="card_fail"): md(steps_html(J["stages"]))
        return st.button("Back to input", type="primary", icon=":material/refresh:", on_click=lambda: ss.update(job=None))
    pts = "".join(f'<i style="--x:{(i * 37) % 100}%;--y:{(i * 53 + 11) % 100}%;--s:{3 + (i % 3) * 2}px;--d:{5 + (i % 5) * 1.7:.1f}s"></i>' for i in range(14))
    md(f'<div class="hero"><div class="pt" aria-hidden="true">{pts}</div><h1>Every video has answers.</h1><p>Turn hours of video into searchable knowledge. Upload, understand, and ask anything.</p>{wave(64)}</div>')
    be = backend()
    if be["missing"]: md('<div class="alert err"><b>Your backend could not be loaded.</b>' + "".join(f"<br><code>{esc(k)}</code>: {esc(v)}" for k, v in be["missing"].items()) + "</div>")
    valid, src, typ, name, up = False, "", "", "", None
    with st.container(key="input"):
        mode = st.radio("Source", ["YouTube URL", "Upload file"], horizontal=True, key="mode", label_visibility="collapsed")
        if mode == "YouTube URL":
            u = st.text_input("YouTube link", key="yt", placeholder="https://www.youtube.com/watch?v=...", label_visibility="collapsed")
            if u.strip():
                ok, m = check_url(u); md(f'<div class="msg {"ok" if ok else "err"}">{esc(m)}</div>'); valid, src, typ, name = ok, u.strip(), "youtube", u.strip()
        else:
            up = st.file_uploader("Drop a video or audio file", type=EXT, key=f"up_{ss.nonce}", label_visibility="collapsed", help=f"Up to {MAX_MB} MB")
            if up is not None:
                ext = Path(up.name).suffix.lstrip(".").lower(); ok, m = (True, "") if up.size > 0 and up.size <= MAX_MB << 20 else (False, "This file is empty." if up.size == 0 else f"This file is larger than {MAX_MB} MB.")
                md(f'<div class="file"><div class="ico">{esc(ext[:4])}</div><div><b>{esc(up.name)}</b><small>{size(up.size)} &middot; .{esc(ext)}</small></div></div>')
                if not ok: md(f'<div class="msg err">{esc(m)}</div>')
                st.button("Remove file", key="rm", icon=":material/close:", on_click=lambda: ss.update(nonce=ss.nonce + 1)); valid, typ, name = ok, "upload", up.name
        c1, c2 = st.columns([1, 1.4], vertical_alignment="bottom")
        lang = c1.selectbox("Spoken language", LANGS, index=LANGS.index(ss.settings["language"]), key="lang")
        go_ = c2.button("Process video", type="primary", use_container_width=True, icon=":material/play_arrow:", disabled=bool(be["missing"]))
    if go_:
        if not valid: st.error("Add a valid YouTube link or a supported file first.")
        else:
            if typ == "upload":
                d = UPL / uuid.uuid4().hex[:10]; d.mkdir(parents=True, exist_ok=True); f = d / (slug(Path(up.name).stem) + Path(up.name).suffix.lower()); f.write_bytes(up.getbuffer()); src = str(f)
            s = ss.settings; ss.job = start_job(src, typ, name, lang, {"whisper_model": s["whisper_model"], "translate": s["translate"], "actions": s["actions"], "decisions": s["decisions"], "questions": s["questions"]}); st.rerun()
    md('<div class="how"><div class="card"><div class="n">1</div><b>Add a video</b><p>Paste a YouTube link or upload a video or audio file.</p></div><div class="card"><div class="n">2</div><b>We transcribe it</b><p>Audio is extracted, split and transcribed with Whisper, then summarized.</p></div><div class="card"><div class="n">3</div><b>Ask anything</b><p>Chat with the transcript. Answers come from what was actually said.</p></div></div>')
    rec = lib_list()[:3]
    if rec:
        md('<div class="sec">Recent videos</div>')
        for col, v in zip(st.columns(3, gap="medium"), rec):
            with col: vcard(v, "r")

def check_url(u):
    u = u.strip()
    if " " in u: return False, "That link contains spaces. Paste only the video URL."
    p = urlparse(u if "://" in u else "https://" + u); h = (p.hostname or "").lower(); path = p.path.strip("/")
    if h not in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be", "www.youtu.be"}: return False, "This doesn't look like a YouTube link. Use a youtube.com or youtu.be URL."
    if path == "playlist": return False, "This is a playlist link. Paste the link to a single video."
    parts = path.split("/"); vid = parts[0] if h.endswith("youtu.be") else (parse_qs(p.query).get("v", [None])[0] if path == "watch" else (parts[1] if parts[0] in {"shorts", "live", "embed", "v"} and len(parts) > 1 else None))
    return (True, "Valid YouTube link.") if vid and re.fullmatch(r"[A-Za-z0-9_-]{11}", vid) else (False, "The video ID is missing or malformed. Copy the link from the video page.")

@st.dialog("Delete this video?")
def confirm_del(v):
    st.write(f"**{v['title']}** will be removed from this device with its transcript, summary and uploaded file. This can't be undone.")
    a, b = st.columns(2)
    if a.button("Delete", type="primary", use_container_width=True):
        lib_del(v["id"]); rt().chains.pop(v["id"], None); st.session_state.chats.pop(v["id"], None)
        if st.session_state.active == v["id"]: st.session_state.active = None
        flash("Video deleted"); st.rerun()
    if b.button("Cancel", use_container_width=True): st.rerun()

def vcard(v, p):
    th = f'<img src="{esc(v["thumbnail"])}" alt="" loading="lazy">' if v.get("thumbnail") else "No preview"
    chips = chip("YouTube" if v["source_type"] == "youtube" else "Upload", "v") + (chip(dur(v["duration"])) if v.get("duration") else "") + (chip("Transcript", "ok") if v.get("transcript") else chip("No transcript", "warn")) + (chip("Summary", "ok") if v.get("summary") else chip("No summary", "warn"))
    try: d = datetime.fromisoformat(v["created_at"]).strftime("%d %b %Y, %H:%M")
    except Exception: d = ""
    with st.container(key=f"card_{p}_{v['id']}"):
        md(f'<div class="thumb">{th}</div><div class="vt">{esc(v["title"])}</div>{chips}<div style="color:var(--muted);font-size:.8rem;margin:2px 0 10px">{d}</div>')
        a, b = st.columns([4, 1])
        a.button("Open workspace", key=f"o_{p}_{v['id']}", type="primary", use_container_width=True, on_click=go, args=("workspace", v["id"]))
        if b.button("", key=f"d_{p}_{v['id']}", icon=":material/delete:", help="Delete", use_container_width=True): confirm_del(v)

def page_library():
    md('<div class="ht">My Videos</div><p class="hs">Saved on this device in the data folder. Deleting a video removes its files.</p>')
    vs = lib_list()
    if not vs: empty("No videos yet", "Processed videos appear here."); return st.button("Go to dashboard", type="primary", on_click=go, args=("dashboard",))
    q = st.text_input("Search", placeholder="Search by title or source", label_visibility="collapsed", key="lq")
    if q.strip(): vs = [v for v in vs if q.lower() in (v["title"] + v.get("source", "")).lower()]
    cols = st.columns(3, gap="medium")
    for i, v in enumerate(vs):
        with cols[i % 3]: vcard(v, "l")

def page_workspace():
    v = lib_get(st.session_state.active)
    if not v: empty("No video selected", "Open a video from My Videos."); return st.button("My Videos", on_click=go, args=("library",))
    vheader(v)
    for w in v.get("warnings", []): md(f'<div class="alert warn">{esc(w)}</div>')
    L, Rr = st.columns([1.15, 1], gap="large")
    with L:
        t1, t2, t3 = st.tabs(["Transcript", "Summary", "Key moments"])
        with t1: transcript_view(v, "ws")
        with t2: summary_view(v, "ws")
        with t3: moments_view(v, "ws")
    with Rr: chat_view(v, "ws", 560)

def page_chat():
    md('<div class="ht">AI Chat</div><p class="hs">Ask questions about any saved video. Answers use its transcript and your RAG pipeline.</p>')
    v = picker("Video", "chat_pick")
    if v: chat_view(v, "pg", 560)
def page_transcripts():
    md('<div class="ht">Transcripts</div>'); v = picker("Video", "tr_pick")
    if v: transcript_view(v, "pg")
def page_summaries():
    md('<div class="ht">Summaries</div>'); v = picker("Video", "su_pick")
    if v: summary_view(v, "pg")

def page_settings():
    ss = st.session_state; s = dict(ss.settings); be = backend(); p = sig("transcribe_all")
    md('<div class="ht">Settings</div><p class="hs">Saved locally. API keys are read from .env and never shown.</p>')
    with st.container(key="card_s1"):
        st.markdown("##### Transcription")
        s["language"] = st.selectbox("Default spoken language", LANGS, index=LANGS.index(s["language"]))
        wk, tk = any(k in p for k in ("model_name", "whisper_model", "model")), ("translate" in p or "task" in p)
        if wk: s["whisper_model"] = st.selectbox("Whisper model", ["tiny", "base", "small", "medium", "large"], index=["tiny", "base", "small", "medium", "large"].index(s["whisper_model"]))
        if tk: s["translate"] = st.toggle("Translate to English", value=s["translate"])
        if not (wk and tk): st.caption("Whisper model and translation are hidden because your transcribe_all(chunks, language) doesn't accept those arguments. Add `model_name` and/or `translate` parameters to enable them.")
    with st.container(key="card_s2"):
        st.markdown("##### Analysis")
        st.caption("Choose which extractions run. Skipping saves LLM calls.")
        s["actions"] = st.toggle("Action items", value=s["actions"]); s["decisions"] = st.toggle("Key decisions", value=s["decisions"]); s["questions"] = st.toggle("Open questions", value=s["questions"])
    if s != ss.settings:
        ss.settings = s; DATA.mkdir(parents=True, exist_ok=True); SETF.write_text(json.dumps(s, indent=2), "utf-8"); st.toast("Settings saved")
    with st.container(key="card_s3"):
        st.markdown("##### Data")
        vs = lib_list(); total = sum(f.stat().st_size for b in (LIB, UPL) if b.exists() for f in b.rglob("*") if f.is_file())
        st.caption(f"{len(vs)} video(s), {size(total)} stored in {DATA}")
        a, b = st.columns(2)
        if a.button("Clear chat history", use_container_width=True): ss.chats = {}; st.toast("Chat history cleared")
        if b.button("Delete all saved videos", use_container_width=True, disabled=not vs): confirm_all()
    with st.container(key="card_s4"):
        st.markdown("##### Application")
        keys = {k: bool(os.getenv(k)) for k in ("MISTRAL_API_KEY", "OPENAI_API_KEY")}
        md(chip(APP, "v") + chip(f"Streamlit {st.__version__}") + "".join(chip(f"{k}: {'set' if v else 'not set'}", "ok" if v else "warn") for k, v in keys.items()))
        md("".join(chip(n, "warn" if n in be["missing"] else "ok") for n in _CAND))

@st.dialog("Delete all videos?")
def confirm_all():
    st.write("Every saved video, transcript and uploaded file will be removed from this device.")
    a, b = st.columns(2)
    if a.button("Delete everything", type="primary", use_container_width=True):
        for v in lib_list(): lib_del(v["id"])
        rt().chains.clear(); st.session_state.chats = {}; st.session_state.active = None; flash("Library cleared"); st.rerun()
    if b.button("Cancel", use_container_width=True): st.rerun()

# ------------------------------------------------------------------ shell
ss = st.session_state
for k, d in (("page", "dashboard"), ("active", None), ("job", None), ("chats", {}), ("nonce", 0)): ss.setdefault(k, d)
if "settings" not in ss: ss.settings = load_settings()
NAV = [("dashboard", "Dashboard", "space_dashboard"), ("library", "My Videos", "video_library"), ("chat", "AI Chat", "forum"), ("transcripts", "Transcripts", "subtitles"), ("summaries", "Summaries", "summarize"), ("settings", "Settings", "settings")]
with st.sidebar:
    md(f'<div class="brand"><div class="logo"><i></i><i></i><i></i><i></i></div><b>{APP}<small>Video intelligence</small></b></div>')
    cur = "library" if ss.page == "workspace" else ss.page
    for k, l, i in NAV: st.button(l, key=("navon_" if k == cur else "nav_") + k, icon=f":material/{i}:", use_container_width=True, on_click=go, args=(k,))
    st.divider()
    J = rt().jobs.get(ss.job)
    if J and J["status"] in ("queued", "running"): md(f'<div class="side"><s>In progress</s><b>{esc(J["name"])}</b></div>'); st.button("View progress", key="vp", use_container_width=True, icon=":material/hourglass_top:", on_click=go, args=("dashboard",))
    av = lib_get(ss.active)
    if av: md(f'<div class="side"><s>Active video</s><b>{esc(av["title"])}</b></div>'); st.button("Open workspace", key="ow", use_container_width=True, icon=":material/open_in_new:", on_click=go, args=("workspace", av["id"]))
    ok = not backend()["missing"]; md(f'<div class="status" style="--c:var(--{"ok" if ok else "err"})">{"Backend connected" if ok else "Backend unavailable"}</div><div class="status" style="--c:var(--ind)">{len(lib_list())} saved on this device</div>')
for m in ss.pop("flash", []): st.toast(m)
{"dashboard": page_dashboard, "library": page_library, "workspace": page_workspace, "chat": page_chat, "transcripts": page_transcripts, "summaries": page_summaries, "settings": page_settings}.get(ss.page, page_dashboard)()
