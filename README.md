# EkoAdresa

Okolišni profil bilo koje adrese u Zagrebu: poplave, buka, zrak, otpad i zelena mobilnost na jednom mjestu, uz EkoSkor 0–100, kartu slojeva i usporedbu dviju adresa.

Rješenje za **Datathon Portala otvorenih podataka 2026**, izazov B (*Okoliš i održivi prostor*).

**Demo:** <https://ekoadresa.vercel.app> · API: <https://ekoadresa-api.vercel.app/docs>

> Status: u izradi. Snimke zaslona dodaju se prije predaje.

## Pokretanje

### Docker (preporučeno)

```bash
cp .env.example .env
docker-compose up --build
```

- Frontend: <http://localhost:5173>
- Backend API: <http://localhost:8000> (OpenAPI dokumentacija na `/docs`)

### Lokalni razvoj

Potrebno: Python 3.11+, [uv](https://docs.astral.sh/uv/), Node.js 20+, pnpm.

```bash
# Backend
cd backend
uv sync
uv run uvicorn app.main:app --reload

# Frontend (drugi terminal)
cd frontend
pnpm install
pnpm dev
```

Provjere:

```bash
cd backend && uv run ruff check && uv run pytest
cd frontend && pnpm lint && pnpm typecheck
# End-to-end (Playwright): protiv objavljene stranice ili lokalno s E2E_BASE_URL
cd frontend && npx playwright install chromium && pnpm e2e
E2E_BASE_URL=http://localhost:5173 pnpm e2e
```

### Objava (Vercel)

Dva Vercel projekta iz istog repozitorija:

- **Backend** (`ekoadresa-api`): korijen repozitorija. `index.py` učitava `backend/app`, a `vercel.json` postavlja regiju `fra1`. Ovisnosti su u `requirements.txt` (izvezeno iz `backend/uv.lock`: `cd backend && uv export --no-dev --no-hashes --no-emit-project -o ../requirements.txt`). Varijabla okruženja: `CORS_ORIGINS` = adresa frontenda. Predmemorija je u `/tmp`; `data/cache_seed.json` (`scripts/warm_cache.py`) unaprijed puni adrese za demo.
- **Frontend** (`ekoadresa`): mapa `frontend/`, Vite. Varijabla okruženja: `VITE_API_URL` = adresa backenda.

```bash
vercel deploy --prod            # u korijenu: backend
cd frontend && vercel deploy --prod
```

## Dokumentacija

- [Izvori podataka](docs/data-sources.md)
- [Plan projekta](PLAN.md)

## Licenca

[MIT](LICENSE)
