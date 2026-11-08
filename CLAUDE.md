# CLAUDE.md — EkoAdresa

> Environmental profile of any address for Croatian citizens. Built for the **Datathon Portala otvorenih podataka 2026**, Challenge B (*Okoliš i održivi prostor*).
> **Hard deadline: submission by email to open.data@mpudt.hr by 09.11.2026 at 24:00.** Internal target: submitted by 20:00. Every decision in this repo is weighed against that date.

---

## 1. Project Overview & Principles

### 1.1 What we are building
The user types an address and instantly sees **what it is like to live there** environmentally. Data that already exists in public GIS services (flood maps, noise maps, air quality stations) is buried where an ordinary person never looks. EkoAdresa turns it into one clear answer: *"Is this a good place to live, and why?"* Typical moment: choosing a flat to rent or buy, a kindergarten or a school.

1. **Search** — address autocomplete (local index of OpenStreetMap addresses, City of Zagreb) plus 3 example addresses for a quick demo.
2. **Address card** — **EkoSkor 0–100** and a traffic-light row per layer, each with one plain Croatian sentence and its data source:
   - **Poplave** — inside a high / medium (100-year) / low probability flood zone, or outside all zones (Hrvatske vode).
   - **Buka** — L<sub>den</sub> and L<sub>night</sub> in dB compared with WHO guidance (strategic noise maps).
   - **Zrak** — nearest monitoring station, distance, latest index, 30-day history chart.
   - **Zelena mobilnost** — ZET stops within 300 m / 500 m, nearest stop; nearest City bike path (decision 2026-11-06).
   - **Zelenilo** — nearest park or forest ≥ 0.5 ha (decision 2026-11-06).
   - **Otpad** was removed from the score (decision 2026-11-08); recycling yards and green islands stay as map layers.
3. **Map** — address marker, 500 m radius, toggleable layers (flood zones, noise, stations, yards, stops).
4. **AI assistant** — answers questions in Croatian (*"Mogu li spavati s otvorenim prozorom?"*, *"Treba li mi osiguranje od poplave?"*) **only from the fetched data**, citing the source of every claim. If the data is not there, it says so.
5. **Compare two addresses** — two cards side by side, differences highlighted, AI summary in 3–4 sentences. This is the strongest demo moment.

> **Decision 2026-11-05:** the AI assistant (item 4) and the AI summary in item 5 are **deferred** and not part of the current build. Everything about them (design, tests, costs, every dependent place in this file and `PLAN.md`) is recorded in `TODO.md` §5. Sections 1.4 (AI row), 2.5, 3.7 and the AI parts of 1.3 and 3.11 are on hold until then.
6. **City view** — heatmap of EkoSkor on a 250 × 250 m grid over Zagreb, for public bodies.
7. **"Kako računamo?"** — the EkoSkor formula and every source, public and readable.

**Pilot area: City of Zagreb** (richest data). The architecture and docs describe how it extends to all of Croatia.

### 1.2 Why it scores (rubric, 60 pts)
| Criterion | Pts | How we earn it |
|---|---|---|
| Upotreba otvorenih podataka | 5 | Live **OGC WMS/WFS** calls to public-sector services + datasets downloaded from data.gov.hr / data.zagreb.hr; provenance shown in UI |
| Povezivanje podataka | 5 | 5+ datasets from 3+ publishers (Hrvatske vode, Grad Zagreb, ministry INSPIRE services, ZET) fused into one profile and one score |
| Relevantnost | 5 | Covers 5 of 6 examples in the Challenge B text: air, waste, green transport, flood risk, noise |
| Utjecaj | 5 | Every citizen choosing where to live; city gets a map of critical zones |
| Inovativnost | 5 | LLM agent with tool use over open geodata, grounded and cited; swappable open-source model |
| **Izvedivost** | **10** | A working, deployed, clickable prototype — not slides |
| Arhitektura | 5 | Clear diagram, OGC + GeoJSON + OpenAPI standards, documented integration with NIPP / INSPIRE, legal prerequisites listed |
| **Dojam (UI/UX)** | **10** | One input → one clear result; works on a phone; colour never the only signal |
| **Prezentacija** | **10** | 3-minute video built around the compare-two-flats demo |

**30 of 60 points are Izvedivost + Dojam + Prezentacija.** A working, beautiful, narrow product beats a broad, broken one. The award is withheld if no solution reaches 50 points.

