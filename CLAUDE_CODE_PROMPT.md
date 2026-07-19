# Inline Prompt for Claude Code: Build "Kaun Banega CHRO" (KBC)

Copy everything between the markers into Claude Code. It is self-contained. Read `PRD.md` in the same folder first if present; this prompt restates the essentials so the build works even standalone.

---

## === BEGIN PROMPT ===

You are building a classroom quiz game called **Kaun Banega CHRO (KBC)**, a "Who Wants To Be A Millionaire" style game that teaches MBA students the five Python libraries for HR analytics. The repo root already contains `PRD.md`, `question_bank.json`, and `CAPABILITIES.md`. Read `PRD.md` and `question_bank.json` before writing code.

### Hard constraints (do not violate)
1. **Agnostic core.** All game logic lives in `core/` as pure Python with NO import from any UI framework (no streamlit, no flask, no fastapi at the core layer). The UI is a thin adapter.
2. **Two adapters.** Implement `ui/streamlit_app.py` (primary local target) and `ui/vertex_app.py` (a Cloud Run entrypoint that serves the same core, e.g. Streamlit inside Cloud Run or a minimal FastAPI wrapper). Both must import from `core/` and share the same engine; no logic duplication.
3. **No runtime network calls.** The question bank is local (`data/question_bank.json`). Do not fetch questions or call any external API at runtime.
4. **No em-dashes and no emojis** in any user-facing string.
5. **Reuse the deck palette:** teal `0F766E`, charcoal `36454F`, accent tint `E6F2F0`. The look must feel like the same course as the teaching deck.
6. **Tests required.** Write `tests/test_core.py` with `pytest` covering: engine round progression, 50-50 removes exactly two wrong options, safe-haven floor at rung 5, timer pause/resume math, and rotation uniqueness (two different seeds yield two different 7-question rounds). All tests must pass.

### Game rules to implement (from the PRD)
- **7 rounds**, one question per difficulty tier (1..7), difficulty always ramps.
- **Designations (prizes):** 1=HR Intern, 2=HR Assistant, 3=HR Generalist, 4=HR Business Partner, 5=HR Manager (SAFE HAVEN floor), 6=HR Director, 7=CHRO.
- **Timer:** rungs 1-3 count down from **60 seconds**; rungs 4-7 have **no time limit**. Timeout on a timed question ends the run and awards the safe-haven floor.
- **Three lifelines, each once per game:**
  - `50-50`: remove two incorrect options, leaving the correct answer plus one decoy.
  - `Phone a Friend`: pause the timer and open a consult panel; perform NO computation.
  - `Expert Advice`: same as Phone a Friend, expert themed; pause timer, no computation.
- **Host control (semi-automated):** provide a host panel/override with Start Round, Pause/Resume Timer, Reveal Answer (triggers a short suspense beat before marking), Force Correct, Force Wrong, Show Explanation.
- **Rotation:** `draw_round(seed)` seeds on contestant id + timestamp + counter so no two contestants get the same round. Seed bank currently has 20 questions (2-3 per tier); the function must pick exactly one per tier.
- **Teaching explanation:** after every reveal (right or wrong), show the explanation card from the bank. Never skip it.
- **WWTBAM visual elements to mirror:** 7-rung designation ladder with current rung highlighted; hot-seat layout (host left, contestant right); four A/B/C/D answer boxes with blue/gold styling and green/red reveal states; three lifeline buttons anchored at top; "Lock kiya jaye?" / final-answer lock before reveal; suspense delay on reveal; sound hooks (timing tick, correct chord, wrong tone) as optional placeholders.
- **Intentional deviations (do NOT "fix" these):** prizes are designations not cash; "Ask the Audience" lifeline is intentionally absent; first three questions are timed (real show is not); no walk-away/quit mechanic; no Fastest Finger First.

### Suggested file layout (create if missing)
```
core/__init__.py, models.py, question_bank.py, game_engine.py,
lifelines.py, timer.py, host_control.py, designations.py, explain.py
ui/app_interface.py, ui/streamlit_app.py, ui/vertex_app.py
data/question_bank.json   (copy from repo root question_bank.json)
tests/test_core.py
Dockerfile, requirements.txt
```

### Implementation notes
- `question_bank.py`: load JSON, expose `load_bank(path)` and `draw_round(bank, seed, contestant_id)` returning a list of 7 Question objects, one per difficulty tier.
- `game_engine.py`: a `GameState` / state machine tracking current rung, used lifelines, selected answer, timer state, and final designation; methods `answer()`, `apply_lifeline()`, `reveal()`, `award()`.
- `timer.py`: an abstract `Timer` with `start()`, `pause()`, `resume()`, `remaining()`, `force_stop()`; emits remaining seconds for the UI to display.
- `host_control.py`: wraps engine + timer to expose the host overrides. Keep it a thin facade.
- `ui/streamlit_app.py`: render ladder, question, answer grid, lifeline bar, host panel (using `st.session_state` for game state), explanation card. Style with a CSS block matching the palette.
- `ui/vertex_app.py`: a `Dockerfile`-friendly entrypoint. Simplest correct approach: serve the Streamlit app via `streamlit run` inside the container on Cloud Run's port. If you prefer, wrap core in FastAPI and render with Streamlit separately; either is acceptable as long as core is shared.
- `Dockerfile`: Python 3.11-slim, install `requirements.txt`, `CMD ["streamlit", "run", "ui/streamlit_app.py", "--server.port=8080", "--server.address=0.0.0.0"]` (Cloud Run sets PORT; read it from env).

### Deliverables checklist
- [ ] `core/` pure Python, no UI imports
- [ ] `ui/streamlit_app.py` runs locally and shows the full game
- [ ] `ui/vertex_app.py` + `Dockerfile` deploy to Cloud Run
- [ ] `tests/test_core.py` passes under `pytest`
- [ ] Rotation, 50-50, safe-haven, timer, explanation all verified

When done, run `pytest` and `streamlit run ui/streamlit_app.py` to confirm, and report the test result and any deviations you had to make.

## === END PROMPT ===
