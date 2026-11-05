# TODO — feature requests (added 2026-11-05)

Requested features not yet in `PLAN.md`. Each one is weighed against the deadline (09.11.2026) and the scope-cut order in `CLAUDE.md` §3.12 before it is started.

## 1. Click on the map → EkoSkor for that point

**Goal:** click anywhere on the map and get the same card as when typing an address.

- The address page already works for any point: `/adresa?lat=…&lon=…` without `a=` shows "Odabrana točka na karti". A map click only has to navigate there.
- Add the click to the address page map. Optionally also add a map to the home page.
- Points outside the City of Zagreb already get the "izvan Grada Zagreba" message (`/api/profile` → 422).
- Keyboard users need an equivalent: the search box covers it. Say so in the map label.
- Optional: reverse-geocode the clicked point to the nearest address in `data/addresses.parquet`, to show a label. No external service.
- Estimate: small (≈ 1 h incl. the browser check).

## 2. Social index: restaurants, cafés, clubs

**Goal:** how lively the area is: places to eat, drink and go out within walking distance.

- **Data:** OpenStreetMap via Overpass (`amenity=restaurant|cafe|bar|pub|nightclub`), ODbL, like `osm-reciklaza`. Not a public-sector dataset, so state that in `docs/data-sources.md`. Check data.zagreb.hr / data.gov.hr for an official register of food and drink businesses first: `TODO(verify)`.
- New pipeline script (`scripts/fetch_social.py` → `data/social.geojson`), a source in `sources.py` + `docs/data-sources.md`, and a layer in the profile (counts within 300 m / 500 m per category, nearest of each).
- **Decision needed (human):**
  - Does it go into EkoSkor or stay a separate info row? Into EkoSkor = new weights, `docs/ekoskor.md` and `test_ekoskor.py` change, heatmap rebuild.
  - Is a nightclub nearby good or bad? For "lively" it is a plus, for noise / sleep a minus. Suggest: separate row "Društveni život", not scored.
  - Fit with Challenge B (*Okoliš i održivi prostor*): frame it as the walkable "15-minute city", not nightlife.
- Estimate: medium (≈ ½ day incl. pipeline, layer, card row, map layer).

## 3. Air quality index from DHMZ

**Goal:** use the DHMZ (Državni hidrometeorološki zavod) air quality data for the index.

- Today: the score uses the City stations' 2023 PM10 mean (`zg-zrak-mjerenja`). The live index comes from the national INSPIRE WFS on servisi.azo.hr (`rh-zrak-indeks`), shown as extra information with `scale_verified: false`.
- **To verify first (`TODO(verify)`, nothing assumed):**
  - Which DHMZ dataset or service is meant: name, URL, data.gov.hr record.
  - Licence as stated.
  - Format (API / WFS / CSV), update frequency, history length.
  - Which stations are in Zagreb, and which pollutants or index.
  - The index scale (classes, pollutants). This would also resolve `scale_verified`.
  - How it relates to the servisi.azo.hr network (the same stations or different ones).
- If it is current and has history, it could replace the 2023 City data as the score basis. That changes `docs/ekoskor.md`, `test_ekoskor.py` and the heatmap, and removes the "data from 2023" caveat.
- Estimate: depends on the source; ≈ 1–2 h to verify, then ½ day to integrate.

## 4. Notifications about real-time events (added 2026-11-05)

**Goal:** tell the user about events at their address, e.g. **collection dates for plastic waste** (and paper, bio, bulky waste). Possibly also air quality alerts or flood warnings. The request says "the bot can notify", so this could be part of the AI assistant (§5), but it does not need AI.

- **Data, to verify first (`TODO(verify)`, nothing assumed):**
  - Is there an open dataset or service with waste collection schedules per street or district? Look on data.zagreb.hr / data.gov.hr. The operator is Zagrebački holding – Podružnica Čistoća (named in `zg-reciklaza`). Record publisher, licence, format, update frequency and coverage.
  - Air alerts: `rh-zrak-indeks` (national index, already queried live) could trigger "air quality poor today", but the index scale is still unverified (`scale_verified: false`).
  - Flood warnings: which institution publishes real-time warnings, and is it open data? `TODO(verify)`.
