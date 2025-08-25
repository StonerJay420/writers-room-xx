
## Part 1/4 - Prompts 01–25

## Prompt 01 — Monorepo Scaffold

> **Objective:** Create the base monorepo with backend (FastAPI), frontend (Next.js), vector DB (Chroma), and local SQLite.  
> **Create exact structure:**
> ```
> writers-room-x/
>   api/
>     app/
>       __init__.py
>       main.py
>       config.py
>       deps.py
>       db.py
>       models/  (empty __init__.py)
>       schemas/ (empty __init__.py)
>       routers/ (empty __init__.py)
>       services/ (empty __init__.py)
>       agents/ (empty __init__.py)
>       rag/ (empty __init__.py)
>       metrics/ (empty __init__.py)
>       utils/ (empty __init__.py)
>     tests/
>     pyproject.toml
>     requirements.txt
>   ui/   (Next.js app scaffolding)
>   artifacts/   (git-ignored)
>   data/        (git-ignored)
>   configs/
>     agents.yaml
>     metrics.yaml
>     project.yaml
>   docker/
>     Dockerfile.api
>     Dockerfile.ui
>   docker-compose.yml
>   .env.example
>   README.md
> ```
> **Backend dependencies (pin versions):** fastapi, uvicorn[standard], pydantic, sqlalchemy, alembic, chromadb, httpx, python-dotenv, textstat, spacy, nltk, sentence-transformers, rapidfuzz, GitPython, typer, langgraph (or autogen), difflib (stdlib).  
> **Frontend dependencies:** Next.js (App Router, TS), TailwindCSS, @tanstack/react-query, react-diff-viewer, cmdk, framer-motion, recharts or visx.  
> **.env.example keys:** `OPENROUTER_API_KEY=`, `DATABASE_URL=sqlite:///data/app.db`, `CHROMA_HOST=chroma`, `CHROMA_PORT=8000`, `API_PORT=8080`, `UI_PORT=3000`, `GIT_USER_NAME=Dev`, `GIT_USER_EMAIL=dev@example.com`.  
> **README.md:** quickstart with docker compose, local dev commands.  
> **Acceptance:** Repo boots (no TODO placeholders), empty modules import cleanly.

## Prompt 02 — Docker Compose & Images

> **Objective:** One-command dev stack.  
> **Create** `docker-compose.yml` with services:
> - `chroma`: official chromadb server; ports `8000:8000`; volume `chroma-data:/chroma`.  
> - `api`: build `docker/Dockerfile.api`; env from `.env`; mounts project; command runs `uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload`; depends_on `chroma`.  
> - `ui`: build `docker/Dockerfile.ui`; env `API_BASE=http://localhost:8080`; runs `next dev -p 3000`; depends_on `api`.  
> **Dockerfile.api:** Python 3.11-slim, system deps for spaCy, install requirements, cache layers, working dir `/app/api`.  
> **Dockerfile.ui:** Node 20-alpine, install, build scripts, dev command.  
> **Acceptance:** `docker compose up` exposes UI on 3000, API on 8080, Chroma on 8000.

## Prompt 03 — Core App Config

> **Objective:** Centralize settings and app bootstrap.  
> **Files:**  
> - `api/app/config.py`: Pydantic `Settings` loading `.env` with keys from Prompt 01; expose `settings = Settings()`.  
> - `api/app/db.py`: build SQLAlchemy engine from `DATABASE_URL`; create `SessionLocal`; ensure `/data` exists; Base metadata exported.  
> - `api/app/deps.py`: `get_db()` context, `get_settings()` returns settings, `get_chroma_client()` HTTP client using `CHROMA_HOST/PORT`.  
> - `api/app/main.py`: FastAPI app with CORS `*` (dev), include (empty) routers, GET `/health` → `{ "status":"ok" }`.  
> **Acceptance:** `uvicorn app.main:app --reload` returns health OK.

## Prompt 04 — Database Models (SQLite)

> **Objective:** Define initial tables.  
> **Create models** under `api/app/models/` with SQLAlchemy ORM:
> - `scene.py`: `Scene(id:str PK, chapter:int, order_in_chapter:int, pov:str, location:str, text_path:str, beats_json:str, links_json:str, created_at:datetime, updated_at:datetime)`.  
> - `character.py`: `Character(id:str PK, name:str, voice_tags_json:str, preferred_words_json:str, banned_words_json:str, arc_flags_json:str, canon_quotes_json:str, updated_at:datetime)`.  
> - `job.py`: `Job(id:str PK, scene_id:str FK->Scene.id, status:str, agents_json:str, result_json:str, created_at, updated_at)`.  
> - `__init__.py`: export `Base`.  
> **Startup hook:** create_all if not exists.  
> **Acceptance:** Tables created on API start.

## Prompt 05 — Schemas & Router Stubs

> **Objective:** Strong I/O contracts; mount routers.  
> **Create Pydantic schemas:** `api/app/schemas/scene.py`, `character.py`, `job.py` (read/write models with type hints).  
> **Create routers:** `api/app/routers/ingest.py`, `scenes.py`, `passes.py`, `patches.py`, `reports.py` (empty endpoints for now).  
> **Register** routers in `main.py` with prefixes `/ingest`, `/scenes`, `/passes`, `/patches`, `/reports`.  
> **Acceptance:** Import clean, API starts.

## Prompt 06 — RAG: Embeddings & Chroma Client

> **Objective:** Chunk text, embed, and upsert/query Chroma.  
> **Files:**  
> - `api/app/rag/embeddings.py`: load `sentence-transformers` model `all-MiniLM-L6-v2`; function `embed_texts(texts:list[str]) -> np.ndarray`.  
> - `api/app/rag/chunker.py`: `chunk_markdown(text:str, max_tokens:int=900, stride:int=200) -> list[{chunk_id,start_line,end_line,text}]` (use word-count proxy).  
> - `api/app/rag/chroma_client.py`: wrapper for Chroma HTTP; `upsert(collection:str, embeddings, metadatas:list[dict], ids:list[str])`, `query(collection:str, query_text:str, top_k:int, filters:dict|None)`.  
> **Acceptance:** Unit-callable functions with docstrings.

## Prompt 07 — Ingestion Endpoint `/ingest/index`

> **Objective:** Index codex/manuscript into DB + Chroma.  
> **Create service** `api/app/services/ingest_service.py` and router `api/app/routers/ingest.py`.  
> **Endpoint:** `POST /ingest/index`  
> **Request:**
> ```json
> { "paths": ["codex/","manuscript/"], "reindex": true }
> ```  
> **Behavior:**  
> - Recursively read `*.md`.  
> - Manuscript path rule: `manuscript/chXX/chXX_sYY.md` → scene_id=`chXX_sYY`, chapter=XX.  
> - Upsert `Scene` rows.  
> - Chunk + embed each file; collection=`codex_docs` or `manuscript_scenes`.  
> - Metadata **must include** `{source_path, scene_id?, chapter?, start_line, end_line, tags?}`.  
> **Response:**
> ```json
> { "indexed_docs": <int>, "scenes": <int> }
> ```  
> **Acceptance:** Response counts reflect files processed; Chroma collections populated.

## Prompt 08 — Retrieval with Receipts

> **Objective:** Canon lookups that preserve line refs.  
> **Create** `api/app/rag/retrieve.py` with `retrieve_canon(query:str, k:int=12, filters:dict|None=None) -> list[{text, source_path, start_line, end_line}]`.  
> **Constraints:** Always return `source_path` and exact line ranges for each snippet.  
> **Tests:** Add minimal fixture docs and assert line ranges map to input text.  
> **Acceptance:** Deterministic retrieval with receipts.

## Prompt 09 — Metrics Module (ED Subset)

> **Objective:** Compute style metrics vs targets.  
> **Create** `api/app/metrics/metrics.py` with:
> - `compute_readability(text) -> {"flesch": float}` (textstat).  
> - `avg_sentence_length(text) -> float`.  
> - `pos_distribution(text) -> {nouns, verbs, adjectives, adverbs, pronouns, other}` using spaCy `en_core_web_sm`.  
> - `active_verb_ratio(text) -> float` (verbs not AUX).  
> - `report(text, metrics_cfg:dict) -> dict` with actual vs target and status `green|yellow|red`.  
> **Populate** `configs/metrics.yaml` with the provided ED targets.  
> **Acceptance:** Functions pure/testable; YAML loaded without error.

## Prompt 10 — Diff Utility

