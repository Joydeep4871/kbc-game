# PRD: Kaun Banega CHRO (KBC) - HR Analytics Quiz Game

**Version:** 1.0
**Date:** 2026-07-19
**Owner:** Joydeep (rabhajoydeep@gmail.com)
**Status:** Draft for build (Claude Code execution pending)

---

## 1. Purpose and Audience

A classroom quiz game that teaches MBA students (zero coding background) the five Python libraries for HR analytics, using the format of "Who Wants To Be A Millionaire" (WWTBAM), known in India as "Kaun Banega Crorepati" (KBC).

Instead of cash, contestants win **corporate HR designations** (promotions) for each correct answer. The game doubles as a teaching tool: every answer reveal shows a plain-English explanation so the audience learns regardless of who is playing.

Source content is the 16-slide deck (`build_deck.js`) plus the AIHR article "HR Data Analytics: 5 Python Libraries You Need in HR". The YouTube link provided is the WWTBAM episode used strictly as a **structural and visual reference**, not a content source.

---

## 2. Source Material and Content Grounding

The question bank is grounded only in the two verified sources above. No question may be invented outside them.

- **Five libraries (workflow order, per the deck mnemonic "clean, calculate, show, check, predict"):**
  1. Pandas - The Organizer (clean)
  2. NumPy - The Calculator (calculate)
  3. Seaborn - The Illustrator (show)
  4. Statsmodels - The Auditor (check)
  5. Scikit-learn - The Forecaster (predict)
- **Seed bank:** `question_bank.json` (20 questions, difficulty 1 to 7). Expand as needed; the engine rotates per contestant so the bank should grow well beyond 7.

---

## 3. Game Concept

A single contestant sits in the "hot seat" with the host. Seven questions are asked in ascending difficulty. Each correct answer awards the next HR designation. A wrong answer (or timeout on a timed question) ends the run; the contestant keeps the highest **safe-haven** designation reached.

The host controls the drama: starting/pausing the timer, deciding when to reveal, and forcing correct/wrong for edge cases. This is a **presenter tool**, not a fully autonomous game.

---

## 4. WWTBAM Structural and Visual Analysis (mirrored 1:1 where faithful)

### 4.1 Elements we mirror exactly
- **The ladder / value pyramid:** a vertical list of the 7 rungs shown on screen, current rung highlighted, completed rungs dimmed, future rungs faint. In WWTBAM this is the cash ladder; here it is the designation ladder.
- **The hot seat:** host on the left, contestant on the right, facing the ladder and the answer grid.
- **Four answer options (A/B/C/D):** large letter boxes with the show's signature blue gradient and gold accents. Selected option highlights; on reveal it turns green (correct) or red (wrong).
- **Three lifeline buttons** anchored at the top of the play area.
- **The final-answer lock:** host asks "Lock kiya jaye?" (KBC phrasing) / "Final answer?" before the reveal, building the signature suspense beat.
- **Dramatized reveal:** after lock, a short suspense delay (music sting, beat) before the option is marked correct or wrong.
- **Sound design hooks:** ticking timer for Q1-3, ascending chord on correct, descending tone on wrong, ambient tension music. (Sounds are hooks/placeholders, not required assets for v1.)
- **Color system:** deep blue/teal field with gold accents, echoing both WWTBAM and KBC while reusing the deck's teal `0F766E` so the game visually matches the teaching materials.

### 4.2 Intentional deviations (documented, not oversights)
- **Prizes are designations, not cash.** Required by the brief.
- **"Ask the Audience" lifeline is dropped.** The brief specifies exactly three lifelines: 50-50, Phone a Friend, Expert Advice.
- **First three questions are 60-second timed.** The real show does not time early questions; the brief requires it.
- **No "walk away / quit" mechanic.** With sequential promotions as prizes in a teaching session, quitting mid-ladder is awkward. The run ends on a wrong answer; the safe-haven floor is retained. (Flagged as a confirmable decision in section 14.)
- **Fastest Finger First is omitted.** Contestant selection is the host's call, not a mini-game.

---

## 5. The 7-Round Ladder and Designations

Difficulty ramps with the ladder. Reaching rung 5 triggers the **safe-haven**: the contestant is guaranteed at least "HR Manager" and cannot fall below it.