- **Privacy conflict (`CLAUDE.md` §2.7):** "no user accounts and no stored addresses on the server". Push or e-mail notifications need a stored subscription with an address, so they break this rule. Options:
  1. **Calendar file (.ics) download** for the address: the browser builds it from the schedule and nothing is stored on the server. Works with any phone calendar. Recommended first step.
  2. Web Push with a subscription stored on the server: needs a privacy policy, consent and deletion. Much more work.
  3. Show "next collection: Tuesday, plastic" on the card only (no notification).
- **Decision needed (human):** which channel; whether it is in scope for the datathon or "daljnji razvoj" (`docs/daljnji-razvoj.md`).
- Estimate: option 3 ≈ ½ day once a dataset exists; option 1 + ½ day; option 2 several days. Without an open schedule dataset, it cannot be built.

## 5. AI assistant: deferred (decision 2026-11-05)

**Decision:** as of 2026-11-05 the AI assistant (`PLAN.md` Phase 4) is **not built** for the datathon submission. We may implement it later. This section keeps everything needed to do that. Nothing AI-related had been implemented; the only traces removed from the app were an empty `backend/app/llm/` folder, the AI variables in `.env.example` and one sentence in `README.md`.

### 5.1 What it was meant to do

- Answer questions in Croatian about the address **only from the fetched data**, citing the source (`source_id` / source name) of every claim, and say "nemam taj podatak" when the data is missing. Examples: *"Mogu li spavati s otvorenim prozorom?"*, *"Treba li mi osiguranje od poplave?"*, *"Kamo s krupnim otpadom?"*.
- Never invent numbers; never give legal, insurance, medical or real-estate pricing advice (point to the right institution instead).
- **Compare summary:** 3–4 sentences under the compare view, summarising the differences between two addresses. One non-chat call, cached per address pair.
- Answers stream token by token (perceived latency ≈ 0).

### 5.2 Design (from `CLAUDE.md` §2.5 and `PLAN.md` Phase 4)

- **Files:** `backend/app/llm/provider.py` (`LLMProvider`, `AnthropicProvider`, `OllamaProvider`), `backend/app/llm/prompt.py` (Croatian system prompt), `backend/app/llm/tools.py`, router `backend/app/routers/chat.py`, `backend/tests/chat_cases.yaml`.
- **System prompt:** Croatian, friendly, short (≤ 5 sentences unless asked for more). Use only tool results. Every factual claim ends with the source name in brackets.
- **Tools** (arguments validated with pydantic): `get_profile(lat, lon)`, `compare(a, b)`, `explain_layer(layer)` (what the metric means, thresholds; text from `docs/ekoskor.md`), `nearest_facility(type, lat, lon)`. The backing services already exist: `services/profile.build_profile`, `services/compare.compare`, the layer services and `/api/layers/{name}`.
- **Grounding check:** after the answer, check that every number in it appears in the tool results; if not, regenerate once, then replace with a safe fallback.
- **Provider abstraction:** `LLMProvider.chat(messages, tools, stream=True)`, selected by `LLM_PROVIDER=anthropic|ollama`. Both providers must pass `chat_cases.yaml`, or the README says which one does not.
- **Limits:** 20 messages per session, 500 characters per message, 30 s timeout.
- **API:** `POST /api/chat` with `{ "lat", "lon", "message", "history" }` → streamed answer with citations (Server-Sent Events).
- **Config to restore in `.env.example`:**
  ```
  # --- AI assistant ---
  # anthropic | ollama
  LLM_PROVIDER=anthropic
  ANTHROPIC_API_KEY=
  OLLAMA_BASE_URL=http://localhost:11434/v1
  ```
  Add `LLM_MODEL` too, so the model can be switched without code changes.
- **Frontend:** `src/components/chat/` (`AssistantPanel`, `MessageBubble`, `SuggestedQuestions`), a panel with 4 suggested questions as buttons on the address page; `AiSummary` under `CompareView` (slot: after the layer rows in `components/compare/CompareView.tsx`). All strings in `i18n/hr.ts`; loading, empty and error states; streaming text with `aria-live`.

### 5.3 Tests and quality bar

- `backend/tests/chat_cases.yaml`: 10 scripted questions with expected content. Target ≥ 8/10 correct and **10/10 with no invented number**. Must include:
  - „Mogu li spavati s otvorenim prozorom?” → mentions L<sub>night</sub> and the WHO guidance (45 dB)
  - „Treba li mi osiguranje od poplave?” → states the flood zone and the source (Hrvatske vode), no insurance advice
  - „Kamo s krupnim otpadom?” → names the nearest recycling yard and its distance
  - „Kolika je cijena kvadrata?” → says it does not have that data