> **Objective:** Make and apply unified diffs safely.  
> **Create** `api/app/utils/diff.py` with:
> - `make_unified_diff(original:str, revised:str, filename:str) -> str` using `difflib.unified_diff`.  
> - `apply_patch_to_file(file_path:str, unified_diff:str) -> bool`: dry-run verify anchors; attempt fuzzy re-anchoring with `rapidfuzz` for small drift; if unsafe, return False.  
> **Tests:** Round-trip apply on sample text; idempotency check.  
> **Acceptance:** Patch apply succeeds/fails predictably.

## Prompt 11 — OpenRouter Client & Agent Base

> **Objective:** Consistent LLM calls and agent abstraction.  
> **Create** `api/app/services/llm_client.py`:
> - `complete(messages:list[dict], model:str, temperature:float, max_tokens:int, json_mode:bool=False, timeout:int=60) -> str|dict` calling OpenRouter `/chat/completions` with `OPENROUTER_API_KEY`; retries with backoff; optional JSON mode.  
> **Create** `api/app/agents/base.py`:
> - `class Agent`: init with `name, model, tools:list[str]|None`; method `run(task:dict, context:dict)->dict`; helper for JSON schema validation (pydantic).  
> **Acceptance:** Mockable, with clear exceptions on HTTP or parse errors.

## Prompt 12 — Supervisor Agent

> **Objective:** Plan sub-tasks, call agents, compose variants.  
> **Create** `api/app/agents/supervisor.py` with `run_supervisor(scene_text:str, scene_meta:dict, metrics_config:dict, edge_intensity:int, requested_agents:list[str]) -> dict`.  
> **Outputs:**  
> ```json
> {
>   "plan": {"tasks":[{"agent":"lore_archivist"}, {"agent":"grim_editor"}, {"agent":"tone_metrics"}],
>            "success_criteria":["no_canon_violations","metrics_within_targets","diffs_valid"]},
>   "variants": {"safe": {...}, "bold": {...}, "red_team": {...}},
>   "receipts": [ { "source":"codex/...", "lines":"L10-L20" } ],
>   "rationales": { "lore_archivist":"...", "grim_editor":"...", "tone_metrics":"..." }
> }
> ```  
> **Acceptance:** Returns up to 3 variants; omits `red_team` if not requested or `edge_intensity=0`.

## Prompt 13 — Lore Archivist Agent

> **Objective:** Canon validation with receipts + minimal fix diff.  
> **Create** `api/app/agents/lore_archivist.py` with `run_lore_archivist(scene_text, scene_meta, retrieve_fn, model) -> dict`.  
> **System prompt:** Validate changes against canon; cite receipts `{source_path, lines}`; if conflict, propose minimal correction diff.  
> **Output schema:**
> ```json
> {
>   "findings":[{"issue":"...", "severity":"block|warn",
>                "receipt":{"source":"codex/...", "lines":"L45-L63"},
>                "suggestion":"..."}],
>   "receipts":[{"source":"...", "lines":"L..-L.."}],
>   "diff":"<unified diff or ''>"
> }
> ```  
> **Acceptance:** Deterministic at `temperature=0.3`.

## Prompt 14 — Grim Editor Agent

> **Objective:** Line edits for clarity/precision; preserve meaning.  
> **Create** `api/app/agents/grim_editor.py` with `run_grim_editor(scene_text:str, style_targets:dict, model:str) -> dict`.  
> **System prompt:** Preserve meaning and plot beats; improve clarity, rhythm, specificity; avoid canon changes. Return unified diff + 3-bullet rationale.  
> **Output:**
> ```json
> { "diff":"<unified diff>", "rationale":["...","...","..."] }
> ```  
> **Acceptance:** Uses `make_unified_diff`, `temperature≈0.7`.

## Prompt 15 — Tone & Metrics Agent

> **Objective:** Score vs targets and propose minimal nudges.  
> **Create** `api/app/agents/tone_metrics.py` with `run_tone_metrics(scene_text:str, metrics_yaml:dict, model:str) -> dict`.  
> **System prompt:** Score passage; suggest minimal edits to hit ranges; return small diff.  
> **Output:**
> ```json
> {
>   "metrics_before": {...},
>   "metrics_after": {...},
>   "diff":"<unified diff>"
> }
> ```  
> **Acceptance:** Calls `metrics.report`; diff may be empty if already in range.

## Prompt 16 — Pass Orchestrator & Endpoint

> **Objective:** Run a pass on a scene end-to-end.  
> **Create** `api/app/services/pass_service.py` with `run_pass(scene_id:str, agents:list[str], edge_intensity:int) -> dict`.  
> **Create** `api/app/routers/passes.py` endpoint `POST /passes/run`.  
> **Request:**
> ```json
> { "scene_id":"ch02_s03", "agents":["lore_archivist","grim_editor","tone_metrics"], "edge_intensity":1 }
> ```  
> **Response:**
> ```json
> {
>   "scene_id":"ch02_s03",
>   "variants":{"safe":{...}, "bold":{...}, "red_team":{...}},
>   "reports":{"metrics":{...}, "canon_receipts":[...], "rationales":{...}}
> }
> ```  
> **Artifacts:** save diffs and JSON under `artifacts/patches/{scene_id}_{variant}.(diff|json)`.  
> **Acceptance:** Inline response (no async queue) for MVP.

## Prompt 17 — Scenes API

> **Objective:** List scenes and fetch content.  
> **Create** routes in `api/app/routers/scenes.py`:
> - `GET /scenes?chapter=<int>&search=<str>` → list of scene metadata.  
> - `GET /scenes/{scene_id}` → `{ "meta": Scene, "text": "<file contents>" }` (read from `text_path`).  
> **Acceptance:** Search matches by id, pov, location, or filename.

## Prompt 18 — Apply Patch Endpoint

> **Objective:** Apply selected patch and commit.  
> **Create** `POST /patches/apply` in `api/app/routers/patches.py`.  
> **Request:**
> ```json
> { "scene_id":"ch02_s03", "variant":"safe", "commit_message":"Apply safe patch for ch02_s03" }
> ```  
> **Behavior:** Load `artifacts/patches/{scene_id}_{variant}.diff`, apply to `text_path`; on success, commit with GitPython using env `GIT_USER_*`.  
> **Response:**
> ```json
> { "status":"ok", "commit_sha":"<sha>" }
> ```  
> **Acceptance:** Idempotent; fails with clear error if anchors mismatch beyond fuzzy threshold.

## Prompt 19 — Chapter Report Endpoint

> **Objective:** Aggregate chapter-level HTML report.  
> **Create** `GET /reports/chapter/{chapter:int}` in `api/app/routers/reports.py`.  
> **Behavior:** Aggregate latest metrics per scene; render HTML (tables + small sparkline Unicode acceptable). Save to `artifacts/reports/ch{chapter}.html`.  
> **Response:** HTML string.  
> **Acceptance:** Opens in browser and summarizes metrics/receipts counts.

## Prompt 20 — Frontend Scaffold (Next.js)

> **Objective:** Base UI with providers and theme.  
> **In** `ui/`: initialize Next.js TS app with Tailwind; set up React Query provider and a global `API_BASE` from env.  
> **Pages:**  
> - `/` (scenes list placeholder)  
> - `/scene/[id]` (review placeholder)  
> **Shared:** `lib/api.ts` (fetch wrapper with `API_BASE`), global layout, toasts provider.  
> **Acceptance:** Both pages render; API health check displayed.

## Prompt 21 — Scenes List Page

> **Objective:** Browse, filter, and run a pass.  
> **Implement** `ui/app/page.tsx`:  
> - Fetch `GET /scenes`.  
> - Table columns: Scene ID, Chapter, POV, Location, Actions.  
> - Filters: chapter select, text search.  
> - “Run Pass” button → modal: agent checkboxes + edge slider (0–3). `POST /passes/run` then route to `/scene/[id]`.  
> **Acceptance:** Loading, empty, and error states present.

## Prompt 22 — Scene Review Page

> **Objective:** Diff viewer + metrics + receipts + apply.  
> **Implement** `ui/app/scene/[id]/page.tsx`:  
> - Left: original text (line numbers).  
> - Center Tabs: Safe / Bold / Red-Team (diff viewer).  
> - Right panel: metrics before/after badges, canon receipts (popover with `source_path:Lx–Ly` snippet), agent rationales.  
> - Footer: Apply Patch → `POST /patches/apply`.  
> **Acceptance:** Disable Apply if no diff or blocking canon conflicts.

## Prompt 23 — Seed Content

> **Objective:** Provide testable sample data.  
> **Create** in repo root:  
> - `codex/systems/energy_core.md` (~80 lines with canonical terms).  
> - `codex/locations/undercity.md`  
> - `codex/factions/enforcers.md`  
> - `manuscript/ch01/ch01_s01.md`, `manuscript/ch01/ch01_s02.md` referencing codex facts.  
> **Create** optional script `api/app/services/seed.py` to copy seeds into `/data/seed/` if empty.  
> **README:** add instructions to hit `POST /ingest/index`.  
> **Acceptance:** Ingestion indexes seeds successfully.