### 1.3 Non-negotiables
- **It works end-to-end in the deployed URL.** Every screen shown in the video exists and functions.
- **Grounded, never invented.** Every number on screen and in AI answers comes from a dataset and carries a `source_id`. The assistant never guesses values, never gives legal, insurance or medical advice, and says "nemam taj podatak" when data is missing.
- **Honest about data age.** If a layer uses historical data (e.g. air quality from 2023), the UI shows the date. No "live" label on anything that is not live.
- **Graceful degradation.** If one layer fails, the other four still render; the failed one shows a clear message. A slow WMS never blocks the card.
- **Croatian first.** All UI copy in Croatian; English fallback is optional.
- **Accessible.** WCAG 2.2 AA contrast, every traffic light also has a text label and icon, full keyboard nav, tap targets ≥ 48 px.
- **Open source.** Public GitHub repo, MIT licence, every library and AI tool listed in the docs (Rules §VIII).
- **Perceived latency ≈ 0.** Layers stream in as they resolve, skeletons instead of spinners, AI answers stream token by token.

### 1.4 Tech stack & rationale
| Layer | Choice | Why |
|---|---|---|
| Frontend | **React 18 + Vite + TypeScript (strict)** | Fast dev server, static deploy, no SSR needed |
| Styling | **Tailwind CSS** | Fast, consistent, tokens in one place |
| Maps | **MapLibre GL JS + OpenFreeMap tiles** | Open source, free, no API key |
| Charts | **Recharts** | Air-quality history in a few lines |
| Client state | **Zustand** (selected addresses, compare mode), **TanStack Query** (API data, caching) | Small, predictable |
| Backend | **Python 3.11 + FastAPI + pydantic** | Geo libraries live in Python; auto OpenAPI docs at `/docs` for the architecture score |
| Geo | **Shapely 2, GeoPandas, pyproj, httpx** | Point-in-polygon, nearest-neighbour, EPSG:4326 ↔ EPSG:3765 (HTRS96/TM) |
| Geocoding | **Local OSM address index** (`data/addresses.parquet`, built by `scripts/fetch_addresses.py`), searched in the API | No external service at runtime; Nominatim's policy forbids autocomplete and public Photon throttles |
| Storage | **GeoJSON / GeoParquet in repo + SQLite cache** for WMS responses | No database server to run; data snapshot is reproducible |
| AI | **LLM with tool calling behind a `LLMProvider` interface**: Anthropic API by default, **Ollama** (OpenAI-compatible) as open-source alternative | Rules favour open-source software; switching is config-only (`LLM_PROVIDER`) |
| Hosting | **Vercel / Netlify** (frontend) + **Render / Railway** (backend) | Free tier, zero ops |
| Local run | **docker-compose** | Judges can run it with one command |

We deliberately do **not** use: PostGIS server, microservices, Kubernetes, a vector DB, user accounts, or our own ML model. They add risk and no points in 5 days. `docs/arhitektura.md` explains how the design scales beyond the prototype.

---

## 2. Technical Standards & Conventions

