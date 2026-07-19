"""Streamlit adapter for Kaun Banega CHRO. Thin: all logic lives in core/.

Run: streamlit run ui/streamlit_app.py
"""
from __future__ import annotations

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

BANK_PATH = ROOT / "data" / "question_bank.json"

TEAL = "#0F766E"
CHARCOAL = "#36454F"
ACCENT = "#E6F2F0"
GOLD = "#D4AF37"
BLUE = "#0B2E63"

REVEAL_SUSPENSE_SECONDS = 1.5


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{ background: linear-gradient(160deg, {BLUE} 0%, {CHARCOAL} 100%); }}
        .kbc-title {{ color: {GOLD}; font-weight: 800; letter-spacing: 1px; }}
        .kbc-card {{ background: {ACCENT}; color: {CHARCOAL}; border-radius: 12px;
                     padding: 16px 20px; border-left: 6px solid {TEAL}; }}
        .ladder-row {{ padding: 6px 12px; margin: 3px 0; border-radius: 8px;
                       font-weight: 600; color: #DDE7E5; border: 1px solid transparent; }}
        .ladder-current {{ background: {GOLD}; color: {BLUE}; border-color: {GOLD}; }}
        .ladder-done {{ background: {TEAL}; color: white; }}
        .ladder-future {{ opacity: 0.55; }}
        .ladder-safe {{ border-color: {GOLD}; }}
        .answer-default div.stButton > button {{
            background: linear-gradient(180deg, #123a7a, {BLUE}); color: white;
            border: 2px solid {GOLD}; border-radius: 26px; width: 100%; text-align: left;
            padding: 12px 18px; font-weight: 600; }}
        .box-selected div.stButton > button {{ background: {GOLD} !important; color: {BLUE} !important; }}
        .box-correct div.stButton > button {{ background: #1B8A3A !important; border-color: #1B8A3A !important; }}
        .box-wrong div.stButton > button {{ background: #B3261E !important; border-color: #B3261E !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def new_game(contestant_id: str) -> None:
    bank = load_bank(BANK_PATH)
    seed = seed_for(contestant_id or "guest", counter=st.session_state.get("game_counter", 0))
    st.session_state["game_counter"] = st.session_state.get("game_counter", 0) + 1
    round_qs = draw_round(bank, seed, contestant_id or "guest")
    eng = GameEngine(round_qs, seed=seed)
    eng.start_round()
    st.session_state["engine"] = eng
    st.session_state["contestant_id"] = contestant_id


def countdown_widget(remaining: float) -> None:
    secs = int(remaining)
    components.html(
        f"""
        <div id="kbc-timer" style="font:700 42px monospace;color:{GOLD};text-align:center;">
          {secs:02d}
        </div>
        <script>
          let r = {secs};
          const el = document.getElementById('kbc-timer');
          const iv = setInterval(() => {{
            r -= 1;
            if (r < 0) {{ clearInterval(iv); el.textContent = 'TIME UP'; el.style.color = '#B3261E'; return; }}
            el.textContent = String(r).padStart(2,'0');
          }}, 1000);
        </script>
        """,
        height=70,
    )


def render_ladder(state) -> None:
    st.markdown(f"<div class='kbc-title'>Designation Ladder</div>", unsafe_allow_html=True)
    for row in view.ladder_rows(state):
        cls = f"ladder-row ladder-{row['state']}" + (" ladder-safe" if row["safe_haven"] else "")
        safe = " (safe haven)" if row["safe_haven"] else ""
        st.markdown(
            f"<div class='{cls}'>{row['rung']}. {row['title']}{safe}</div>",
            unsafe_allow_html=True,
        )


def render_answers(eng) -> None:
    state = eng.state
    for box in view.answer_boxes(state):
        if box["hidden"]:
            st.markdown("<div class='ladder-row ladder-future'>&nbsp;</div>", unsafe_allow_html=True)
            continue
        wrapper = {"default": "answer-default", "selected": "answer-default box-selected",
                   "correct": "answer-default box-correct", "wrong": "answer-default box-wrong"}[box["box_state"]]
        st.markdown(f"<div class='{wrapper}'>", unsafe_allow_html=True)
        disabled = state.revealed or state.locked
        if st.button(f"{box['letter']}.  {box['text']}", key=f"opt{box['index']}", disabled=disabled):
            eng.select(box["index"])
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render_lifelines(eng) -> None:
    cols = st.columns(3)
    for col, ll in zip(cols, view.lifeline_states(eng.state)):
        with col:
            if st.button(ll["label"], key=f"ll_{ll['name']}",
                         disabled=ll["used"] or eng.state.revealed):
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
    if st.sidebar.button("Next question", disabled=not (s.revealed and s.last_correct and s.status == "running")):
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
    locked = s.locked
    if st.sidebar.button("Lock kiya jaye (lock answer)", disabled=locked or s.selected_index is None or s.revealed):
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
    with st.spinner("Lock kiya jaye... revealing"):
        time.sleep(REVEAL_SUSPENSE_SECONDS)
    reveal_fn()
    st.rerun()


def render_explanation(eng) -> None:
    card = eng.explanation()
    code = f"<pre style='margin-top:8px;'>{card['code']}</pre>" if card["code"] else ""
    st.markdown(
        f"<div class='kbc-card'><b>Correct answer:</b> {card['correct_option']}"
        f" &nbsp;|&nbsp; <i>{card['library']}</i><br><br>{card['why']}{code}</div>",
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Kaun Banega CHRO", layout="wide")
    inject_css()
    st.markdown("<h1 class='kbc-title'>Kaun Banega CHRO</h1>", unsafe_allow_html=True)

    if "engine" not in st.session_state:
        st.write("Enter a contestant id and start the hot seat.")
        cid = st.text_input("Contestant id", value="contestant-1")
        if st.button("Start game"):
            new_game(cid)
            st.rerun()
        return

    eng = st.session_state["engine"]
    s = eng.state

    render_lifelines(eng)
    st.divider()

    play, ladder = st.columns([2, 1])
    with ladder:
        render_ladder(s)
    with play:
        if s.status == "won":
            st.markdown("<h2 class='kbc-title'>CHRO. Top of the ladder.</h2>", unsafe_allow_html=True)
            render_explanation(eng)
        elif s.status == "lost":
            st.markdown(
                f"<h2 class='kbc-title'>Run over. Final designation: {eng.final_designation()}</h2>",
                unsafe_allow_html=True,
            )
            render_explanation(eng)
        else:
            q = s.current_question
            tp = view.timer_payload(eng)
            if tp["timed"] and not s.revealed and tp["running"]:
                countdown_widget(tp["remaining"])
            elif tp["timed"] and not tp["running"] and not s.revealed:
                st.markdown(f"<div class='kbc-title'>Timer paused: {int(tp['remaining'])}s</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='kbc-card'><b>Rung {s.current_rung}.</b> {q.question}</div>", unsafe_allow_html=True)
            st.write("")
            render_answers(eng)
            if s.revealed:
                render_explanation(eng)

    render_host_panel(eng)


if __name__ == "__main__":
    main()