## Prompt 24 — End-to-End Smoke Test

> **Objective:** Programmatic happy-path validation.  
> **Create** `api/tests/test_smoke.py` (pytest):  
> 1) POST `/ingest/index` for `codex/` and `manuscript/`.  
> 2) GET `/scenes`, pick first `scene_id`.  
> 3) POST `/passes/run` with `["lore_archivist","grim_editor","tone_metrics"]`.  
> 4) Assert `variants.safe.diff` exists and `reports.metrics` present.  
> 5) POST `/patches/apply` variant `safe`; assert 200.  
> **CI:** GitHub Actions workflow to run tests.  
> **Acceptance:** CI passes.

## Prompt 25 — CLI Utilities (Typer)

> **Objective:** Power-user commands that call API.  
> **Create** `api/app/utils/cli.py` using Typer with commands:  
> - `wrx index <paths...> --reindex` → POST `/ingest/index`.  
> - `wrx pass --scene <scene_id> --agents lore,grim,tone --edge 1` → POST `/passes/run`.  
> - `wrx apply --scene <scene_id> --variant <name> --msg "<commit>"` → POST `/patches/apply`.  
> - `wrx report --chapter <n>` → GET `/reports/chapter/{n}` and write HTML.  
> **pyproject:** console_script `wrx=app.utils.cli:app`.  
> **Acceptance:** Commands run against local API.

## Part 2/4 - Prompts 26–50

## Prompt 26 — Config Files (Agents, Metrics, Project)

> **Objective:** Provide concrete YAML configs and load/validate them at API startup.  
> **Tasks**  
> 1) Create `configs/agents.yaml` with exact defaults:
> ```yaml
> supervisor: { model: "reasoner-1", max_tokens: 4000, temperature: 0.2 }
> lore_archivist: { model: "reasoner-1", temperature: 0.3, tools: ["rag","citations"] }
> grim_editor: { model: "stylist-1", temperature: 0.7, tools: ["diff","metrics"] }
> dialogue_demon: { model: "stylist-1", temperature: 0.8, tools: ["diff"] }
> pacing_surgeon: { model: "reasoner-1", temperature: 0.5, tools: ["metrics","diff"] }
> plot_twister: { model: "reasoner-1", temperature: 0.6 }
> tone_metrics: { model: "critic-1", temperature: 0.2, tools: ["metrics"] }
> red_team: { model: "stylist-1", temperature: 0.9, tools: ["diff"] }
> reviewer_pack: { model: "reasoner-1", temperature: 0.5 }
> voice_simulator: { model: "stylist-1", temperature: 0.8 }
> ```
> 2) Create `configs/metrics.yaml` using the ED targets exactly (copy full spec from prior material; include all bands and targets).  
> 3) Create `configs/project.yaml`:
> ```yaml
> edge_intensity: 1                       # 0..3
> patch_variants: ["safe","bold","red_team"]
> chapter_reversal_percent: [8,11,50]
> banned_global: ["neon","echoes","symphony"]
> ```
> 4) Implement loader `api/app/utils/config_loader.py` with functions:
> - `load_agents_cfg() -> dict`
> - `load_metrics_cfg() -> dict`
> - `load_project_cfg() -> dict`
> Validate keys with Pydantic models; raise `HTTPException(500)` on invalid.  
> 5) Call loaders at API startup; cache results.  
> **Acceptance**: `GET /health` includes `{ "configs": "ok" }` when files parse and validate; errors produce startup failure with clear logs.

## Prompt 27 — Environment, Security, and spaCy Model

> **Objective:** Ensure predictable runtime: env validation, secret hygiene, spaCy model availability.  
> **Tasks**  
> 1) In `api/app/config.py`, make `OPENROUTER_API_KEY` required; if missing, set `LLM_DISABLED=True`.  
> 2) Add middleware that returns `503 JSON {error:"LLM_DISABLED"}` for endpoints that need LLMs when key is absent.  
> 3) Update `docker/Dockerfile.api` to install spaCy model:
> ```
> RUN python -m spacy download en_core_web_sm
> ```
> 4) Scrub secrets in logs (never print API keys). Add helper `redact(value:str)->str` for logging.  
> 5) Document `.env` usage in README; add warnings for committing secrets.  
> **Acceptance**: With no key, `/passes/run` returns 503 with explicit message; with key, runs normally.

## Prompt 28 — Structured Logging & Global Error Handling

> **Objective:** Consistent logs and error responses with correlation IDs.  
> **Tasks**  
> 1) Create `api/app/utils/logging.py` that configures `structlog` or standard logging with JSON lines (timestamp, level, message, route, correlation_id).  
> 2) Add middleware to inject `X-Request-ID` (use existing header or generate UUID). Attach to responses and logs.  
> 3) Global exception handler that returns JSON:
> ```json
> { "error": "Message", "code": "INTERNAL_ERROR", "request_id": "<uuid>" }
> ```
> 4) Log key events: ingestion start/end, pass start/end, patch apply result, report generation.  
> **Acceptance**: Errors return JSON with `request_id`; logs show matching correlation IDs.

## Prompt 29 — UI Safeguards & Validation

> **Objective:** Prevent unsafe or invalid user actions in the UI.  
> **Tasks**  
> 1) In `/scene/[id]`, disable **Apply Patch** when:
>    - selected variant has empty diff, OR
>    - any Lore finding has `severity:"block"`.  
> 2) Add metrics legend (green/yellow/red thresholds from `metrics.yaml`).  
> 3) Show confirmation modal before apply, displaying:
>    - number of changed lines,
>    - list of files affected (only one expected),
>    - summary of metrics deltas.  
> 4) Accessibility: ensure buttons have ARIA labels; tooltips keyboard-accessible.  
> **Acceptance**: Attempts to apply when disabled are blocked and show a toast explaining why.

## Prompt 30 — Acceptance Script (End-to-End)

> **Objective:** Single bash script validates the MVP end-to-end.  
> **Tasks**  
> 1) Create `scripts/acceptance.sh` (bash, executable). Steps:
>    - `docker compose up -d --build`
>    - Wait for `http://localhost:8080/health` (retry up to 60s)
>    - `curl -X POST /ingest/index` for `codex/` and `manuscript/`
>    - `curl -X GET /scenes` to pick first `scene_id`
>    - `curl -X POST /passes/run` (lore, grim, tone)
>    - Verify `variants.safe.diff` present
>    - `curl -X POST /patches/apply` (safe)
>    - `curl -X GET /reports/chapter/1` (save HTML)
>    - Print `DONE: MVP PASSED` on success; exit nonzero on any failure  
> 2) Update README: how to run the script and interpret failures.  
> **Acceptance**: Running the script prints success and produces artifacts (patch and report files).

## Prompt 31 — Red-Team Agent (Flagged Output)

> **Objective:** Generate an “edge” variant safely; never auto-apply.  
> **Tasks**  
> 1) Implement `api/app/agents/red_team.py` function:
> `run_red_team(scene_text:str, edge_intensity:int, banned:list[str], model:str) -> dict`.  
> 2) System prompt: escalate tension and taboo via psychology, not explicit gore/sex; obey `banned` list and canon.  
> 3) Output schema:
> ```json
> { "diff":"<unified diff>", "rationale":["..."], "label":"RED_TEAM", "edge_intensity": 0..3 }
> ```  
> 4) Wire into `supervisor.py` to include as `variants.red_team` **only if** `edge_intensity>=1`.  
> **Acceptance**: Red-Team never included when `edge_intensity=0`; diff contains no banned terms.

## Prompt 32 — Documentation Pass

> **Objective:** Ship handoff-ready docs.  
> **Tasks**  
> 1) Expand `README.md` with:
>    - Architecture overview (ASCII diagram acceptable)
>    - Quickstart (docker + local)
>    - Endpoint table with request/response JSON examples
>    - Config reference (`agents.yaml`, `metrics.yaml`, `project.yaml`)
>    - Troubleshooting (common errors, LLM disabled mode)  
> 2) Add `CONTRIBUTING.md` (linting, testing, branch strategy).  
> 3) Add OpenAPI docs exposure at `/docs` and `/openapi.json`.  
> **Acceptance**: A new developer can set up and execute the MVP using only the docs.

## Prompt 33 — Dialogue Demon Agent