### 2.1 Repository layout
```
/
├── CLAUDE.md
├── PLAN.md
├── README.md                     # what it is, demo URL, screenshots, docker-compose up
├── LICENSE                       # MIT
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── arhitektura.md            # diagram, components, API contract, data flow
│   ├── data-sources.md           # every dataset: name, publisher, URL, licence, fetch date, transform
│   ├── integracija.md            # NIPP/INSPIRE, OGC standards, technical/organisational/legal prerequisites
│   ├── ekoskor.md                # formula, thresholds, limitations
│   ├── daljnji-razvoj.md         # all of Croatia, bathing water, fire risk, alerts, API for real-estate portals
│   ├── demo-script.md            # the 3-minute video script
│   └── screenshots/
├── scripts/                      # data pipeline (Python)
│   ├── fetch_waste.py            # → data/waste.geojson
│   ├── fetch_transit.py          # → data/transit.geojson
│   ├── fetch_air.py              # → data/air_stations.geojson, data/air_history.parquet
│   └── build_heatmap.py          # → data/heatmap.geojson
├── data/                         # clean snapshots are COMMITTED; raw/ is gitignored
├── notebooks/
│   └── 00_validacija.ipynb       # Phase 0: proof that each source answers for a point
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app, routers, CORS
│   │   ├── routers/              # geocode, profile, compare, chat, heatmap, sources
│   │   ├── services/
│   │   │   ├── wms.py            # get_feature_info(service, layer, lat, lon) + reprojection
│   │   │   ├── flood.py
│   │   │   ├── noise.py
│   │   │   ├── air.py
│   │   │   ├── mobility.py
│   │   │   └── ekoskor.py
│   │   ├── llm/
│   │   │   ├── provider.py       # LLMProvider, AnthropicProvider, OllamaProvider
│   │   │   ├── prompt.py         # Croatian system prompt
│   │   │   └── tools.py          # get_profile, compare, explain_layer, nearest_facility
│   │   ├── models.py             # pydantic schemas (Profile, Layer, Source…)
│   │   ├── sources.py            # registry of source_id → name, publisher, URL, licence
│   │   └── cache.py              # SQLite cache
│   └── tests/
│       ├── test_ekoskor.py
│       ├── test_services.py      # 3 reference points (see §2.6)
│       └── chat_cases.yaml       # 10 scripted assistant questions
└── frontend/
    └── src/
        ├── pages/                # Home, Address, Compare, City, Sources
        ├── components/
        │   ├── search/           # AddressSearch, ExampleAddresses
        │   ├── card/             # EkoSkorRing, LayerRow, LayerDetail, SourceBadge
        │   ├── map/              # AddressMap, LayerToggle, Legend
        │   ├── chat/             # AssistantPanel, MessageBubble, SuggestedQuestions
        │   ├── compare/          # CompareView, DiffRow, AiSummary
        │   ├── city/             # HeatmapView
        │   └── common/           # Skeleton, ErrorState, EmptyState, HowWeScoreModal
        ├── api/                  # typed client for the backend
        ├── stores/               # Zustand
        └── i18n/hr.ts            # all UI strings
```

### 2.2 Code style
- TypeScript `strict: true`. No `any` without a `// reason:` comment.
- ESLint + Prettier; `tsc --noEmit` in CI.
- Components: function components, named exports, one component per file, `PascalCase.tsx`. Hooks `useThing.ts`. Utilities `camelCase.ts`.
- All API responses are typed; the frontend types mirror the pydantic models in `backend/app/models.py`.
- UI strings live in `src/i18n/hr.ts`, never inline.
- Python: `ruff` (lint + format), type hints everywhere, pydantic for every request/response and every parsed dataset row.
- Pipeline scripts are idempotent and re-runnable; each writes one file in `data/` and logs row counts.
- Coordinates: **EPSG:4326 everywhere internally**. Reproject to EPSG:3765 only at the boundary of a service that requires it, inside `wms.py`.
- Distances in metres, noise in dB, always with units in variable names (`distance_m`, `lden_db`).

### 2.3 Design system
- **Tokens** in `index.css` as CSS variables; light + dark themes; `prefers-color-scheme` respected with manual toggle.
- **Palette:** off-white background `#F4F6F1`, ink `#14211A` text, **primary forest green `#1F7A4D`** for actions, accent teal `#0E8C8C` for links and map highlights.
- **Traffic light** colours are reserved for layer status only: green `#2E9D57`, amber `#E0A100` (dark ink text on it), red `#D2423A`. Each status always has a text label (*Dobro / Umjereno / Loše*) and an icon, so it works without colour.
- **Style: clean and calm.** One main action per screen. The EkoSkor ring is the hero element; the five layer rows sit directly under it. Plain short Croatian sentences, sentence-case headings, solid colours behind text, no decorative gradients behind content.
- **Type:** Inter; Croatian diacritics checked (č ć đ š ž). Base text 16–18 px.
- **Motion:** 150–250 ms, ease-out; the EkoSkor ring animates once on load; respect `prefers-reduced-motion`.
- **States:** every async component has designed loading (skeleton), empty, error and success states. No raw spinners, no blank screens.
- **Responsive:** mobile-first (375 px); on desktop (≥ 1024 px) map left, card right. Compare view stacks on mobile.

### 2.4 Data sources & model
Every source is registered once in `backend/app/sources.py` and listed in `docs/data-sources.md`.

