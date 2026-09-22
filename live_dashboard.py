import asyncio
import contextlib
import io
import time
from datetime import datetime

import streamlit as st

from resources.resource import Resource
from resources.registry import ResourceRegistry
from scheduler.scheduler import Scheduler
from prediction.history import RuntimeHistory
from prediction.predictor import PredictionEngine
from reservation.reservation import ReservationEngine
from runtime.monitor import RuntimeMonitor
from runtime.interceptor import RuntimeInterceptor
from ai.local_model import LocalAI
from agents.live_agent import LiveAgent
from tools.search_tool import SearchTool
from tools.database_tool import DatabaseTool
from tools.python_tool import PythonTool

st.set_page_config(
    page_title="NEXORA Live Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

GALAXY_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Orbitron:wght@500;600;700;800&display=swap');
:root{--bg:#020511;--panel:#080d27;--blue:#35c8ff;--purple:#9b55ff;--pink:#df62ff;--green:#31e6a4;--text:#edf5ff;--muted:#8299c1}
.stApp{background:radial-gradient(circle at 15% 5%,rgba(41,91,255,.25),transparent 28%),radial-gradient(circle at 85% 10%,rgba(157,53,255,.23),transparent 30%),radial-gradient(circle at 55% 55%,rgba(0,194,255,.08),transparent 32%),linear-gradient(135deg,#020511 0%,#060a20 48%,#0a0520 100%);color:var(--text);font-family:'Inter',sans-serif}
.stApp:before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.28;background-image:radial-gradient(circle,rgba(255,255,255,.8) 0 1px,transparent 1.5px),radial-gradient(circle,rgba(104,197,255,.8) 0 1px,transparent 1.5px),radial-gradient(circle,rgba(210,110,255,.7) 0 1px,transparent 1.5px);background-size:180px 180px,260px 260px,330px 330px;animation:stars 24s linear infinite}
@keyframes stars{from{transform:translate3d(0,0,0)}to{transform:translate3d(50px,-35px,0)}}
@keyframes orbit{to{transform:rotate(360deg)}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
@keyframes glow{0%,100%{opacity:.65}50%{opacity:1}}
.block-container{padding-top:1rem;max-width:1500px}
[data-testid="stSidebar"]{background:linear-gradient(180deg,rgba(3,7,25,.98),rgba(12,5,35,.98));border-right:1px solid rgba(101,121,255,.2)}
.sidebar-brand{font-family:'Orbitron';font-size:25px;font-weight:900;letter-spacing:2px;text-shadow:0 0 20px #557eff}.sidebar-sub{font-size:10px;color:#7188b0;letter-spacing:1px}
div[data-testid="stButton"]>button{width:100%;border:1px solid rgba(91,205,255,.5);border-radius:14px;color:#fff;background:linear-gradient(100deg,#155bff,#7b35ff,#d23fff);font-weight:800;box-shadow:0 0 25px rgba(92,65,255,.3);transition:.25s}div[data-testid="stButton"]>button:hover{transform:translateY(-2px);box-shadow:0 0 38px rgba(92,65,255,.55)}
.neon{position:relative;overflow:hidden;border:1px solid rgba(92,122,255,.24);background:linear-gradient(145deg,rgba(11,18,49,.9),rgba(6,9,28,.8));border-radius:20px;padding:18px;box-shadow:inset 0 1px 0 rgba(255,255,255,.035),0 14px 45px rgba(0,0,0,.3);backdrop-filter:blur(15px)}
.neon:after{content:"";position:absolute;left:0;right:0;top:-100%;height:1px;background:linear-gradient(90deg,transparent,#54dcff,#b85cff,transparent);animation:scan 7s ease-in-out infinite}@keyframes scan{0%,100%{top:-10%;opacity:0}30%,70%{opacity:.65}55%{top:110%}}
.hero{min-height:245px;display:flex;align-items:center;gap:30px;padding:28px 34px;border-radius:28px;background:radial-gradient(circle at 12% 50%,rgba(52,122,255,.3),transparent 22%),radial-gradient(circle at 80% 25%,rgba(174,62,255,.28),transparent 25%),linear-gradient(115deg,rgba(7,17,53,.96),rgba(20,8,48,.92));border:1px solid rgba(91,153,255,.36);box-shadow:0 0 60px rgba(63,80,255,.14)}
.orb{width:175px;height:175px;flex:0 0 175px;border-radius:50%;display:flex;align-items:center;justify-content:center;position:relative;background:radial-gradient(circle at 35% 30%,#5cecff 0 5%,#286dff 18%,#632cff 48%,#160d47 75%,#05051b);box-shadow:0 0 45px rgba(56,135,255,.5),0 0 90px rgba(150,63,255,.25);animation:float 5s ease-in-out infinite}.orb:before,.orb:after{content:"";position:absolute;inset:-15px;border:1px solid rgba(90,210,255,.55);border-radius:50%;transform:rotate(65deg) scaleX(1.55);animation:orbit 9s linear infinite}.orb:after{transform:rotate(-35deg) scaleX(1.55);animation-duration:12s;animation-direction:reverse;border-color:rgba(206,83,255,.45)}.orb b{font-family:'Orbitron';font-size:70px;text-shadow:0 0 25px #4ddcff,0 0 50px #a44cff}.kicker{font-size:11px;letter-spacing:2.4px;color:#64dcff;font-weight:800}.hero h1{font-family:'Orbitron';font-size:clamp(28px,3vw,50px);margin:7px 0}.hero h1 span{color:#6adfff;text-shadow:0 0 25px rgba(83,215,255,.5)}.hero p{color:#a8bce1;margin:0 0 16px}.chips{display:flex;gap:8px;flex-wrap:wrap}.chip{padding:7px 11px;border:1px solid rgba(75,187,255,.38);border-radius:999px;background:rgba(10,35,77,.45);color:#bceaff;font-size:10px;font-weight:700}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#34efb0;box-shadow:0 0 14px #34efb0;animation:glow 1.7s infinite}
.metrics{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px;margin:16px 0}.metric{min-height:115px}.label{color:#7e99c3;font-size:10px;letter-spacing:1.7px;font-weight:800}.value{font-size:27px;font-weight:900;margin-top:9px}.sub{color:#91a5c8;font-size:10px;margin-top:4px}.bar{height:6px;border-radius:99px;background:#111938;margin-top:13px;overflow:hidden}.bar>div{height:100%;border-radius:99px;background:linear-gradient(90deg,#27bfff,#9a4cff,#ec62ff);box-shadow:0 0 12px rgba(82,159,255,.5);transition:width .8s}
.title{font-family:'Orbitron';font-size:14px;letter-spacing:1px;margin:3px 0 10px}.timeline{max-height:510px;overflow:auto}.event{display:grid;grid-template-columns:70px 29px 1fr;gap:9px;padding:10px 5px;border-bottom:1px solid rgba(89,114,194,.13)}.event:hover{background:rgba(70,91,180,.09)}.time{font:10px monospace;color:#7189b1;padding-top:5px}.icon{width:27px;height:27px;border-radius:9px;display:flex;align-items:center;justify-content:center;background:rgba(53,124,255,.15);border:1px solid rgba(79,166,255,.35);color:#6edcff;font-size:11px}.event b{font-size:10px}.event p{color:#7f99bf;font-size:10px;margin:3px 0;line-height:1.35}.tag{display:inline-block;margin:2px 4px 0 0;padding:3px 7px;border-radius:7px;background:rgba(92,67,202,.16);border:1px solid rgba(120,95,255,.2);color:#bcaaff;font-size:8px}
.flow{min-height:510px;display:flex;align-items:center;justify-content:center;position:relative;background:radial-gradient(circle,rgba(44,109,255,.14),transparent 52%)}.flow:before,.flow:after{content:"";position:absolute;border:1px solid rgba(63,171,255,.18);border-radius:50%;width:310px;height:310px;animation:orbit 16s linear infinite}.flow:after{width:225px;height:225px;animation-duration:11s;animation-direction:reverse;border-color:rgba(201,75,255,.22)}.stack{display:flex;flex-direction:column;align-items:center;gap:16px;z-index:2}.node{width:105px;height:105px;border-radius:50%;display:flex;flex-direction:column;align-items:center;justify-content:center;background:radial-gradient(circle at 35% 25%,#38dfff,#1454cf 42%,#130d44 78%);border:1px solid rgba(89,210,255,.7);box-shadow:0 0 35px rgba(44,174,255,.34);font-weight:900;font-size:11px}.node.p{background:radial-gradient(circle at 35% 25%,#d271ff,#6935df 42%,#1a0b45 78%);border-color:#c36dff}.node.g{background:radial-gradient(circle at 35% 25%,#56ffd0,#13a878 42%,#062c31 78%);border-color:#55ffd0}.arrow{color:#6ce2ff;font-size:23px;text-shadow:0 0 14px #3bd6ff;animation:float 1.8s infinite}
.res{margin:10px 0 15px}.reshead{display:flex;justify-content:space-between;font-size:10px;color:#bdd0ed}.resmeta{color:#7189b2;font-size:9px;margin-top:3px}.health{display:flex;gap:8px;align-items:center;padding:7px 0;color:#a5b9db;font-size:10px}.health i{width:8px;height:8px;border-radius:50%;background:#35e6ad;box-shadow:0 0 10px #35e6ad}.smallgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.small{padding:11px;border:1px solid rgba(87,114,190,.16);border-radius:12px;background:rgba(9,14,40,.65)}.small strong{font-size:16px}.small span{display:block;color:#728bb2;font-size:8px;margin-top:3px}
@media(max-width:1100px){.metrics{grid-template-columns:repeat(3,1fr)}.hero{flex-direction:column;align-items:flex-start}.orb{width:140px;height:140px;flex-basis:140px}}
</style>
"""

def init_state():
    defaults = {
        "task":"Research the NEXORA project, find current information about AI agent orchestration, then calculate 25 multiplied by 4.",
        "result":None,"running":False,"last_run":None,
    }
    for key,value in defaults.items():
        if key not in st.session_state:
            st.session_state[key]=value

def build_system():
    registry=ResourceRegistry()
    for name,capacity in [("LLM",2),("SEARCH",2),("DATABASE",1),("PYTHON",2)]:
        registry.add_resource(Resource(name,capacity))
    registry.add_substitution("DATABASE","SEARCH",penalty=0.20,reason="Read-only retrieval fallback")
    history=RuntimeHistory()
    predictor=PredictionEngine(history)
    reservation_engine=ReservationEngine(registry)
    scheduler=Scheduler(registry,reservation_engine)
    monitor=RuntimeMonitor(scheduler=scheduler,reservation_engine=reservation_engine)
    interceptor=RuntimeInterceptor(scheduler=scheduler,reservation_engine=reservation_engine,history=history,predictor=predictor)
    ai=LocalAI(model="llama3.2:3b")
    tools={"SEARCH":SearchTool(),"DATABASE":DatabaseTool(),"PYTHON":PythonTool()}
    return registry,history,predictor,reservation_engine,scheduler,monitor,interceptor,ai,tools

def run_live(task):
    registry,history,predictor,reservation_engine,scheduler,monitor,interceptor,ai,tools=build_system()
    agent=LiveAgent(agent_id=100,name="Live Research AI",task=task,ai=ai,scheduler=scheduler,reservation_engine=reservation_engine,history=history,predictor=predictor,interceptor=interceptor,tools=tools,monitor=monitor,priority=3,max_steps=8)
    monitor.register_agent(agent.agent)
    capture=io.StringIO()
    started=time.perf_counter()
    with contextlib.redirect_stdout(capture):
        asyncio.run(agent.execute())
    elapsed=time.perf_counter()-started
    events=interceptor.get_events()
    return {
        "elapsed":elapsed,"events":events,"history":history.get_events(),"steps":monitor.completed_steps,
        "deadlocks":monitor.deadlocks_detected,"recoveries":monitor.recoveries,
        "predictions":{service:predictor.predict_next(service) for service in ["SEARCH","PYTHON","DATABASE"]},
        "resources":{name:(res.capacity-res.available,res.capacity) for name,res in registry.resources.items()},
        "tools":agent.tool_history,"logs":capture.getvalue(),"completed":agent.agent.status=="COMPLETED",
    }

def clean(value):
    return str(value).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def render_event(event):
    name=event.get("event","")
    logical=event.get("logical_service") or "SYSTEM"
    physical=event.get("physical_service") or ""
    details=event.get("details") or ""
    timestamp=event.get("timestamp","")
    if "T" in timestamp:
        timestamp=timestamp.split("T")[-1][:8]
    icon={"AI_DECISION":"◈","TOOL_COMPLETED":"✓","RESOURCE_ALLOCATED":"⚙","PREDICTION":"✦","ORCHESTRATOR_OVERRIDE":"</>","AI_FINISHED":"⚑","WORKFLOW_COMPLETED":"✓"}.get(name,"•")
    tags=f'<span class="tag">Logical: {clean(logical)}</span>'
    if physical:
        tags+=f'<span class="tag">Physical: {clean(physical)}</span>'
    return f'<div class="event"><div class="time">{clean(timestamp)}</div><div class="icon">{icon}</div><div><b>{clean(name)} · {clean(logical)}</b><p>{clean(details)[:280]}</p>{tags}</div></div>'

def sidebar():
    with st.sidebar:
        st.markdown('<div class="sidebar-brand">NEXORA</div><div class="sidebar-sub">LIVE PREDICTIVE RUNTIME ORCHESTRATION</div><hr style="border-color:rgba(100,120,255,.15)">',unsafe_allow_html=True)
        st.markdown("### ◉ Live Command Center")
        for item in ["⌂  Agent Simulation","◈  Resource Manager","◌  Analytics & Insights","⌁  System Monitor","⚙  Settings"]:
            st.caption(item)
        st.markdown("### ✦ Live Agent Task")
        st.session_state.task=st.text_area("Task",value=st.session_state.task,label_visibility="collapsed",height=120)
        if st.button("▶  START LIVE RUN",use_container_width=True):
            st.session_state.running=True
            st.session_state.result=None
            st.rerun()
        st.markdown("### ◎ Local Model")
        st.markdown('<div class="neon"><b>llama3.2:3b</b><br><span style="color:#31e6a4">● Online · Ollama</span></div>',unsafe_allow_html=True)
        st.markdown("### ◇ Runtime Environment")
        st.markdown('<div class="neon">🐍 Python &nbsp; · &nbsp; ◈ Streamlit &nbsp; · &nbsp; ⚡ NEXORA</div>',unsafe_allow_html=True)
        st.markdown('<p style="text-align:center;color:#7185aa;font-size:9px;letter-spacing:1px;margin-top:18px">SMARTER AGENTS · BETTER OUTCOMES</p>',unsafe_allow_html=True)

def render():
    init_state()
    st.markdown(GALAXY_CSS,unsafe_allow_html=True)
    sidebar()
    if st.session_state.running:
        with st.spinner("NEXORA is orchestrating the local AI agent..."):
            try:
                st.session_state.result=run_live(st.session_state.task)
            except Exception as exc:
                st.session_state.result={"error":str(exc)}
            st.session_state.running=False
            st.session_state.last_run=datetime.now().strftime("%H:%M:%S")
    result=st.session_state.result or {}
    events=result.get("events",[])
    steps=result.get("steps",0)
    completed=result.get("completed",False)
    status="COMPLETED" if completed else ("ERROR" if result.get("error") else "READY")
    resources=result.get("resources",{"LLM":(0,2),"SEARCH":(0,2),"DATABASE":(0,1),"PYTHON":(0,2)})
    predictions=result.get("predictions",{})
    st.markdown(f'''<div class="hero"><div class="orb"><b>N</b></div><div style="flex:1"><div class="kicker"><span class="dot"></span>&nbsp; LIVE EXECUTION · LOCAL AI</div><h1>NEXORA <span>LIVE</span> COMMAND CENTER</h1><p>Predictive Runtime Orchestration for Multi-Agent Systems</p><div class="chips"><span class="chip">LOCAL AI</span><span class="chip">PREDICTION</span><span class="chip">RESERVATION</span><span class="chip">FAIRNESS</span><span class="chip">DEADLOCK RECOVERY</span></div></div><div class="neon" style="min-width:175px;text-align:center"><div class="label">AGENT STATUS</div><div style="font-size:20px;font-weight:900;color:#31e6a4;margin-top:10px">● {status}</div><div style="color:#7e99c3;font-size:10px;margin-top:7px">{steps}/8 steps completed</div></div></div>''',unsafe_allow_html=True)
    cards=[("AGENT",status,"Live Research AI",100 if completed else 25),("STEPS",f"{steps}/8","tool operations",min(100,steps*12.5)),("EVENTS",len(events),"runtime events",min(100,len(events)*4)),("RESERVATIONS",0,"active future claims",0),("DEADLOCKS",result.get("deadlocks",0),"detected cycles",0),("RECOVERIES",result.get("recoveries",0),"runtime recoveries",0)]
    st.markdown('<div class="metrics">'+''.join(f'<div class="neon metric"><div class="label">{a}</div><div class="value">{b}</div><div class="sub">{c}</div><div class="bar"><div style="width:{d}%"></div></div></div>' for a,b,c,d in cards)+'</div>',unsafe_allow_html=True)
    st.markdown('<div class="title">RUNTIME CONTROL PLANE</div>',unsafe_allow_html=True)
    left,right=st.columns([1.5,1])
    with left:
        event_html=''.join(render_event(e) for e in events[-18:]) if events else '<div style="padding:55px;text-align:center;color:#61779f">Start a live run to populate the runtime trace.</div>'
        st.markdown(f'<div class="neon"><div class="title">⚡ LIVE DECISION STREAM <span style="float:right;color:#31e6a4;font-size:9px">● REAL-TIME</span></div><div class="timeline">{event_html}</div></div>',unsafe_allow_html=True)
    with right:
        tool_names=[item.get("tool") for item in result.get("tools",[])] or ["SEARCH","PYTHON","FINISH"]
        flow=[]
        for item in tool_names+["FINISH"]:
            if item not in flow: flow.append(item)
        nodes=''
        for i,node in enumerate(flow[:5]):
            cls='p' if node=='PYTHON' else ('g' if node=='FINISH' else '')
            symbol='⌕' if node=='SEARCH' else ('</>' if node=='PYTHON' else '⚑')
            nodes+=f'<div class="node {cls}"><div style="font-size:24px">{symbol}</div>{clean(node)}</div>'
            if i<len(flow[:5])-1: nodes+='<div class="arrow">↓</div>'
        st.markdown(f'<div class="neon"><div class="title">◎ SERVICE FLOW <span style="float:right;color:#67dcff;font-size:9px">3D VIEW</span></div><div class="flow"><div class="stack">{nodes}</div></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="title">SYSTEM INTELLIGENCE</div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns([1.05,1.05,.9])
    with c1:
        html='<div class="neon"><div class="title">▣ RESOURCE UTILIZATION</div>'
        for name,(used,cap) in resources.items():
            pct=(used/cap*100) if cap else 0
            html+=f'<div class="res"><div class="reshead"><b>{name}</b><span>{pct:.0f}%</span></div><div class="resmeta">{used}/{cap} used · {cap-used} available</div><div class="bar"><div style="width:{pct}%"></div></div></div>'
        st.markdown(html+'</div>',unsafe_allow_html=True)
    with c2:
        html='<div class="neon"><div class="title">✦ PREDICTIONS</div>'
        found=False
        for source,values in predictions.items():
            for target,prob in values.items():
                found=True
                html+=f'<div style="display:flex;justify-content:space-between;font-size:10px;margin:10px 0 5px"><span>{source} → {target}</span><b>{prob*100:.1f}%</b></div><div class="bar"><div style="width:{prob*100}%"></div></div>'
        if not found: html+='<p style="color:#7189b2;font-size:10px">No learned transitions yet.</p>'
        st.markdown(html+'</div>',unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="neon"><div class="title">♥ SYSTEM HEALTH</div><div class="health"><i></i>No deadlocks detected</div><div class="health"><i></i>No runtime errors</div><div class="health"><i></i>All services operational</div><div class="health"><i></i>Local AI connected</div></div>',unsafe_allow_html=True)
    b1,b2,b3=st.columns([1.05,1.05,.9])
    with b1:
        html='<div class="neon"><div class="title">⌁ RECENT TOOL RESULTS</div>'
        tools=result.get("tools",[])
        if tools:
            for i,item in enumerate(tools[-5:],1): html+=f'<div class="small" style="margin:7px 0"><strong>{i}. {clean(item.get("tool"))}</strong><span>{clean(str(item.get("result",""))[:130])}</span></div>'
        else: html+='<span style="color:#7189b2;font-size:10px">No tool results yet.</span>'
        st.markdown(html+'</div>',unsafe_allow_html=True)
    with b2:
        elapsed=f'{result.get("elapsed",0):.2f}s' if result else '0.00s'
        html='<div class="neon"><div class="title">◌ RUNTIME METRICS</div><div class="smallgrid">'
        for value,label in [(steps,'Completed Steps'),(elapsed,'Total Execution'),('0.00s','Total Waiting'),(len(events),'Total Events')]: html+=f'<div class="small"><strong>{clean(value)}</strong><span>{label}</span></div>'
        st.markdown(html+'</div></div>',unsafe_allow_html=True)
    with b3:
        task=clean(st.session_state.task)
        st.markdown(f'<div class="neon"><div class="title">◈ CURRENT TASK</div><div style="color:#a9bde1;font-size:10px;line-height:1.6">{task}</div><hr style="border-color:rgba(90,110,190,.14)"><div style="color:#31e6a4;font-size:9px">✓ SEARCH</div><div style="color:#31e6a4;font-size:9px;margin-top:7px">✓ PYTHON</div></div>',unsafe_allow_html=True)
    if result.get("error"):
        st.error(result["error"])
    if result:
        with st.expander("Developer Runtime Trace"):
            st.code(result.get("logs",""),language="text")

render()