> **Objective:** Rewrite only dialogue lines with stronger subtext and voice.  
> **Tasks**  
> 1) Create `api/app/agents/dialogue_demon.py`:
> `run_dialogue_demon(scene_text:str, character_meta:dict, model:str) -> dict`.  
> 2) System prompt: modify **only dialogue** (quoted lines or em-dash lines); keep intent; amplify subtext; enforce per-character preferred/banned words.  
> 3) Output:
> ```json
> { "diff":"<unified diff>", "rationale":["...","...","..."] }
> ```  
> 4) Integrate optional call in Supervisor when `dialogue_demon` requested.  
> **Acceptance**: No narration changes; unit test verifies only dialogue lines differ.

## Prompt 34 — Pacing Surgeon Agent

> **Objective:** Adjust rhythm and hooks while preserving meaning.  
> **Tasks**  
> 1) Create `api/app/agents/pacing_surgeon.py`:
> `run_pacing_surgeon(scene_text:str, metrics_cfg:dict, model:str) -> dict`.  
> 2) System prompt: assess sentence length variance, paragraph size, whitespace, and scene hook; propose minimal edits; optionally inject a final sentence hook if absent.  
> 3) Output:
> ```json
> { "diff":"<unified diff>", "rationale":["pace adjustment","hook added? yes/no"] }
> ```  
> 4) Integrate optional call in Supervisor.  
> **Acceptance**: Average sentence length moves toward configured target; diff is minimal.

## Prompt 35 — Plot Twister Agent

> **Objective:** Suggest plot reversals; no automatic diffs.  
> **Tasks**  
> 1) Create `api/app/agents/plot_twister.py`:
> `run_plot_twister(scene_meta:dict, story_percent:float, codex_context:dict, model:str) -> dict`.  
> 2) System prompt: provide 2–3 twists tuned to `story_percent` (8–11% or ~50% pivot). Each: label, beats, 1-paragraph sample.  
> 3) Output:
> ```json
> { "twists":[ { "label":"...", "beats":["...","..."], "sample":"..." } ] }
> ```  
> 4) Supervisor surfaces `twists` in result; UI displays under “WTF moments”.  
> **Acceptance**: JSON only; no diffs produced.

## Prompt 36 — Beatmap Service & Endpoint

> **Objective:** Compute a story timeline with reversal markers.  
> **Tasks**  
> 1) Create `api/app/services/beatmap_service.py` that:
>    - Scans `Scene` records in order (by chapter then order_in_chapter),
>    - Estimates cumulative word counts from file contents,
>    - Computes `percent = (cumulative_words / total_words) * 100`,
>    - Marks windows at 8–11% and 50% if twists/hooks exist.  
> 2) Add `GET /reports/beatmap` returning:
> ```json
> { "scenes":[ { "scene_id":"ch01_s02", "chapter":1, "percent":10.4, "markers":["reversal"] } ] }
> ```  
> **Acceptance**: With seed data, percent values sum logically and markers appear near configured windows.

## Prompt 37 — Reviewer Persona Pack Agent

> **Objective:** Generate targeted critiques with grades.  
> **Tasks**  
> 1) Create `api/app/agents/reviewer_pack.py`:
> `run_reviewer_pack(scene_text:str, persona:str, model:str) -> dict`.  
> 2) Personas: `hostile_reviewer`, `genre_purist`, `film_producer`.  
> 3) System prompt template: roleplay persona; 500-word max critique; end with `Grade: A–F`.  
> 4) Output:
> ```json
> { "persona":"...", "critique":"...", "grade":"B+" }
> ```  
> 5) Supervisor may attach reviewer results when requested.  
> **Acceptance**: Grade parsed and included; length ≤ 500 words.

## Prompt 38 — Character Voice Simulator

> **Objective:** A/B/C dialogue variants per line; learn preferences.  
> **Tasks**  
> 1) Create `api/app/agents/voice_simulator.py`:
> `simulate_voice(scene_text:str, character_meta:dict, model:str) -> dict`.  
> 2) Output:
> ```json
> {
>   "lines":[
>     { "line_id":"L23", "original":"...", "variants": { "A":"...", "B":"...", "C":"..." } }
>   ]
> }
> ```  
> 3) Add endpoints:
>    - `POST /voices/simulate` (returns JSON above),
>    - `POST /voices/choose` with `{scene_id,line_id,choice}` to persist choice in DB (new table `voice_choices`).  
> **Acceptance**: Choices are saved and retrievable for future runs.

## Prompt 39 — Edge Dial Overrides (Character/Scene)

> **Objective:** Fine-grained control of “edge” intensity.  
> **Tasks**  
> 1) Extend project config concept with overrides in DB:
>    - New table `edge_overrides(id PK, scope: "global"|"character"|"scene", ref_id:str|null, value:int)`  
> 2) Extend `POST /passes/run` request to accept optional:
> ```json
> { "edge_overrides": { "global":2, "char_overrides": {"char:MC":3}, "scene_overrides": {"ch02_s03":1} } }
> ```  
> 3) Supervisor computes effective edge for Red-Team using overrides (scene > char > global).  
> **Acceptance**: Red-Team generation respects overrides; API echoes effective edge in response.

## Prompt 40 — Chapter-Level Story Report (Enhanced)

> **Objective:** Enrich chapter report with aggregates and summaries.  
> **Tasks**  
> 1) Extend `GET /reports/chapter/{n}` to include JSON alongside HTML:
> ```json
> {
>   "chapter": 2,
>   "scenes": [...],
>   "metrics_aggregate": { "flesch_avg": ..., "avg_sentence_len": ... },
>   "dialogue_pct_avg": ...,
>   "pacing_distribution": { "short":..., "medium":..., "long":... },
>   "reviewer_summary": { "A":2, "B":3, "C":1, "D":0, "F":0 }
> }
> ```  
> 2) HTML shows tables and brief narrative summary per scene.  
> **Acceptance**: Endpoint returns valid HTML and JSON; saved to `artifacts/reports/ch{n}.html`.

## Prompt 41 — Multi-Agent Debate Mode

> **Objective:** One critique round where agents challenge each other; persist transcript.  
> **Tasks**  
> 1) In `supervisor.py`, after initial agent outputs, run one debate cycle where each agent can post ≤200 tokens critique of others.  
> 2) Compose re-ranking of variants based on critiques.  
> 3) Save transcript to `artifacts/debate/{scene_id}.json`:
> ```json
> { "messages":[ { "agent":"Grim", "text":"...", "ts":"<ISO8601>" } ] }
> ```  
> 4) Add `GET /passes/debate/{scene_id}` to read transcript.  
> **Acceptance**: Debate tab can fetch and render transcript; ranking rationale included in response.

## Prompt 42 — Global Dark Mode & Theme Tokens

> **Objective:** Default dark theme with brand tokens.  
> **Tasks**  
> 1) Tailwind: `darkMode: "class"`. Extend theme with tokens:
>    - Colors: `bg.default #0B0C10`, `bg.panel rgba(13,14,20,0.7)`, `text.primary #E6E6F0`, `text.muted #A0A3B1`, `accent.primary #8A2BE2`, `accent.secondary #00FFFF`, `success #39FF14`, `error #E0115F`, `warning #FFB000`.  
> 2) Fonts via `next/font`: Inter (body), Orbitron (headings).  
> 3) `ui/app/providers/ThemeProvider.tsx` forces dark; optional toggle via `NEXT_PUBLIC_ENABLE_THEME_TOGGLE`.  
> 4) Utilities: `.glass` (panel bg + blur), `.neon-hover` (box-shadow accent).  
> **Acceptance**: App renders in dark mode by default; sample `Card`/`Button` use tokens.

## Prompt 43 — Beatmap Timeline Page (UI)

> **Objective:** Visualize reversals across the manuscript.  
> **Tasks**  
> 1) Create `ui/app/beatmap/page.tsx`.  
> 2) Fetch `GET /reports/beatmap`.  
> 3) Render timeline with `recharts`:
>    - X = percent (0–100),
>    - Scene nodes labeled `chapter:scene_id`,
>    - Cyan bands at 8–11%, violet vertical at 50%,
>    - Tooltip shows scene info + markers.  
> 4) Zoom/scroll, keyboard arrows to jump.  
> **Acceptance**: Responsive chart, loading and error states present.

## Prompt 44 — Reviewer Notes Tab (UI)

> **Objective:** Show persona critiques and grades for a scene.  
> **Tasks**  
> 1) Add `ui/app/scene/[id]/reviewers/page.tsx`.  
> 2) Use reviewer data from the `/passes/run` response (or separate fetch).  
> 3) Cards per persona: icon, critique (collapsible), grade badge (color by grade).  
> 4) Copy-to-clipboard button.  
> **Acceptance**: Tab switcher between Review and Reviewers; empty state when none.