| `source_id` | Dataset | Publisher | Access | Used for |
|---|---|---|---|---|
| `hv-poplave` | Karte opasnosti od poplava | Hrvatske vode | WMS `servisi.voda.hr/poplave_opasnosti/wms`, `GetFeatureInfo` | Flood zone at point |
| `zg-buka` | Strateška karta buke Grada Zagreba | Grad Zagreb | WMS (URL via NIPP CSW record) — `TODO(verify)` | L<sub>den</sub>, L<sub>night</sub> at point |
| `rh-buka` | Strateške karte buke (INSPIRE) | Ministarstvo zdravstva / MINGOR | WFS — `TODO(verify)` | Fallback for noise |
| `zg-zrak-postaje` | Geoportal Kvaliteta zraka | Grad Zagreb | CSV / CKAN Data API | Station locations |
| `zg-zrak-mjerenja` | Podaci o kvaliteti zraka u Gradu Zagrebu (per station, monthly) | Grad Zagreb | XLSX/CSV, CC BY 4.0 | History chart, latest value |
| `rh-zrak-indeks` | Indeks kvalitete zraka u RH (INSPIRE) | MINGOR | `TODO(verify)` | Live index if reachable |
| `zg-reciklaza` | Reciklažna dvorišta Grada Zagreba | Grad Zagreb | data.gov.hr / data.zagreb.hr | Nearest recycling yard |
| `zg-zet` | Autobusna stajališta ZET | Grad Zagreb / ZET | data.zagreb.hr | Stops within radius |

Several of these datasets have **no licence stated** in their metadata. Note that in `data-sources.md` and keep it visible; do not claim a licence that is not stated.

**Core response model (`Profile`):**

| Field | Type | Notes |
|---|---|---|
| `location` | `{lat, lon, address}` | EPSG:4326 |
| `ekoskor` | `int 0–100 \| null` | null if fewer than 3 layers available |
| `layers.flood` | `{status, zone: high\|medium\|low\|none, source_id}` | |
| `layers.noise` | `{status, lden_db, lnight_db, source_id}` | range allowed if read from legend |
| `layers.air` | `{status, station, distance_m, index, measured_at, history[], source_id}` | `measured_at` always shown in UI |
| `layers.mobility` | `{status, stops_300m, stops_500m, nearest_stop, source_id}` | |
| `layers.*.status` | `green \| yellow \| red \| unavailable` | |
| `generated_at` | ISO 8601 | |

**EkoSkor v1.** **`docs/ekoskor.md` is the authoritative description**; the code is `services/ekoskor.py`. Summary: weighted mean of five 0–100 sub-scores, 20 % each (decision 2026-11-08), rounded half up; weights renormalised over available layers; no EkoSkor with fewer than 3 layers.

| Layer | Weight | 100 | 50 | 0 |
|---|---|---|---|---|
| Flood | 20 % | outside all zones | low-probability zone | medium- or high-probability zone |
| Noise L<sub>den</sub>, loudest source | 20 % | ≤ 53 dB (WHO road traffic); no mapped band = below 50 dB | 54–64 dB | ≥ 65 dB |
| Air, PM10 mean Jan–Aug 2023, nearest City station | 20 % | ≤ 15 µg/m³ (WHO 2021) | 27,5 µg/m³ (linear) | ≥ 40 µg/m³ (EU limit) |
| Mobility = 4/5 transit + 1/5 bike (decision 2026-11-06) | 20 % | transit: ≥ 3 ZET platforms within 300 m; bike: City bike path or public bike station ≤ 200 m (the nearer) | transit: any platform within 500 m; bike linear | transit: none within 500 m; bike ≥ 1 km |
| Green space (Zelenilo), nearest park/forest ≥ 0.5 ha (decision 2026-11-06) | 20 % | ≤ 300 m or inside (WHO Europe 2017) | 650 m (linear) | ≥ 1 km |

Traffic light per layer from its sub-score as shown (rounded): ≥ 67 green, 34–66 yellow, ≤ 33 red.

Changing a threshold or weight requires updating `test_ekoskor.py` and `docs/ekoskor.md` in the same commit.