| Rung | Difficulty | Designation | Timed? | Tier |
|------|------------|-------------|--------|------|
| 1 | 1 | HR Intern | 60s | Opening |
| 2 | 2 | HR Assistant | 60s | Opening |
| 3 | 3 | HR Generalist | 60s | Opening |
| 4 | 4 | HR Business Partner | No limit | Safe-haven approach |
| 5 | 5 | HR Manager | No limit | **Safe haven (floor)** |
| 6 | 6 | HR Director | No limit | Final |
| 7 | 7 | CHRO | No limit | Final (title of the game) |

The title of the game is "Kaun Banega CHRO" = "Who Will Become CHRO", so rung 7 = CHRO is the literal win condition.

---

## 6. Timer Rules

- Rungs 1 to 3: **60-second countdown**, auto-started when the question appears.
- Rungs 4 to 7: **no time limit.**
- Timeout on a timed question = treated as a wrong answer (run ends, award safe-haven floor). Host may override with force-correct.
- Timer is **pauseable** by the host (used during Phone a Friend and Expert Advice, and at host discretion).

---

## 7. Lifelines (each usable once per game)

1. **50-50:** removes two incorrect options from the screen, leaving the correct answer and one decoy. Real function performed by the engine.
2. **Phone a Friend:** pauses the timer and opens a "friend" panel. No computation is performed; it exists purely to let the host dramatize a consult. Timer stays paused until host resumes.
3. **Expert Advice:** same behavior as Phone a Friend but themed as an expert consult. Pauses timer, no computation.

All three are single-use. Used lifelines are visually disabled for the rest of the run.

---

## 8. Host Control Model (semi-automated)

The timer auto-runs per the rules, but the host has an override panel:

- **Start Round / Next Question:** advance the ladder.
- **Pause / Resume Timer:** freeze or continue the countdown.
- **Reveal Answer:** trigger the suspenseful reveal sequence (highlight selected option, beat, then mark correct/wrong).
- **Force Correct:** mark the current answer correct regardless of selection (edge cases, host discretion).
- **Force Wrong:** mark the current answer wrong (edge cases, host discretion).
- **Show Explanation:** after reveal, display the plain-English explanation card.

The host is the source of the drama. The app provides the controls and the suspense scaffolding; the human decides the timing.

---

## 9. Question Bank and Rotation

- Bank lives in `question_bank.json` (or `.yaml`). Each question carries: id, library, difficulty (1-7), question, four options, correct_index, explanation, optional code snippet.
- **Round composition:** exactly one question per difficulty tier (1 through 7), so difficulty always ramps. Within a tier, the library/topic is shuffled.
- **Rotation:** `draw_round(seed)` seeds a random generator on `contestant_id + session_timestamp + monotonic_counter`. This guarantees **no two contestants receive the same 7-question round**, as long as the bank has enough questions per tier (aim for at least 3 per tier; seed bank already has 2-3).
- Bank is **local and self-contained.** No network call is made to fetch questions at runtime.

---

## 10. Answer Reveal and Teaching Explanation

- After the host triggers reveal, the selected option is marked green (correct) or red (wrong), with a sound hook.
- Regardless of right or wrong, the next screen transition shows the **explanation card**: the correct answer plus the plain-English "why" from the bank. This is the teaching payload and must never be skipped.
- On wrong answer, the run ends and the contestant is shown their final (safe-haven-floored) designation.

---

## 11. Architecture (agnostic core plus thin UI adapters)

The game logic must be **framework-independent pure Python**, so it runs identically under Streamlit, a Vertex/Cloud Run web service, or tests.