## Prompt 45 — Debate Transcript Tab (UI)

> **Objective:** Render debate chat among agents.  
> **Tasks**  
> 1) Add `ui/app/scene/[id]/debate/page.tsx`.  
> 2) Fetch `GET /passes/debate/{scene_id}`.  
> 3) Virtualized list; colored roles: Lore=cyan, Grim=violet, Dialogue=green, Red-Team=crimson, Supervisor=gray.  
> 4) Sticky auto-scroll with pause on hover; filter by agent.  
> **Acceptance**: Smooth scroll; export `.txt` works.

## Prompt 46 — Voice Simulator Panel (UI)

> **Objective:** Blind-pick dialogue variants and apply as draft diff.  
> **Tasks**  
> 1) Add `ui/app/scene/[id]/voices/page.tsx`.  
> 2) `POST /voices/simulate` → render per-line original + A/B/C options.  
> 3) Selecting A/B/C updates a client-side preview diff; persist via `POST /voices/choose`.  
> 4) “Commit Selected Variants” bundles changes and posts to `/patches/apply` (variant name `voice_draft`).  
> **Acceptance**: Selections persist across reload; commit produces a patch artifact.

## Prompt 47 — Character Settings Page (UI)

> **Objective:** Edit voice tags, wordlists, and edge dial per character.  
> **Tasks**  
> 1) Add `ui/app/characters/[id]/page.tsx`.  
> 2) Fetch `GET /characters/{id}` and update via `POST /characters/{id}` (implement minimal routers if missing).  
> 3) Inputs: tags (chips), preferred/banned words (chips with dedupe), edge slider 0–3.  
> 4) Optimistic save; show last updated.  
> **Acceptance**: Validation prevents overlap of preferred and banned lists.

## Prompt 48 — Reports Dashboard (UI)

> **Objective:** Centralized view of metrics, beatmap, and reviewers.  
> **Tasks**  
> 1) Create `ui/app/reports/page.tsx`.  
> 2) Fetch `GET /reports/chapter/{n}` and `/reports/beatmap`.  
> 3) Widgets:
>    - Radar chart of metrics vs targets,
>    - Beatmap mini strip per chapter,
>    - Reviewer grade matrix (scene × persona).  
> 4) Export HTML/PDF.  
> **Acceptance**: Widgets modular under `ui/components/reports/*`; loading skeletons implemented.

## Prompt 49 — Micro-Interactions & Motion (UI)

> **Objective:** Consistent animations and feedback.  
> **Tasks**  
> 1) Add `ui/components/ui/Motion.tsx` helpers using `framer-motion`.  
> 2) Buttons: ripple + neon pulse on hover/focus.  
> 3) Tabs: animated underline; keyboard shortcuts `1/2/3` to switch variants, `A` to apply patch.  
> 4) Loading states: glitch text (“Compiling Canon…”, etc.).  
> **Acceptance**: Animations are performant (no layout thrash) and respect reduced-motion settings.

## Prompt 50 — Brand Application & Meta (UI)

> **Objective:** Apply brand identity across shell.  
> **Tasks**  
> 1) Header (`ui/app/(shell)/Header.tsx`): slot for logo/wordmark; uses `accent.primary`.  
> 2) Footer: “Writers’ Room X — © J. N. Scott”.  
> 3) Favicon/meta: set theme color, social preview images, and title templates in `layout.tsx`.  
> 4) Env overrides: `NEXT_PUBLIC_ACCENT_PRIMARY`, `NEXT_PUBLIC_ACCENT_SECONDARY` to tweak colors without rebuild.  
> **Acceptance**: Lighthouse color-contrast passes; shell consistent on all pages.

## Part 3/4 - Prompts 51–67

## Prompt 51 — Scene Review Page Enhancements (UI)

> **Objective:** Improve clarity, safety, and data density on the scene review page without adding compare mode.  
> **Tasks**  
> 1) In `ui/app/scene/[id]/page.tsx`, add a right-side “Metrics Panel” with compact badges for each key metric (Flesch, avg sentence length, active verbs %, dialogue %, tone). Green/yellow/red status must reflect thresholds from `/configs/metrics.yaml`.  
> 2) Add a “Canon Receipts” list showing each receipt `{source_path, Lx–Ly}` with a hover popover containing the referenced snippet (rendered monospace, max 10 lines).  
> 3) Add an “Apply Summary” info box above the Apply button: changed lines count, number of receipts touched, and whether any `severity:"block"` findings exist.  
> 4) Disable **Apply Patch** if `diff` is empty **or** any Lore Archivist finding has `severity:"block"`. Tooltip must explain the reason.  
> 5) Add “Download Diff” button per variant to save the unified diff as `<scene_id>_<variant>.diff`.  
> **Acceptance**  
> - Status colors exactly match threshold bands.  
> - Popovers are keyboard accessible (focus/escape).  
> - Apply button reliably disables with a clear tooltip message.

## Prompt 52 — Command Palette (UI)

> **Objective:** Keyboard-driven navigation and actions.  
> **Tasks**  
> 1) Install and configure `cmdk`. Add a global `CommandPalette` component mounted in root layout.  
> 2) Bind `Ctrl/Cmd+K` to open/close.  
> 3) Commands (with handlers):  
>    - Go to Scene… (fuzzy search by `scene_id`, `location`) → navigate to `/scene/[id]`.  
>    - Run Pass (on current scene) → open modal with agents + edge slider → POST `/passes/run`.  
>    - Apply Safe / Apply Bold / Apply Red-Team → POST `/patches/apply`.  
>    - Open Beatmap (`/beatmap`), Open Reports (`/reports`), Open Dashboard (`/dashboard`).  
> 4) Results show path hints and keyboard hints (e.g., `↵` to select).  
> **Acceptance**  
> - Palette opens instantly (<100ms).  
> - All commands work, with success/error toasts.

## Prompt 53 — Notifications & Toaster (UI)

> **Objective:** Centralize transient and persistent notifications reflecting API/job states.  
> **Tasks**  
> 1) Add a Toast provider with variants: `info|success|warning|error` using brand tokens.  
> 2) Standardize messages for: ingest start/complete, pass start/complete/fail, patch apply success/fail, report generation success/fail.  
> 3) Include `request_id` (correlation id) from API responses in error toasts.  
> 4) Persist last 50 notifications in memory; expose a hook `useNotifications()` to list them.  
> **Acceptance**  
> - All network errors trigger error toasts including `request_id`.  
> - Success toasts show concise, action-specific messages.

## Prompt 54 — Access Control & Safe Operations (UI)

> **Objective:** Prevent destructive actions without explicit user consent and support read-only mode.  
> **Tasks**  
> 1) Add confirmation modal before any patch apply. The modal must display: number of changed lines, estimated tokens changed (heuristic OK), and receipt count.  
> 2) Add read-only mode via `NEXT_PUBLIC_READONLY=true` that disables: Run Pass, Apply Patch, Save Settings. Show a header banner “Read-Only Mode”.  
> 3) Respect keyboard shortcuts but block actions in read-only mode with informative toast.  
> **Acceptance**  
> - Confirmation is required for all apply actions.  
> - Read-only mode disables controls consistently and visibly.

## Prompt 55 — Keyboard-First UX (UI)

> **Objective:** Add explicit shortcuts for speed.  
> **Tasks**  
> 1) On `/scene/[id]`:  
>    - `g` then `s` → open “Go to Scene” search.  
>    - `r` then `p` → open Run Pass modal.  
>    - `v 1` / `v 2` / `v 3` → switch to Safe / Bold / Red-Team tabs.  
>    - `a s` → apply Safe patch (still requires confirmation modal).  
> 2) Show a `?` shortcut to open a “Shortcuts” modal listing all keys.  
> **Acceptance**  
> - Shortcuts do not conflict with browser defaults.  
> - Shortcut modal is accessible and dismissible.

## Prompt 56 — Scene Comparison Mode (UI)

> **Objective:** Compare two variants side-by-side.  
> **Tasks**  
> 1) In `/scene/[id]`, add a “Compare” toggle.  
> 2) Provide a selector to choose any two variants among Safe/Bold/Red-Team/current text.  
> 3) Render two diff viewers stacked vertically; synchronize horizontal and vertical scrolling.  
> 4) Add “Show changed lines only” filter.  
> **Acceptance**  
> - Scroll synchronization is smooth.  
> - Filtering hides unchanged context lines while preserving diff integrity.

## Prompt 57 — Scene History Timeline (UI + API)

