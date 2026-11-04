# EkoAdresa

Okolišni profil bilo koje adrese u Zagrebu: poplave, buka, zrak, otpad i zelena mobilnost na jednom mjestu, uz EkoSkor 0–100 i AI asistenta koji odgovara samo iz otvorenih podataka.

Rješenje za **Datathon Portala otvorenih podataka 2026**, izazov B (*Okoliš i održivi prostor*).

> Status: u izradi. Demo URL i snimke zaslona dodaju se prije predaje.

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
```

## Dokumentacija

- [Izvori podataka](docs/data-sources.md)
- [Plan projekta](PLAN.md)

## Licenca

[MIT](LICENSE)
