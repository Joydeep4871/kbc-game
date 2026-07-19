"""Streamlit adapter for Kaun Banega CHRO.

Thin: all game logic lives in core/. This file is theWho Wants To Be A Millionaire /
KBC-style presentation layer: a centered studio stage, a 2x2 answer grid, the
"Lock kiya jaye?" beat, the designation ladder, and the host control sidebar.

Run: streamlit run ui/streamlit_app.py
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# Allow `streamlit run ui/streamlit_app.py` from the repo root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import lifelines
from core.game_engine import GameEngine
from core.question_bank import draw_round, load_bank, seed_for
from ui import app_interface as view

# Gameshow palette (WWTBAM / KBC look), overriding the earlier teal deck theme.
GOLD = "#FFD700"          # letter indicators, title, lifeline badges
ORANGE = "#FFA500"        # lock-in fill and money-tree highlight
GREEN = "#32CD32"         # correct reveal
RED = "#DC143C"           # wrong reveal
BORDER = "#8BB8E8"        # metallic light-blue box outline
BOX_FILL = "#040914"      # near-black box fill
LIGHT_BLUE = "#ADD8E6"    # future money-tree rungs
WHITE = "#FFFFFF"
BG_CENTER = "#0F1B4C"     # radial gradient centre
BG_EDGE = "#000000"       # radial gradient edge
FONT = '"Copperplate", "Copperplate Gothic Bold", "Trajan Pro", "Bookman Old Style", Georgia, serif'

# Legacy aliases still referenced elsewhere in the module.
BLUE = BG_CENTER
TEAL = "#0F766E"
CHARCOAL = "#36454F"
ACCENT = "#E6F2F0"

# The signature suspense beat before a reveal (the show stretches 2-4 seconds).
REVEAL_SUSPENSE_SECONDS = 2.5

# Elongated-hexagon "lozenge" used for question and answer boxes.
LOZENGE = "polygon(3% 0, 97% 0, 100% 50%, 97% 100%, 3% 100%, 0 50%)"


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{ background: radial-gradient(ellipse at 50% 32%, {BG_CENTER} 0%, {BG_EDGE} 72%); }}
        .block-container {{ padding-top: 1rem; }}

        .kbc-title {{
            color: {GOLD}; font-family: {FONT}; font-weight: 800; letter-spacing: 3px;
            text-align: center; text-transform: uppercase; margin-bottom: 0.2rem;
            text-shadow: 0 0 18px rgba(255,215,0,0.35);
        }}
        .kbc-sub {{ color: {LIGHT_BLUE}; font-family: {FONT}; text-align: center;
                    letter-spacing: 1px; text-transform: uppercase;
                    font-size: 0.8rem; margin-bottom: 1rem; }}

        /* Lifeline oval badges. */
        [class*="st-key-ll_"] button {{
            background: radial-gradient(circle, #12213f 0%, {BG_EDGE} 100%) !important;
            color: {GOLD} !important; border: 2px solid {GOLD} !important;
            border-radius: 50% / 60% !important; width: 100% !important;
            min-height: 54px !important; font-family: {FONT} !important;
            font-weight: 700 !important; letter-spacing: 1px !important;
            text-transform: uppercase !important; position: relative !important;
        }}
        [class*="st-key-ll_"] button:disabled {{ opacity: 0.55 !important; color: #7a7a7a !important; }}
        /* Red X over a used lifeline, as on the show. */
        [class*="st-key-ll_"] button:disabled::after {{
            content: "X"; position: absolute; inset: 0; display: flex;
            align-items: center; justify-content: center;
            color: {RED}; font-size: 2.2rem; font-weight: 900; opacity: 0.85;
        }}

        .stage {{ background: transparent; padding: 6px; }}

        .kbc-card {{ background: {BOX_FILL}; color: {WHITE}; border: 2px solid {BORDER};
                     border-radius: 10px; padding: 16px 20px; }}
        .kbc-card b {{ color: {GOLD}; }}

        /* Question box: a wide hexagon lozenge. Outer div paints the light-blue
           outline; inner div paints the near-black fill inset by the padding. */
        .qbox {{ background: {BORDER}; clip-path: {LOZENGE}; padding: 2px; margin: 8px 0 22px 0; }}
        .qinner {{ background: {BOX_FILL}; clip-path: {LOZENGE}; color: {WHITE};
                   font-family: {FONT}; font-weight: 700; font-size: 1.18rem;
                   letter-spacing: 1px; text-transform: uppercase; text-align: center;
                   padding: 20px 52px; }}

        /* Answer board: same two-layer lozenge trick applied to Streamlit buttons. */
        [class*="st-key-opt"] {{ background: {BORDER}; clip-path: {LOZENGE};
                                 padding: 2px; margin-bottom: 12px; }}
        [class*="st-key-opt"] button {{
            clip-path: {LOZENGE} !important; background: {BOX_FILL} !important;
            color: {WHITE} !important; border: none !important; border-radius: 0 !important;
            width: 100% !important; min-height: 72px !important;
            text-align: center !important; padding: 12px 40px !important;
            font-family: {FONT} !important; font-weight: 700 !important;
            font-size: 1.02rem !important; letter-spacing: 1px !important;
            text-transform: uppercase !important; white-space: normal !important;
            line-height: 1.25 !important;
        }}
        .ans-hidden {{ min-height: 76px; }}

        .lockbeat {{ text-align: center; color: {ORANGE}; font-family: {FONT}; font-weight: 800;
                     font-size: 1.35rem; letter-spacing: 2px; text-transform: uppercase;
                     margin: 14px 0; padding: 10px; border: 2px dashed {ORANGE}; border-radius: 8px; }}

        /* Money tree. Only the current rung is a glowing orange lozenge. */
        .ladder-wrap {{ background: transparent; padding: 6px; }}
        .ladder-title {{ color: {GOLD}; font-family: {FONT}; text-transform: uppercase;
                         letter-spacing: 2px; text-align: center; margin-bottom: 8px; }}
        .ladder-row {{ font-family: {FONT}; text-transform: uppercase; letter-spacing: 1px;
                       padding: 6px 14px; margin: 5px 0; font-weight: 700;
                       display: flex; justify-content: space-between; }}
        .ladder-current {{ background: {ORANGE}; color: #000; clip-path: {LOZENGE};
                           animation: kbcPulse 1.2s ease-in-out infinite; }}
        .ladder-done {{ color: {ORANGE}; }}
        .ladder-future {{ color: {LIGHT_BLUE}; opacity: 0.7; }}
        @keyframes kbcPulse {{ 0%,100% {{ filter: brightness(1); }} 50% {{ filter: brightness(1.35); }} }}

        .endcard {{ text-align: center; padding: 24px; }}
        .endcard h2 {{ color: {GOLD}; font-family: {FONT}; text-transform: uppercase; letter-spacing: 2px; }}

        /* Landing screen. */
        .kbc-logo {{ text-align: center; margin: 2px 0 4px 0; }}
        .kbc-logo svg {{ width: min(340px, 68vw); height: auto;
                         animation: kbcHalo 4s ease-in-out infinite; }}
        @keyframes kbcHalo {{ 0%,100% {{ filter: drop-shadow(0 0 16px rgba(255,215,0,0.30)); }}
                              50% {{ filter: drop-shadow(0 0 34px rgba(255,165,0,0.55)); }} }}
        .flavor {{ text-align: center; color: {LIGHT_BLUE}; font-family: {FONT};
                   text-transform: uppercase; letter-spacing: 2px; line-height: 1.75;
                   font-size: 0.86rem; margin: 8px auto 20px auto; max-width: 620px; }}
        .flavor .big {{ color: {GOLD}; font-size: 1.15rem; display: block; margin-bottom: 8px;
                        text-shadow: 0 0 16px rgba(255,215,0,0.4); }}
        .flavor .cue {{ color: {ORANGE}; display: block; margin-top: 10px; letter-spacing: 3px; }}
        .landing-hint {{ text-align: center; color: #9fb3c8; font-family: {FONT};
                         text-transform: uppercase; letter-spacing: 1px; font-size: 0.72rem;
                         margin: 6px 0 2px 0; }}
        [class*="st-key-startbtn"] button {{
            background: linear-gradient(180deg, {GOLD}, {ORANGE}) !important; color: #0B1B3A !important;
            border: 2px solid {GOLD} !important; border-radius: 30px !important; min-height: 56px !important;
            font-family: {FONT} !important; font-weight: 800 !important; letter-spacing: 2px !important;
            text-transform: uppercase !important; box-shadow: 0 0 22px rgba(255,215,0,0.4) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def new_game(contestant_id: str) -> None:
    bank = load_bank(ROOT / "data" / "question_bank.json")
    seed = seed_for(contestant_id or "guest", counter=st.session_state.get("game_counter", 0))
    st.session_state["game_counter"] = st.session_state.get("game_counter", 0) + 1
    round_qs = draw_round(bank, seed, contestant_id or "guest")
    eng = GameEngine(round_qs, seed=seed)
    eng.start_round()
    st.session_state["engine"] = eng
    st.session_state["contestant_id"] = contestant_id


def countdown_widget(remaining: float, running: bool) -> None:
    """Always rendered while a rung is timed. Ticks only when running; when the
    timer is paused it shows the frozen value in orange and starts no interval.
    Rendered unconditionally (never swapped for another element type) so the
    iframe cannot be left ticking after a pause."""
    secs = int(remaining)
    color = GOLD if running else ORANGE
    tick = "true" if running else "false"
    components.html(
        f"""
        <div id="kbctimer" style="font:800 44px monospace;color:{color};text-align:center;">
          {secs:02d}{'' if running else ' (STOPPED)'}
        </div>
        <script>
          let r = {secs};
          const el = document.getElementById('kbctimer');
          if ({tick}) {{
            const iv = setInterval(() => {{
              r -= 1;
              if (r < 0) {{ clearInterval(iv); el.textContent = 'TIME UP'; el.style.color = '{RED}'; return; }}
              el.textContent = String(r).padStart(2, '0');
            }}, 1000);
          }}
        </script>
        """,
        height=70,
    )


def win_celebration() -> None:
    """Self-contained confetti burst, marquee lights, and a glowing CHRO title."""
    components.html(
        """
        <div id="cel">
          <canvas id="cfx"></canvas>
          <div class="marquee"></div>
          <div class="wrap">
            <div class="crown">CHRO</div>
            <div class="tag">TOP OF THE LADDER</div>
            <div class="sub">You became Chief Human Resources Officer</div>
          </div>
        </div>
        <style>
          #cel{position:relative;height:300px;overflow:hidden;border-radius:14px;
               background:radial-gradient(ellipse at 50% 28%,#12225a 0%,#000 75%);}
          #cfx{position:absolute;inset:0;width:100%;height:100%;z-index:1;}
          .wrap{position:relative;z-index:2;text-align:center;padding-top:72px;
                font-family:"Copperplate","Trajan Pro","Bookman Old Style",Georgia,serif;}
          .crown{font-size:76px;font-weight:900;letter-spacing:8px;color:#FFD700;
                 text-transform:uppercase;animation:glow 1.1s ease-in-out infinite;}
          .tag{font-size:26px;letter-spacing:6px;color:#FFA500;text-transform:uppercase;margin-top:4px;}
          .sub{color:#ADD8E6;letter-spacing:2px;text-transform:uppercase;font-size:12px;margin-top:12px;}
          @keyframes glow{0%,100%{text-shadow:0 0 12px #FFD700,0 0 24px #FFA500;}
                          50%{text-shadow:0 0 28px #FFFFFF,0 0 52px #FFD700;}}
          .marquee{position:absolute;inset:6px;border-radius:12px;z-index:1;pointer-events:none;
                   background:
                     repeating-linear-gradient(90deg,#FFD700 0 8px,transparent 8px 34px) top/100% 7px no-repeat,
                     repeating-linear-gradient(90deg,#FFD700 0 8px,transparent 8px 34px) bottom/100% 7px no-repeat,
                     repeating-linear-gradient(0deg,#FFD700 0 8px,transparent 8px 34px) left/7px 100% no-repeat,
                     repeating-linear-gradient(0deg,#FFD700 0 8px,transparent 8px 34px) right/7px 100% no-repeat;
                   animation:blink .5s steps(2) infinite;opacity:.8;}
          @keyframes blink{50%{opacity:.22;}}
        </style>
        <script>
          const c=document.getElementById('cfx'),x=c.getContext('2d');
          function rz(){c.width=c.offsetWidth;c.height=c.offsetHeight;}rz();
          const cols=['#FFD700','#FFA500','#32CD32','#8BB8E8','#FFFFFF','#DC143C'];
          let P=[];
          function burst(n){for(let i=0;i<n;i++){P.push({
            x:c.width/2,y:c.height/3,vx:(Math.random()-.5)*11,vy:Math.random()*-10-2,
            g:.18+Math.random()*.12,s:4+Math.random()*5,col:cols[i%cols.length],
            rot:Math.random()*6,vr:(Math.random()-.5)*.4});}}
          function rain(){P.push({x:Math.random()*c.width,y:-10,vx:(Math.random()-.5)*2,
            vy:2+Math.random()*3,g:.03,s:4+Math.random()*4,
            col:cols[Math.floor(Math.random()*cols.length)],rot:Math.random()*6,vr:(Math.random()-.5)*.3});}
          burst(180);
          let t=0;
          function loop(){x.clearRect(0,0,c.width,c.height);
            if(t<240&&t%3==0)rain();t++;
            P.forEach(p=>{p.vy+=p.g;p.x+=p.vx;p.y+=p.vy;p.rot+=p.vr;
              x.save();x.translate(p.x,p.y);x.rotate(p.rot);
              x.fillStyle=p.col;x.fillRect(-p.s/2,-p.s/2,p.s,p.s*1.6);x.restore();});
            P=P.filter(p=>p.y<c.height+20);
            requestAnimationFrame(loop);}
          loop();
          window.addEventListener('resize',rz);
        </script>
        """,
        height=312,
    )


def render_ladder(state) -> None:
    st.markdown("<div class='ladder-title' style='font-size:1rem;'>Designation Ladder</div>",
                 unsafe_allow_html=True)
    for row in view.ladder_rows(state):
        state_cls = row["state"]
        st.markdown(
            f"<div class='ladder-row ladder-{state_cls}'>"
            f"<span>{row['rung']}. {row['title']}</span>"
            f"<span>{'▶' if state_cls=='current' else ''}</span></div>",
            unsafe_allow_html=True,
        )


def answer_state_css(boxes) -> None:
    """Color specific answer keys by state. Injected after the base rule so it wins."""
    colors = {
        "selected": f"background:{ORANGE}!important;color:#000!important;",
        "correct": f"background:{GREEN}!important;color:#000!important;",
        "wrong": f"background:{RED}!important;color:#000!important;",
    }
    rules = [
        f".st-key-opt{b['index']} button{{{colors[b['box_state']]}}}"
        for b in boxes if b["box_state"] in colors
    ]
    if rules:
        st.markdown("<style>" + "".join(rules) + "</style>", unsafe_allow_html=True)


def render_one_answer(eng, box) -> None:
    state = eng.state
    if box["hidden"]:
        st.markdown("<div class='ans-hidden'></div>", unsafe_allow_html=True)
        return
    disabled = state.revealed or state.locked
    label = f"{box['letter']}.  {box['text']}"
    if st.button(label, key=f"opt{box['index']}", disabled=disabled, use_container_width=True):
        eng.select(box["index"])
        st.rerun()


def render_answers(eng) -> None:
    boxes = view.answer_boxes(eng.state)
    answer_state_css(boxes)
    top = st.columns(2)
    bottom = st.columns(2)
    cells = [top[0], top[1], bottom[0], bottom[1]]
    for cell, box in zip(cells, boxes):
        with cell:
            render_one_answer(eng, box)


def render_lifelines(eng) -> None:
    cols = st.columns(3)
    for col, ll in zip(cols, view.lifeline_states(eng.state)):
        with col:
            if st.button(ll["label"], key=f"ll_{ll['name']}",
                         disabled=ll["used"] or eng.state.revealed,
                         use_container_width=True):
                eng.apply_lifeline(ll["name"])
                st.rerun()
    if eng.state.consulting:
        theme = "friend" if eng.state.consulting == lifelines.PHONE_A_FRIEND else "expert"
        st.info(f"Consult panel open ({theme}). Timer paused. Host resumes when ready.")
        if st.button("Close consult and resume timer"):
            eng.close_consult()
            st.rerun()


def render_host_panel(eng) -> None:
    st.sidebar.markdown("### Host Control")
    s = eng.state
    if st.sidebar.button("Next question",
                         disabled=not (s.revealed and s.last_correct and s.status == "running")):
        eng.advance()
        st.rerun()
    c1, c2 = st.sidebar.columns(2)
    if c1.button("Pause timer"):
        if eng.timer:
            eng.timer.pause()
        st.rerun()
    if c2.button("Resume timer"):
        if eng.timer:
            eng.timer.resume()
        st.rerun()
    if st.sidebar.button("Lock kiya jaye (lock answer)",
                         disabled=s.locked or s.selected_index is None or s.revealed):
        eng.lock()
        st.rerun()
    if st.sidebar.button("Reveal answer", disabled=not s.locked or s.revealed):
        _reveal_with_suspense(eng.reveal)
    c3, c4 = st.sidebar.columns(2)
    if c3.button("Force correct", disabled=s.revealed):
        _reveal_with_suspense(eng.force_correct)
    if c4.button("Force wrong", disabled=s.revealed):
        _reveal_with_suspense(eng.force_wrong)
    st.sidebar.divider()
    if st.sidebar.button("Restart game"):
        new_game(st.session_state.get("contestant_id", "guest"))
        st.rerun()


def _reveal_with_suspense(reveal_fn) -> None:
    # The signature KBC beat: a pause, then the verdict.
    with st.spinner("Lock kiya jaye... suspense builds..."):
        time.sleep(REVEAL_SUSPENSE_SECONDS)
    reveal_fn()
    st.rerun()


def render_explanation(eng) -> None:
    card = eng.explanation()
    lib = card.get("library", "")
    st.markdown(
        f"<div class='kbc-card'>"
        f"<b>Correct answer:</b> {card['correct_option']}"
        f" &nbsp;|&nbsp; <i>{lib}</i><br><br>{card['why']}</div>",
        unsafe_allow_html=True,
    )


def build_logo_svg() -> str:
    """An original KBC-style emblem: concentric gold/blue rings, a ring of
    question marks, a globe centre, and arced 'KAUN BANEGA' / 'CHRO' wording."""
    marks = []
    n = 16
    for i in range(n):
        a = (i / n) * 2 * math.pi - math.pi / 2
        x = 200 + 118 * math.cos(a)
        y = 200 + 118 * math.sin(a)
        rot = math.degrees(a) + 90
        marks.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="17" fill="#32CD32" font-weight="900" '
            f'text-anchor="middle" dominant-baseline="central" '
            f'transform="rotate({rot:.1f} {x:.1f} {y:.1f})">?</text>'
        )
    rays = []
    for i in range(28):
        a = (i / 28) * 2 * math.pi
        x1, y1 = 200 + 40 * math.cos(a), 200 + 40 * math.sin(a)
        x2, y2 = 200 + 86 * math.cos(a), 200 + 86 * math.sin(a)
        rays.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#FFD700" stroke-width="1.3" opacity="0.45"/>'
        )
    return f"""
    <svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Kaun Banega CHRO">
      <defs>
        <path id="arcTop" d="M 70,200 A 130,130 0 0 1 330,200" fill="none"/>
        <path id="arcBot" d="M 330,200 A 130,130 0 0 1 70,200" fill="none"/>
        <radialGradient id="globe" cx="50%" cy="38%" r="70%">
          <stop offset="0%" stop-color="#1b3f8f"/><stop offset="100%" stop-color="#050b1e"/>
        </radialGradient>
      </defs>
      <circle cx="200" cy="200" r="160" fill="#040914" stroke="#FFD700" stroke-width="6"/>
      <circle cx="200" cy="200" r="150" fill="none" stroke="#6CA6CD" stroke-width="2"/>
      <circle cx="200" cy="200" r="138" fill="none" stroke="#FFA500" stroke-width="1.2" opacity="0.7"/>
      {''.join(marks)}
      <circle cx="200" cy="200" r="100" fill="url(#globe)" stroke="#FFD700" stroke-width="2.5"/>
      <ellipse cx="200" cy="200" rx="100" ry="42" fill="none" stroke="#6CA6CD" stroke-width="1" opacity="0.45"/>
      <ellipse cx="200" cy="200" rx="100" ry="74" fill="none" stroke="#6CA6CD" stroke-width="1" opacity="0.35"/>
      <ellipse cx="200" cy="200" rx="42" ry="100" fill="none" stroke="#6CA6CD" stroke-width="1" opacity="0.35"/>
      <line x1="100" y1="200" x2="300" y2="200" stroke="#6CA6CD" stroke-width="1" opacity="0.45"/>
      {''.join(rays)}
      <text x="200" y="214" font-size="62" fill="#FFD700" font-weight="900" text-anchor="middle"
            font-family='Copperplate, "Trajan Pro", Georgia, serif'>?</text>
      <text font-size="30" fill="#FFD700" font-weight="800" letter-spacing="3"
            font-family='Copperplate, "Trajan Pro", Georgia, serif'>
        <textPath href="#arcTop" startOffset="50%" text-anchor="middle">KAUN BANEGA</textPath>
      </text>
      <text font-size="34" fill="#FFA500" font-weight="800" letter-spacing="8"
            font-family='Copperplate, "Trajan Pro", Georgia, serif'>
        <textPath href="#arcBot" startOffset="50%" text-anchor="middle">CHRO</textPath>
      </text>
    </svg>
    """


def render_landing() -> None:
    st.markdown(f"<div class='kbc-logo'>{build_logo_svg()}</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='flavor'>"
        "<span class='big'>Seven questions stand between you and the corner office.</span>"
        "Climb the ladder from HR Intern to Chief Human Resources Officer, "
        "one right answer at a time. Three lifelines. One hot seat. No second chances."
        "<span class='cue'>Lock kiya jaye?</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    left, mid, right = st.columns([1, 2, 1])
    with mid:
        st.markdown("<div class='landing-hint'>Take the hot seat</div>", unsafe_allow_html=True)
        cid = st.text_input("Contestant id", value="contestant-1", label_visibility="collapsed",
                            placeholder="Contestant id")
        if st.button("Start game", key="startbtn", use_container_width=True):
            new_game(cid)
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="Kaun Banega CHRO", layout="wide")
    inject_css()

    if "engine" not in st.session_state:
        render_landing()
        return

    st.markdown("<h1 class='kbc-title'>Kaun Banega CHRO</h1>", unsafe_allow_html=True)
    st.markdown("<div class='kbc-sub'>Who will become Chief Human Resources Officer?</div>",
                unsafe_allow_html=True)

    eng = st.session_state["engine"]
    s = eng.state

    render_lifelines(eng)
    st.divider()

    play, ladder = st.columns([2, 1])
    with ladder:
        st.markdown("<div class='ladder-wrap'>", unsafe_allow_html=True)
        render_ladder(s)
        st.markdown("</div>", unsafe_allow_html=True)

    with play:
        st.markdown("<div class='stage'>", unsafe_allow_html=True)
        if s.status == "won":
            win_celebration()
            render_explanation(eng)
            if st.button("Play again"):
                new_game(st.session_state.get("contestant_id", "guest"))
                st.rerun()
        elif s.status == "lost":
            st.markdown(
                f"<div class='endcard'><h2>Run over.</h2>"
                f"<p>Final designation: {eng.final_designation()}</p></div>",
                unsafe_allow_html=True,
            )
            render_explanation(eng)
            if st.button("Play again"):
                new_game(st.session_state.get("contestant_id", "guest"))
                st.rerun()
        else:
            q = s.current_question
            tp = view.timer_payload(eng)
            if tp["timed"] and not s.revealed:
                countdown_widget(tp["remaining"], tp["running"])
            st.markdown(
                f"<div class='qbox'><div class='qinner'>{q.question}</div></div>",
                unsafe_allow_html=True)
            render_answers(eng)
            if s.locked and not s.revealed:
                st.markdown("<div class='lockbeat'>LOCK KIYA JAYE? &nbsp;(final answer locked)</div>",
                            unsafe_allow_html=True)
            if s.revealed:
                render_explanation(eng)
        st.markdown("</div>", unsafe_allow_html=True)

    render_host_panel(eng)


if __name__ == "__main__":
    main()