> **Objective:** Display and revert commit history for a scene’s file.  
> **Backend Tasks**  
> 1) Implement `GET /scenes/{scene_id}/history` returning:  
> ```json
> { "commits":[ { "sha":"...", "msg":"...", "date":"<ISO8601>", "author":"...", "diff_url":"/patches/commit/<sha>.diff" } ] }
> ```  
> 2) Implement `POST /patches/revert` body `{ "scene_id":"...", "commit_sha":"..." }` → revert file to that version; create a new commit with message `Revert <sha>`.  
> **UI Tasks**  
> 3) Add `/scene/[id]/history/page.tsx` with a vertical timeline of commits, click to preview the diff, and a “Revert to This” button (confirmation modal required).  
> **Acceptance**  
> - History loads reliably; revert creates a new commit and updates the scene content.

## Prompt 58 — Global Search Across Codex & Manuscript (UI + API)

> **Objective:** Find references quickly across all documents.  
> **Backend Tasks**  
> 1) Implement `GET /search?q=<term>&type=<codex|manuscript|all>` returning:  
> ```json
> { "results":[ { "id":"<scene_id or doc_id>", "type":"scene|codex", "excerpt":"...", "source_path":"..." } ] }
> ```  
> 2) Use Chroma semantic query (top-k=10) + simple keyword fallback if Chroma unavailable.  
> **UI Tasks**  
> 3) Add `ui/app/search/page.tsx` with a search field, results list, filters for codex/manuscript. Highlight matched terms.  
> **Acceptance**  
> - Empty query is blocked; results link to the appropriate viewer (scene review or codex modal).

## Prompt 59 — Inline Canon Receipts in Diff (UI)

> **Objective:** Annotate changed lines that touch canon receipts.  
> **Tasks**  
> 1) For each variant, map changed line numbers to receipt ranges. If a changed line `n` falls within any `{start_line..end_line}` for the scene’s receipts, show a small receipt icon inline.  
> 2) Hovering the icon opens a popover with `{source_path, Lx–Ly}` snippet and a “Open Source” action (modal with full text).  
> **Acceptance**  
> - Mapping logic is robust to off-by-one discrepancies.  
> - Popover content is correctly tied to the line.

## Prompt 60 — Multi-Scene Batch Pass UI (UI + API)

> **Objective:** Run agent passes for multiple scenes and track progress.  
> **Backend Tasks**  
> 1) Implement `POST /passes/run_batch` body:  
> ```json
> { "scene_ids":["ch01_s01","ch01_s02"], "agents":["lore_archivist","grim_editor","tone_metrics"], "edge_intensity":1 }
> ```  
> Returns: `{ "job_id":"<uuid>" }`.  
> 2) Implement `GET /batch/{job_id}` returning per-scene status and results when available:  
> ```json
> { "job_id":"...", "items":[ { "scene_id":"...", "status":"queued|running|done|error", "result":{...}|null } ] }
> ```  
> **UI Tasks**  
> 3) On `/scenes` page, add “Batch Pass” button → multi-select modal (checkbox list) + agent checkboxes + edge slider → POST, then navigate to `/batch/[job_id]`.  
> 4) Create `/batch/[job_id]/page.tsx` showing a grid with each scene’s Safe/Bold/Red-Team readiness and links to open the scene.  
> **Acceptance**  
> - Live polling updates statuses.  
> - Batch job survives page refresh.

## Prompt 61 — Notifications Center Drawer (UI)

> **Objective:** Persistent notifications feed.  
> **Tasks**  
> 1) Add a right-side drawer accessible via a bell icon and the `n` key.  
> 2) Show the stored notification timeline (from Prompt 53), grouped by date and job type (ingest, pass, apply, report).  
> 3) Each item deep-links to the related page (scene, batch, report).  
> **Acceptance**  
> - Drawer animates smoothly; keyboard shortcut toggles open/close.  
> - Feed shows last 50 items with timestamps.

## Prompt 62 — Split-Screen Editor Mode (UI + API)

> **Objective:** Allow manual edits side-by-side with AI suggestions.  
> **Backend Task**  
> 1) Implement `POST /patches/manual` body:  
> ```json
> { "scene_id":"...", "revised_text":"...", "commit_message":"Manual edit: ..." }
> ```  
> Server computes diff against current file, applies, and commits. Returns `{status, commit_sha, diff}`.  
> **UI Tasks**  
> 2) On `/scene/[id]`, add “Edit Mode” toggle: left = diff viewer (selected variant), right = editable text area initialized with variant-applied text.  
> 3) “Save Manual Edit” posts to `/patches/manual`.  
> **Acceptance**  
> - Edits persist and appear in history.  
> - Diff correctly reflects manual changes.

## Prompt 63 — Chapter Overview Page (UI)

> **Objective:** Provide chapter-level at-a-glance status.  
> **Tasks**  
> 1) Create `ui/app/chapters/[id]/page.tsx`.  
> 2) Fetch all scenes for the chapter (`GET /scenes?chapter=<id>`).  
> 3) Table columns: Scene ID, Word Count, Metrics Score (color), Last Pass Date, Unresolved Canon Blocks (#), Actions.  
> 4) “Export Chapter” button to download a single concatenated markdown file. Implement `GET /export/chapter/{id}.md`.  
> **Acceptance**  
> - Rows link to scene pages.  
> - Export produces a valid `.md` with scenes in order.

## Prompt 64 — Project Dashboard (UI)

> **Objective:** High-level control panel.  
> **Tasks**  
> 1) Create `ui/app/dashboard/page.tsx` and make it the default landing page (`/`).  
> 2) Widgets (fetch from existing endpoints):  
>    - Counts: total scenes, total characters, % scenes “within metrics” (green).  
>    - Beatmap mini preview (sparkline).  
>    - Reviewer grade distribution (bar chart).  
>    - Latest commits list (from `/scenes/{id}/history` for recent scenes; or add `GET /commits/recent`).  
> 3) Quick actions: Run Batch Pass, Open Beatmap, Open Reports.  
> **Acceptance**  
> - Widgets render with loading skeletons; all links functional.

## Prompt 65 — Scene Tagging & Filters (UI + API)

> **Objective:** Organize scenes by tags (arcs, subplots, locations).  
> **Backend Tasks**  
> 1) Add table `scene_tags(scene_id TEXT, tag TEXT, PRIMARY KEY(scene_id, tag))`.  
> 2) Implement:  
>    - `GET /scenes/{id}/tags` → `{ "tags":["..."] }`  
>    - `POST /scenes/{id}/tags` body `{ "tags":["..."] }` (replace entire set).  
> **UI Tasks**  
> 3) Add tag editor (chip input) to scene sidebar.  
> 4) Add filter by tags on `/scenes`.  
> **Acceptance**  
> - Tags persisted; filter narrows the list correctly.

## Prompt 66 — Export Center (UI + API)

> **Objective:** Centralize exporting diffs, reports, and project state.  
> **Backend Tasks**  
> 1) Implement:  
>    - `POST /export/diffs` body `{ "scene_ids":["..."] }` → returns ZIP of diffs.  
>    - `GET /export/project.json` → serialized project (scenes, characters, configs).  
>    - `GET /export/reports.zip` → ZIP of all HTML chapter reports.  
> **UI Tasks**  
> 2) Add `ui/app/export/page.tsx` with three export cards and progress indicators.  
> **Acceptance**  
> - Files download with proper MIME types and file names.

## Prompt 67 — Custom Theme Editor (UI + API)

> **Objective:** Allow live tweaking of accent colors and save configuration.  
> **Backend Task**  
> 1) Implement `POST /settings/theme` body:  
> ```json
> { "primary":"#8A2BE2", "secondary":"#00FFFF", "success":"#39FF14", "error":"#E0115F" }
> ```  
> Persist to a config file `data/ui_theme.json`.  
> **UI Tasks**  
> 2) Create `ui/app/settings/theme/page.tsx` with color pickers for primary/secondary/success/error and a live preview panel.  
> 3) Save to backend and also store a copy in `localStorage` to apply immediately.  
> **Acceptance**  
> - Theme updates apply without page reload.  
> - Saved config survives server restart.

## Part 4/4 - Prompts 68–91

## Prompt 68 — Alternative Endings Generator (API + Agent)

