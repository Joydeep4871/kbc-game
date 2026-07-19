"""Streamlit adapter for Kaun Banega CHRO.

Thin: all game logic lives in core/. This file is theWho Wants To Be A Millionaire /
KBC-style presentation layer: a centered studio stage, a 2x2 answer grid, the
"Lock kiya jaye?" beat, the designation ladder, and the host control sidebar.

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

TEAL = "#0F766E"
CHARCOAL = "#36454F"
ACCENT = "#E6F2F0"
GOLD = "#D4AF37"
BLUE = "#0B2E63"

REVEAL_SUSPENSE_SECONDS = 1.6


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{ background: radial-gradient(circle at 50% 0%, {BLUE} 0%, {CHARCOAL} 100%); }}
        .block-container {{ padding-top: 1rem; }}

        .kbc-title {{
            color: {GOLD}; font-weight: 800; letter-spacing: 2px;
            text-align: center; margin-bottom: 0.2rem;
        }}
        .kbc-sub {{ color: #C9D4DC; text-align: center; font-size: 0.85rem; margin-bottom: 0.8rem; }}

        /* Lifeline buttons, targeted by Streamlit's per-key wrapper class. */
        [class*="st-key-ll_"] button {{
            background: linear-gradient(180deg, #1b3a6b, {BLUE}) !important;
            color: {GOLD} !important; border: 1px solid {GOLD} !important;
            border-radius: 24px !important; width: 100% !important;
            min-height: 44px !important; font-weight: 700 !important;
        }}
        [class*="st-key-ll_"] button:disabled {{ opacity: 0.4 !important; }}

        .stage {{ background: rgba(0,0,0,0.18); border: 1px solid rgba(212,175,55,0.35);
                 border-radius: 14px; padding: 18px; }}

        .kbc-card {{ background: {ACCENT}; color: {CHARCOAL}; border-radius: 12px;
                     padding: 16px 20px; border-left: 6px solid {TEAL}; }}

        .qtext {{ color: white; font-weight: 700; font-size: 1.25rem; text-align: center;
                  margin: 10px 0 18px 0; }}

        /* 2x2 answer board. Base look for every answer button; per-state
           colors (selected/correct/wrong) are injected each render below. */
        [class*="st-key-opt"] button {{
            background: linear-gradient(180deg, #123a7a, {BLUE}) !important;
            color: white !important; border: 2px solid {GOLD} !important;
            border-radius: 14px !important; width: 100% !important; min-height: 66px !important;
            text-align: left !important; padding: 12px 18px !important;
            font-weight: 600 !important; font-size: 1.02rem !important; line-height: 1.3 !important;
            white-space: normal !important;
        }}
        .ans-hidden {{ min-height: 66px; }}

        .lockbeat {{ text-align: center; color: {GOLD}; font-weight: 800; font-size: 1.4rem;
                     letter-spacing: 1px; margin: 14px 0; padding: 10px;
                     border: 2px dashed {GOLD}; border-radius: 10px; }}

        .ladder-wrap {{ background: rgba(0,0,0,0.25); border-radius: 12px; padding: 12px; }}
        .ladder-row {{ padding: 7px 12px; margin: 4px 0; border-radius: 8px;
                       font-weight: 700; color: #DDE7E5; border: 1px solid transparent;
                       display: flex; justify-content: space-between; }}
        .ladder-current {{ background: {GOLD}; color: {BLUE}; border-color: {GOLD}; }}
        .ladder-done {{ background: {TEAL}; color: white; }}
        .ladder-future {{ opacity: 0.5; }}

        .endcard {{ text-align: center; padding: 24px; }}
        .endcard h2 {{ color: {GOLD}; }}
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


def countdown_widget(remaining: float) -> None:
    secs = int(remaining)
    components.html(
        f"""
        <div style="font:800 44px monospace;color:{GOLD};text-align:center;">
          {secs:02d}
        </div>
        <script>
          let r = {secs};
          const el = document.currentScript.previousElementSibling;
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
    st.markdown("<div class='kbc-title' style='font-size:1rem;'>Designation Ladder</div>",
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
        "selected": f"background:{GOLD}!important;color:{BLUE}!important;",
        "correct": "background:#1B8A3A!important;border-color:#1B8A3A!important;color:#fff!important;",
        "wrong": "background:#B3261E!important;border-color:#B3261E!important;color:#fff!important;",
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


def main() -> None:
    st.set_page_config(page_title="Kaun Banega CHRO", layout="wide")
    inject_css()
    st.markdown("<h1 class='kbc-title'>Kaun Banega CHRO</h1>", unsafe_allow_html=True)
    st.markdown("<div class='kbc-sub'>Who will become Chief Human Resources Officer?</div>",
                unsafe_allow_html=True)

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
        st.markdown("<div class='ladder-wrap'>", unsafe_allow_html=True)
        render_ladder(s)
        st.markdown("</div>", unsafe_allow_html=True)

    with play:
        st.markdown("<div class='stage'>", unsafe_allow_html=True)
        if s.status == "won":
            st.markdown("<div class='endcard'><h2>CHRO. Top of the ladder.</h2>"
                        "<p>You became Chief Human Resources Officer.</p></div>",
                        unsafe_allow_html=True)
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
            if tp["timed"] and not s.revealed and tp["running"]:
                countdown_widget(tp["remaining"])
            elif tp["timed"] and not tp["running"] and not s.revealed:
                st.markdown(f"<div class='kbc-title'>Timer paused: {int(tp['remaining'])}s</div>",
                            unsafe_allow_html=True)
            st.markdown(f"<div class='qtext'>Rung {s.current_rung}. {q.question}</div>",
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