```
kbc_game/
  core/                  # pure Python, no UI dependency, fully unit-tested
    models.py            # Question, Option, Lifeline, Round, Contestant, GameState
    question_bank.py     # load bank; draw_round(seed) -> 7 questions, one per tier
    game_engine.py       # state machine: rounds, evaluation, safe-haven, designation award
    lifelines.py         # 50-50 logic; phone-a-friend / expert-advice as pause flags
    timer.py             # abstract Timer: start/pause/resume/force-stop; emits seconds
    host_control.py      # host override interface (pause, reveal, force_correct, force_wrong)
    designations.py      # rung -> HR title mapping; safe-haven floor
    explain.py           # explanation card payload
  ui/
    app_interface.py     # contract both adapters implement (render question, timer, lifelines, host panel, explanation)
    streamlit_app.py     # Streamlit implementation (primary local/dev target)
    vertex_app.py        # Vertex/Cloud Run entrypoint (thin wrapper around core + a web layer)
  data/
    question_bank.json   # seed bank
  tests/
    test_core.py         # pytest: engine, lifelines, rotation uniqueness, safe-haven, timer
  Dockerfile             # for Vertex/Cloud Run deployment
  requirements.txt
  PRD.md
  CLAUDE_CODE_PROMPT.md
```

**Why this split:** the brief requires deployment in "streamlit, vertex etc." Keeping `core/` free of any UI import means the same engine powers every front end, and the rotation/evaluation logic is testable without a browser.

---

## 12. Tech Stack and Dependencies

- **Language:** Python 3.11+
- **Core:** standard library only (dataclasses, random, json). No heavy deps.
- **Streamlit adapter:** `streamlit`.
- **Vertex adapter:** deployed as a container on **Cloud Run** serving the Streamlit app (or a minimal FastAPI layer). `gcloud` for deploy.
- **Tests:** `pytest`.
- **Theming:** CSS overrides for Streamlit to achieve the blue/teal/gold KBC look; sound hooks are optional `.wav`/`.mp3` placeholders.

---

## 13. Non-Functional Requirements

- **Offline by default:** no external API or network call at runtime. Question bank and game state are local.
- **Deterministic rotation:** same seed yields same round; different seeds yield different rounds (verified by test).
- **Accessibility:** high-contrast text, large answer boxes, keyboard-selectable options where feasible.
- **Theming consistency:** reuse deck teal `0F766E` and charcoal `36454F` so the game feels like part of the same course.
- **No em-dashes or emojis** in any user-facing copy (matches the course's writing standard).
- **Maintainability:** `core/` has no UI imports; adapters stay thin.

---

## 14. Out of Scope / Decisions to Confirm

- **Walk-away / quit mechanic:** omitted (see 4.2). Confirm or request addition.
- **Fastest Finger First:** omitted; host selects the contestant.
- **Sound assets:** hooks only in v1; real audio is a later enhancement.
- **Persistence of scores across sessions:** not required for v1; in-memory game state is sufficient.
- **Multi-contestant tournament bracket:** out of scope for v1.

---

## 15. Acceptance Criteria

1. App launches in Streamlit and presents the 7-rung designation ladder and hot-seat layout.
2. Exactly 7 questions are drawn, one per difficulty tier, with ascending difficulty.
3. Two different contestant seeds produce two different rounds (rotation works; covered by a pytest).
4. Q1-3 count down from 60s; timeout ends the run at the safe-haven floor.
5. Q4-7 have no timer.
6. 50-50 removes exactly two wrong options and leaves correct + one decoy.
7. Phone a Friend and Expert Advice pause the timer and perform no computation.
8. Host panel can pause/resume timer, reveal, force-correct, force-wrong.
9. After every reveal (right or wrong), the explanation card appears.
10. Safe-haven floor holds: reaching rung 5 guarantees at least "HR Manager".
11. Same code base deploys to Cloud Run via the provided Dockerfile.
12. `pytest` on `core/` passes.

---

## 16. Appendix

### A. Designation ladder
HR Intern (1) -> HR Assistant (2) -> HR Generalist (3) -> HR Business Partner (4) -> HR Manager (5, safe haven) -> HR Director (6) -> CHRO (7).

### B. Lifeline summary
| Lifeline | Function | Uses |
|----------|----------|------|
| 50-50 | Remove 2 wrong options | 1 |
| Phone a Friend | Pause timer, dramatize consult | 1 |
| Expert Advice | Pause timer, dramatize consult | 1 |

### C. Build entry point
The build is driven by `CLAUDE_CODE_PROMPT.md`, executed via the Claude Code agent. See `CAPABILITIES.md` for the skills, plugins, connectors, and MCP servers required to build and deploy.