> **Objective:** Generate 2–3 canon-consistent alternative endings with synopsis + sample scene.  
> **Files:** `api/app/agents/alt_endings.py`, router updates in `api/app/routers/creative.py` (new file).  
> **Agent Function:**  
> `run_alt_endings(codex_context:dict, manuscript_text:str, model:str, num_variants:int=3) -> dict`  
> **System prompt (embed):** “Generate plausible alternative endings consistent with canon. Return concise synopses (≤500 words each) and a short sample scene (1–2 paragraphs). Do not contradict established facts.”  
> **Endpoint:** `POST /creative/alt_endings`  
> **Request JSON:**
> ```json
> { "num_variants": 3, "include_samples": true }
> ```
> (Server loads codex + manuscript content internally; ignore if missing.)  
> **Response JSON:**
> ```json
> {
>   "variants": [
>     { "id": "alt_001", "label": "Tragic Ascension", "synopsis": "...", "sample": "..." },
>     { "id": "alt_002", "label": "Quiet Revolt", "synopsis": "...", "sample": "..." }
>   ]
> }
> ```
> **Artifacts:** Save each as `artifacts/creative/alt_endings/{id}.json`.  
> **Acceptance:** Returns 1–3 endings with nonempty `synopsis`; `sample` present when `include_samples=true`.

## Prompt 69 — Theme Analyzer Agent (API + Agent)

> **Objective:** Detect themes, motif frequencies, and produce a narrative essay.  
> **Files:** `api/app/agents/theme_analyzer.py`, extend `creative.py`.  
> **Agent Function:**  
> `run_theme_analyzer(manuscript_text:str, codex_context:dict, model:str) -> dict`  
> **System prompt:** “Analyze manuscript for themes (e.g., power, rebellion, survival). Map frequency across scenes and chapters; write a 400–700 word essay summarizing evolution.”  
> **Endpoint:** `GET /creative/themes`  
> **Response JSON:**
> ```json
> {
>   "themes": [
>     { "name": "rebellion", "frequency": 42, "scenes": ["ch01_s01","ch01_s03","ch02_s02"] },
>     { "name": "intimacy", "frequency": 18, "scenes": ["ch01_s02"] }
>   ],
>   "essay": "..."
> }
> ```
> **Acceptance:** At least 3 themes detected; essay length within range.

## Prompt 70 — AI Co-Author Personas (API + Agent + Config)

> **Objective:** Rewrite a scene in the style of a chosen co-author persona.  
> **Files:** `api/app/agents/co_author.py`, `configs/personas.yaml`, extend `creative.py`.  
> **Config (`configs/personas.yaml`) Example:**
> ```yaml
> personas:
>   romantic_realist: { label: "Romantic Realist", temp: 0.7 }
>   brutalist_poet:   { label: "Brutalist Poet", temp: 0.8 }
>   cyberpunk_satirist: { label: "Cyberpunk Satirist", temp: 0.9 }
> ```
> **Agent Function:**  
> `run_co_author(scene_text:str, persona_key:str, persona_cfg:dict, model:str) -> dict`  
> **System prompt:** “Roleplay as {label}. Rewrite the scene preserving plot beats and canon. Produce a unified diff only and a 2–4 bullet rationale.”  
> **Endpoint:** `POST /creative/coauthor`  
> **Request JSON:**
> ```json
> { "scene_id": "ch01_s02", "persona": "cyberpunk_satirist" }
> ```
> **Response JSON:**
> ```json
> { "diff": "<unified diff>", "rationale": ["...","..."], "persona": "cyberpunk_satirist" }
> ```
> **Acceptance:** Diff applies cleanly; persona key validated against `personas.yaml`.

## Prompt 71 — Cross-Genre Reimagine (API + Agent)

> **Objective:** Reimagine a scene in a different genre; save as alt text (not a diff).  
> **Files:** `api/app/agents/genre_reimagine.py`, extend `creative.py`.  
> **Agent Function:**  
> `run_genre_reimagine(scene_text:str, genre:str, model:str) -> dict`  
> **Allowed genres:** `"noir"|"horror"|"romance"|"farce"|"epic_fantasy"|"literary"`.  
> **Endpoint:** `POST /creative/reimagine`  
> **Request JSON:**
> ```json
> { "scene_id": "ch01_s02", "genre": "noir" }
> ```
> **Response JSON:**
> ```json
> { "label": "noir", "text": "...", "rationale": "..." }
> ```
> **Artifacts:** Write `artifacts/creative/reimagine/{scene_id}_{genre}.md`.  
> **Acceptance:** Nonempty `text` returned; file written.

## Prompt 72 — Symbolism & Imagery Mapper (API + Agent)

> **Objective:** Extract existing symbols and suggest new inserts.  
> **Files:** `api/app/agents/symbolism_mapper.py`, extend `creative.py`.  
> **Agent Function:**  
> `map_symbols(scene_text:str, codex_context:dict, model:str) -> dict`  
> **System prompt:** “List symbolic objects/colors/images; map to themes; propose 2–3 new symbolic inserts consistent with canon.”  
> **Endpoint:** `POST /creative/symbols`  
> **Request JSON:**
> ```json
> { "scene_id": "ch01_s02" }
> ```
> **Response JSON:**
> ```json
> {
>   "symbols": [
>     { "item": "cracked lens", "meaning": "distorted truth", "linked_scenes": ["ch01_s01","ch02_s03"] }
>   ],
>   "suggestions": [
>     { "item": "static moths", "meaning": "attraction to danger", "where": "ch01_s02 L45-L60" }
>   ]
> }
> ```
> **Acceptance:** At least one existing symbol OR one suggestion returned.

## Prompt 73 — Dreamscape Generator (API + Agent)

> **Objective:** Generate a surreal dream/vision for a character + interpretation.  
> **Files:** `api/app/agents/dreamscape.py`, extend `creative.py`.  
> **Agent Function:**  
> `run_dreamscape(character_id:str, codex_context:dict, model:str) -> dict`  
> **System prompt:** “Compose a fragmented, poetic dream sequence rooted in character fears/desires; provide a short interpretation tied to themes.”  
> **Endpoint:** `POST /creative/dreamscape`  
> **Request JSON:**
> ```json
> { "character_id": "char:MC" }
> ```
> **Response JSON:**
> ```json
> { "sequence": "...", "interpretation": "..." }
> ```
> **Artifacts:** Save `artifacts/creative/dreams/{character_id}_{timestamp}.md`.  
> **Acceptance:** Nonempty `sequence` and `interpretation`.

## Prompt 74 — Subplot Weaver (API + Agent)

> **Objective:** Propose a subplot woven through multiple scenes.  
> **Files:** `api/app/agents/subplot_weaver.py`, extend `creative.py`.  
> **Agent Function:**  
> `run_subplot(manuscript_context:dict, seed_scene_id:str, model:str, span:int=4) -> dict`  
> **Endpoint:** `POST /creative/subplot`  
> **Request JSON:**
> ```json
> { "seed_scene_id": "ch01_s02", "span": 4 }
> ```
> **Response JSON:**
> ```json
> {
>   "subplot_id": "sp_001",
>   "description": "...",
>   "anchor_scenes": ["ch01_s02","ch01_s04","ch02_s01","ch02_s03"]
> }
> ```
> **Acceptance:** 3–5 anchor scenes returned; IDs exist in DB.

## Prompt 75 — Character POV Flip (API + Agent)

> **Objective:** Rewrite scene from another character’s POV; return alt text + diff.  
> **Files:** `api/app/agents/pov_flip.py`, extend `creative.py`.  
> **Agent Function:**  
> `run_pov_flip(original_scene_text:str, new_character_id:str, model:str) -> dict`  
> **System prompt:** “Rewrite the scene from {character} POV, preserving factual canon but shifting perception and emotional framing. Provide full alt text and a unified diff against the original.”  
> **Endpoint:** `POST /creative/pov_flip`  
> **Request JSON:**
> ```json
> { "scene_id": "ch01_s02", "new_character_id": "char:ALLY" }
> ```
> **Response JSON:**
> ```json
> { "alt_text": "...", "diff": "<unified diff>", "notes": "Perspective bias: envy → pity." }
> ```
> **Acceptance:** Diff applies cleanly to produce the alt text content.

## Prompt 76 — Dialogue Improvisation Sandbox (API + Agent)

> **Objective:** Generate branching dialogue responses for selected lines.  
> **Files:** `api/app/agents/dialogue_improv.py`, extend `creative.py`.  
> **Agent Function:**  
> `improv_dialogue(scene_snippet:str, character_ids:list[str], model:str, max_branches:int=3) -> dict`  
> **Endpoint:** `POST /creative/dialogue_improv`  
> **Request JSON:**
> ```json
> { "scene_id": "ch01_s02", "line_range": { "start": 20, "end": 40 }, "character_ids": ["char:MC","char:ALLY"] }
> ```
> **Response JSON:**
> ```json
> {
>   "lines": [
>     { "line_id": "L23", "speaker": "char:MC", "options": ["...", "...", "..."] },
>     { "line_id": "L24", "speaker": "char:ALLY", "options": ["...", "..."] }
>   ]
> }
> ```
> **Acceptance:** Each returned line has ≥1 option and valid speaker IDs.