### 2.5 Agent design
- **System prompt** (`backend/app/llm/prompt.py`): Croatian, friendly, short answers (≤ 5 sentences unless asked for more). Use only tool results. Every factual claim ends with the source name in brackets. Never invent numbers, never give legal, insurance, medical or real-estate pricing advice; for those, point to the right institution.
- **Tools:** `get_profile(lat, lon)`, `compare(a, b)`, `explain_layer(layer)` (what the metric means, thresholds), `nearest_facility(type, lat, lon)`. Args validated with pydantic.
- **Grounding check:** after the answer, a simple post-check verifies that every number in the answer appears in the tool results; if not, the answer is regenerated once, then replaced with a safe fallback.
- **Provider abstraction:** `LLMProvider.chat(messages, tools, stream=True)`. `AnthropicProvider` and `OllamaProvider` both pass `chat_cases.yaml`, or the README states which one does not.
- **Limits:** 20 messages per session, 500 characters per message, 30 s timeout.
- **Compare summary:** one non-chat call that returns 3–4 sentences, cached per address pair.

### 2.6 Testing standards
- **pytest:**
  - `test_ekoskor.py` — every threshold edge, missing layers, renormalisation.
  - `test_services.py` — **three reference points** with expected results, recorded in Phase 0:
    - Savica, near the Sava (flood layer must not be `none`)
    - Trg bana Jelačića (dense stops, central noise)
    - Sljeme (high EkoSkor, few stops)
  - WMS/WFS calls mocked in unit tests from recorded responses in `backend/tests/fixtures/`.
- **Assistant evals:** `chat_cases.yaml`, 10 questions, run manually before recording; target ≥ 8/10 correct and 10/10 with no invented number.
- **Playwright:** one golden-path E2E (search → card → compare two addresses; "ask the assistant" only if the assistant is built, `TODO.md` §5). Must pass before any demo recording.
- **Lighthouse:** Performance ≥ 80, Accessibility ≥ 90 on the home page.
- No coverage targets — test what would embarrass us in the video.

### 2.7 Security & privacy (prototype level)
- Secrets only in `.env` / hosting env vars; `.env.example` committed; `gitleaks` in CI.
- E-mail addresses may be stored (e.g. for notifications), but users must be told before they submit one: what is stored, why, and how to remove it.
- No addresses or IPs in logs beyond aggregate counts.
- Respect public OSM services' usage policies (Overpass, Nominatim): identifying User-Agent, low request rates, cache everything. Never use Nominatim for autocomplete.
- Every team member turns off "use my data for training" in the AI tools they use (Claude, ChatGPT, Codex) before pasting project material.

---

## 3. Execution Instructions for AI Assistants

1. **Read `PLAN.md` first.** Work on the current phase only. If a request falls outside it, say so before doing it.
2. **Deadline mode.** Prefer the simplest thing that works and looks good. Do not introduce new dependencies, services or abstractions without stating why the existing stack can't do it.
3. **Small, verifiable steps.** Make one change, run the relevant checks (`pnpm typecheck && pnpm lint` in `frontend/`, `ruff check && pytest` in `backend/`), and report the result. Never claim something works without running it.
4. **Respect the structure** in §2.1. New components go in the matching folder; new strings go in `hr.ts`; new sources go in `sources.py` **and** `docs/data-sources.md`.
5. **Every UI component ships with its loading, empty and error states**, dark mode, keyboard support and reduced-motion handling. If you skip one, say which.
6. **Never fabricate data sources, URLs, columns, layer names or licences.** If unknown, write `TODO(verify)`. Judges score `data-sources.md`; one invented source can cost more than a missing layer.
7. **Never let the AI assistant answer without tool results.** Changes to `prompt.py`, `tools.py` or the grounding check require re-running `chat_cases.yaml` and stating the result.
8. **Coordinates and units are explicit.** State the EPSG code whenever you reproject; keep units in names.
9. **Commits:** Conventional Commits (`feat:`, `fix:`, `data:`, `docs:`, `style:`). One logical change per commit. Never add AI tools as author or co-author.
10. **When unsure about a dataset's meaning** (what a flood zone class or noise band represents), say so and flag it for a human to check rather than inventing an interpretation.
11. **Demo reliability over cleverness.** Anything on the demo path needs a fallback: pre-warmed cache for the demo addresses, committed data snapshot, last cached WMS response if the service is down, cached AI answers for the scripted questions.
12. **Scope cuts, in this order, if time runs out:** (1) city heatmap, (2) compare view, (3) air history chart. The address card and map are never cut. (The AI assistant is deferred, `TODO.md` §5.)