- Re-run `chat_cases.yaml` after any change to `prompt.py`, `tools.py` or the grounding check, and state the result.
- Playwright golden path then includes "ask the assistant" (search → card → ask → compare).

### 5.4 Model and cost (estimate of 2026-11-05)

Prices per million tokens (input / output, from the price table of 2026-10-06; check the Anthropic pricing page): **Claude Opus 5.5** $4 / $20, **Claude Sonnet 5.5** $2 / $10, **Claude Haiku 5.5** $0.10 / $0.50.

One question ≈ 2 model calls ≈ 15 000 input + 1 000 output tokens, mostly the address profile in the prompt. Estimated per question: Opus 5.5 ~$0.08, Sonnet 5.5 ~$0.04, Haiku 5.5 ~$0.002. About 600 questions (development, evals, demo recording, judges) ≈ $50 / $25 / $1.

Plan: start with Opus 5.5 and **$25 credit + a monthly spend limit** in the Console. Run `chat_cases.yaml` on Opus 5.5 and Sonnet 5.5 (≈ $1–2), then pick. Cost levers: trim the profile sent to the model (no 120-value air history for a noise question), prompt caching of the system prompt + tools, low effort for chat, and cached answers for the scripted demo questions. Ollama (local, open source, e.g. `qwen2.5:7b` as in `PLAN.md`) is the free fallback; it is slower and weaker in Croatian.

### 5.5 Everything that depends on it (restore when implementing)

| Where | What changes with the assistant deferred |
|---|---|
| `CLAUDE.md` §1.1 items 4–5 | Assistant and the compare AI summary are deferred (note added) |
| `CLAUDE.md` §1.2 rubric, Inovativnost (5 pts) | The planned argument was "LLM agent with tool use over open geodata". Without it, innovation must rest on other things (data fusion into one score, façade noise rule, map tile proxy, compare view) |
| `CLAUDE.md` §1.3 | "Grounded, never invented" still applies to every number on screen; "AI answers stream token by token" no longer applies |
| `CLAUDE.md` §1.4 tech stack, AI row | No LLM in the stack for now |
| `CLAUDE.md` §2.1 layout | `backend/app/llm/`, `routers/chat`, `tests/chat_cases.yaml`, `frontend/src/components/chat/` not created |
| `CLAUDE.md` §2.5 Agent design | Whole section on hold (kept as the spec, see 5.2) |
| `CLAUDE.md` §2.6 | No assistant evals; the Playwright golden path is search → card → compare |
| `CLAUDE.md` §3.7 | Rule on prompt/tools changes on hold |
| `CLAUDE.md` §3.11 | "Cached AI answers for the scripted questions" not needed |
| `CLAUDE.md` §3.12 | "AI assistant never cut" no longer applies; address card and map are still never cut |
| `PLAN.md` overview, goals, prerequisites (API key, Ollama), tech stack, architecture diagram (`POST /api/chat`, LLM box), API table | Marked deferred |
| `PLAN.md` Phase 4 (all items) | Deferred |
| `PLAN.md` Phase 5: assistant panel; AI summary under compare | Deferred; compare view is done without the summary |
| `PLAN.md` Phase 6: E2E golden path | Without "ask the assistant" |
| `PLAN.md` Phase 7: architecture doc | No LLM component. The list of **AI tools used** is still mandatory (Rules §VIII) because AI coding tools were used to build the app |
| `PLAN.md` Phase 8: video script "AI question" | Replace with another demo moment (e.g. map layers or the city view) |
| `PLAN.md` §6 success criteria: AI answers, compare AI summary, `LLM_PROVIDER=ollama` | Deferred |
| `PLAN.md` risks: "LLM hallucinates data"; scope-cut row | Not applicable for now |
| `PLAN.md` rubric mapping, Innovation row (`backend/llm/`, demo AI questions) | Needs a new argument |
| `README.md` intro sentence | AI assistant removed from the description |
| `.env.example` | AI variables removed (block above) |
| §4 notifications ("bot can notify") | Can be built without AI; if the assistant comes back, it could also answer "kada je odvoz plastike?" from the same data |