## Prompt 77 — Moodboard Tag Extractor (API + Agent)

> **Objective:** Extract visual tags and prompts for art tools.  
> **Files:** `api/app/agents/moodboard.py`, extend `creative.py`.  
> **Agent Function:**  
> `make_moodboard(scene_text:str, model:str) -> dict`  
> **Endpoint:** `POST /creative/moodboard`  
> **Request JSON:**
> ```json
> { "scene_id": "ch01_s02" }
> ```
> **Response JSON:**
> ```json
> { "tags": ["neon decay","rusted cathedral","blood-haloed sunrise"], "prompts": ["...","..."] }
> ```
> **Acceptance:** At least 5 tags OR 3 prompts returned.

## Prompt 78 — Foreshadow Auditor (API + Agent)

> **Objective:** Identify existing foreshadows and suggest earlier insertions.  
> **Files:** `api/app/agents/foreshadow_auditor.py`, extend `creative.py`.  
> **Agent Function:**  
> `audit_foreshadow(manuscript_context:dict, scene_id:str, model:str) -> dict`  
> **Endpoint:** `POST /creative/foreshadow`  
> **Request JSON:**
> ```json
> { "scene_id": "ch02_s03" }
> ```
> **Response JSON:**
> ```json
> {
>   "foreshadows": [ { "scene_id": "ch01_s01", "line": 57, "hint": "..." } ],
>   "insert_suggestions": [
>     { "scene_id": "ch01_s02", "lines": "L20-L30", "hint": "..." }
>   ]
> }
> ```
> **Acceptance:** Either list is nonempty; scene IDs validated.

## Prompt 79 — Generative Chaos Agent (API + Agent)

> **Objective:** Provide disruptive “what if” provocations (ideas only).  
> **Files:** `api/app/agents/chaos.py`, extend `creative.py`.  
> **Agent Function:**  
> `run_chaos(scene_text:str, model:str, n:int=8) -> dict`  
> **System prompt:** “Propose high-impact ‘what if’ changes to premise/character dynamics. Do not produce diffs or final prose. Ideas only.”  
> **Endpoint:** `POST /creative/chaos`  
> **Request JSON:**
> ```json
> { "scene_id": "ch01_s02", "n": 8 }
> ```
> **Response JSON:**
> ```json
> { "wtf_moments": ["What if the MC dies here?", "What if the antagonist is an ally?", "..."] }
> ```
> **Acceptance:** Returns 5–12 ideas; strictly no diff field.

## Prompt 80 — Alt Endings Page (UI)

> **Objective:** Display generated alternative endings.  
> **Route:** `ui/app/creative/alt_endings/page.tsx`  
> **Tasks:**  
> 1) On load, POST `/creative/alt_endings` with `{ "num_variants": 3, "include_samples": true }`.  
> 2) Render each variant as a card with `label`, `synopsis` (scrollable), and expandable `sample`.  
> 3) Provide “Download .md” button that saves `synopsis + sample` as `<id>.md`.  
> **Acceptance:** Handles loading/error; supports 1–3 cards.

## Prompt 81 — Themes Dashboard (UI)

> **Objective:** Visualize themes and show essay.  
> **Route:** `ui/app/creative/themes/page.tsx`  
> **Tasks:**  
> 1) GET `/creative/themes`.  
> 2) Render bar/heatmap chart of `themes[].frequency`; clicking a bar filters the scene list.  
> 3) Essay panel shows `essay` with scroll; copy button.  
> **Acceptance:** Chart and essay render; empty state handled.

## Prompt 82 — Co-Author Personas Panel (UI)

> **Objective:** Run persona rewrite and show diff.  
> **Route:** `ui/app/scene/[id]/coauthor/page.tsx`  
> **Tasks:**  
> 1) Load persona list from `configs/personas.yaml` (served via a simple `GET /configs/personas` endpoint—implement if missing).  
> 2) Persona dropdown → POST `/creative/coauthor`.  
> 3) Show diff and rationale; export `.patch`.  
> **Acceptance:** Persona key validated; diff viewer scrolls smoothly.

## Prompt 83 — Genre Reimagination Page (UI)

> **Objective:** Render reimagined text in selected genre.  
> **Route:** `ui/app/scene/[id]/reimagine/page.tsx`  
> **Tasks:**  
> 1) Genre select with allowed values.  
> 2) POST `/creative/reimagine`.  
> 3) Display `text` in a reader view; “Save as Variant” → write to artifacts (trigger via `POST /creative/reimagine` server-side write already done).  
> **Acceptance:** Distinct accent color per genre (map in UI); export link available.

## Prompt 84 — Symbolism Mapper (UI)

> **Objective:** Show existing symbols vs suggested ones.  
> **Route:** `ui/app/scene/[id]/symbols/page.tsx`  
> **Tasks:**  
> 1) POST `/creative/symbols`.  
> 2) Two lists: “Existing Symbols” and “Suggested Inserts”; each item shows `item`, `meaning`, and linked scenes (hover to reveal list).  
> **Acceptance:** Clicking a linked scene navigates to that scene’s page.

## Prompt 85 — Dreamscape Viewer (UI)

> **Objective:** Render dream sequence with interpretation.  
> **Route:** `ui/app/characters/[id]/dreams/page.tsx`  
> **Tasks:**  
> 1) POST `/creative/dreamscape`.  
> 2) Show `sequence` with stylized typesetting and a panel for `interpretation`.  
> 3) Download `.md` button.  
> **Acceptance:** Handles multiple runs with timestamps.

## Prompt 86 — Subplot Weaving Tool (UI)

> **Objective:** Visualize subplot graph and export JSON.  
> **Route:** `ui/app/creative/subplot/page.tsx`  
> **Tasks:**  
> 1) POST `/creative/subplot` with a scene picker (seed) and span.  
> 2) Render graph (visx): nodes = scenes; edges = subplot relationships; hover highlights path.  
> 3) Export button downloads the returned JSON.  
> **Acceptance:** Graph pan/zoom responsive.

## Prompt 87 — POV Flip Viewer (UI)

> **Objective:** Compare original vs flipped POV.  
> **Route:** `ui/app/scene/[id]/pov_flip/page.tsx`  
> **Tasks:**  
> 1) Character dropdown → POST `/creative/pov_flip`.  
> 2) Split view: left = original, right = alt_text; diff viewer toggle to see unified diff.  
> 3) Notes panel shows perspective shifts.  
> **Acceptance:** Diff and alt_text remain synchronized.

## Prompt 88 — Dialogue Improv Sandbox (UI)

> **Objective:** Branching dialogue experiment tool.  
> **Route:** `ui/app/scene/[id]/dialogue_improv/page.tsx`  
> **Tasks:**  
> 1) POST `/creative/dialogue_improv` with optional line range.  
> 2) Render a tree: each line node shows `speaker` and options; clicking an option advances a preview path.  
> 3) “Export Path” saves selected branch as an alt dialogue scene `.md`.  
>  **Acceptance:** Tree collapses/expands smoothly; export includes ordered lines.

## Prompt 89 — Moodboard Tag Extractor (UI)

> **Objective:** Copy/paste visual tags and prompts for art tools.  
> **Route:** `ui/app/scene/[id]/moodboard/page.tsx`  
> **Tasks:**  
> 1) POST `/creative/moodboard`.  
> 2) Render tags as chips with copy buttons; render prompts as list with “Copy All”.  
> **Acceptance:** Clipboard ops work; handles long lists.

## Prompt 90 — Foreshadow Auditor Panel (UI)

> **Objective:** Show detected foreshadows and insertion points on a timeline.  
> **Route:** `ui/app/scene/[id]/foreshadow/page.tsx`  
> **Tasks:**  
> 1) POST `/creative/foreshadow`.  
> 2) Render a timeline strip with markers; clicking a suggestion focuses the target scene and line range.  
> **Acceptance:** Timeline is keyboard navigable; deep-links function.

## Prompt 91 — Chaos Agent “WTF” Panel (UI)

> **Objective:** Surface disruptive ideas clearly marked as non-patch suggestions.  
> **Route:** `ui/app/scene/[id]/chaos/page.tsx`  
> **Tasks:**  
> 1) POST `/creative/chaos`.  
> 2) Render `wtf_moments` as cards with glitch animation and a red accent; each card has “Export as Prompt” to copy idea text.  
> 3) Warning banner: “Experimental ideas. Not applied to manuscript.”  
> **Acceptance:** No apply buttons present; copy works; banner always visible.

---


# End of prompts (1–91)
