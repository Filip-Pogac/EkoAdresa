# Korišteni alati i licencije

Popis softvera, servisa i alata umjetne inteligencije korištenih za izradu EkoAdrese, u skladu s poglavljem VIII. Pravila za Datathon Portala otvorenih podataka („Timovi smiju koristiti postojeće alate, biblioteke i komponente otvorenog koda, uključujući alate temeljene na umjetnoj inteligenciji, pod uvjetom da ne krše njihove licence i da ih navedu u dokumentaciji").

Skupovi podataka i njihove licencije navedeni su zasebno u [data-sources.md](data-sources.md).

**Licencija rješenja:** izvorni kod EkoAdrese objavljen je pod licencijom MIT ([LICENSE](../LICENSE)) u javnom repozitoriju <https://github.com/Filip-Pogac/EkoAdresa>.

Verzije su one zaključane u `backend/uv.lock` i `frontend/pnpm-lock.yaml`, a licencije su preuzete iz metapodataka instaliranih paketa (5. 11. 2026.).

## 1. Aplikacija: backend (Python)

| Paket | Verzija | Licencija | Namjena |
|---|---|---|---|
| FastAPI | 0.162.0 | MIT | Web API, automatska OpenAPI dokumentacija (`/docs`) |
| Starlette | 1.10.0 | BSD-3-Clause | Temelj FastAPI-ja (CORS, gzip) |
| pydantic | 2.14.2 | MIT | Sheme zahtjeva i odgovora |
| Uvicorn | 0.54.0 | BSD-3-Clause | ASGI poslužitelj (lokalno i Docker) |
| httpx2 | 2.16.0 | BSD-3-Clause | HTTP klijent za WMS/WFS servise |
| Shapely | 2.2.0 | BSD-3-Clause | Prostorne operacije (granica Grada Zagreba) |
| pyproj | 3.7.2 | MIT | Preračun koordinata EPSG:4326 ↔ EPSG:3765 (HTRS96/TM) |
| NumPy | 2.4.6 | BSD-3-Clause (i dijelovi 0BSD, MIT, Zlib) | Izračun udaljenosti |
| pandas | 3.1.1 | BSD-3-Clause | Tablični podaci (adrese, mjerenja zraka) |
| PyArrow | 26.0.1 | Apache-2.0 | Čitanje i pisanje datoteka Parquet |
| Pillow | 13.0.0 | MIT-CMU | Čitanje boje piksela s karte poplava, kartografske pločice |

## 2. Aplikacija: frontend (TypeScript)

| Paket | Verzija | Licencija | Namjena |
|---|---|---|---|
| React, React DOM | 18.3.1 | MIT | Korisničko sučelje |
| React Router | 7.18.4 | MIT | Stranice s adresama koje se mogu dijeliti |
| TanStack Query | 5.104.5 | MIT | Dohvat i privremeno spremanje podataka s API-ja |
| MapLibre GL JS | 6.16.0 | BSD-3-Clause | Interaktivna karta |
| Recharts | 3.10.1 | MIT | Graf mjerenja kvalitete zraka |
| react-is | 18.3.1 | MIT | Ovisnost Rechartsa |
| Tailwind CSS (+ `@tailwindcss/vite`) | 4.3.4 | MIT | Stilovi |
| Inter (`@fontsource-variable/inter`) | 5.3.0 | OFL-1.1 | Font s hrvatskim dijakritičkim znakovima |

## 3. Razvoj, testiranje i obrada podataka

| Alat | Verzija | Licencija | Namjena |
|---|---|---|---|
| Python | 3.11 (lokalno), 3.12 (Vercel) | PSF-2.0 | Backend i skripte za podatke |
| uv | 0.13.7 | MIT / Apache-2.0 | Upravljanje Python ovisnostima |
| pytest | 9.2.0 | MIT | Testovi backenda |
| Ruff | 0.17.3 | MIT | Provjera i formatiranje Python koda |
| openpyxl | 3.1.5 | MIT | Čitanje XLSX mjerenja kvalitete zraka (`scripts/fetch_air.py`) |
| Jupyter, httpx | — | BSD-3-Clause | Provjera izvora u fazi 0 (`notebooks/00_validacija.ipynb`) |
| Node.js | 24 | MIT | Izgradnja frontenda |
| pnpm | 12.16.1 | MIT | Upravljanje JavaScript ovisnostima |
| Vite (+ `@vitejs/plugin-react`) | 8.3.5 | MIT | Izgradnja i razvojni poslužitelj |
| TypeScript | 5.9.3 | Apache-2.0 | Tipizirani kod |
| ESLint, typescript-eslint i dodaci | 10.14.0 / 8.72.1 | MIT | Provjera koda |
| Prettier | 3.9.10 | MIT | Formatiranje koda |
| Playwright | 1.64.1 | Apache-2.0 | Testovi s kraja na kraj i provjera prikaza na 375 / 768 / 1440 px |
| Lighthouse | 13.5.0 | Apache-2.0 | Mjerenje performansi i pristupačnosti |
| Docker Engine, Docker Compose | 29.7.2 | Apache-2.0 | Pokretanje cijelog sustava jednom naredbom (`docker-compose.yml`) |
| Docker Desktop | 29.7.2 | Vlasnička licencija proizvođača (nije otvorenog koda) | Pokretanje Dockera na Windowsima tijekom razvoja; nije potreban za rad rješenja |
| Git | 2.47 | GPL-2.0 | Upravljanje verzijama |
| Vercel CLI | 59.20.0 | Apache-2.0 | Objava aplikacije |

## 4. Servisi

| Servis | Vrsta | Namjena |
|---|---|---|
| **Vercel** (besplatni plan Hobby) | Komercijalna platforma za objavu; nije softver otvorenog koda | Hosting demo verzije: <https://ekoadresa.vercel.app>, API <https://ekoadresa-api.vercel.app> |
| **OpenFreeMap** | Besplatne vektorske pločice podloge; podaci © OpenMapTiles i © OpenStreetMap contributors (ODbL) | Podloga karte |
| **GitHub** | Javni repozitorij koda | Objava izvornog koda |

Aplikacija se može pokrenuti i bez Vercela: `docker-compose up` pokreće cijeli sustav lokalno (vidi [README](../README.md)).

## 5. Alati umjetne inteligencije

| Alat | Proizvođač | Licencija | Kako je korišten |
|---|---|---|---|
| **Claude Code** | Anthropic | Komercijalni alat (nije otvorenog koda), korišten prema uvjetima korištenja proizvođača | Asistent pri programiranju: pisanje i pregled koda, testova i dokumentacije, provjera izvora podataka i servisa, pokretanje provjera. Članovi tima pregledali su i prihvatili sve izmjene. |

**Aplikacija sama ne koristi umjetnu inteligenciju u radu.** EkoSkor je izračun prema javno objavljenoj formuli ([ekoskor.md](ekoskor.md)), a svaki broj na zaslonu dolazi iz navedenog skupa podataka. AI asistent za pitanja o adresi bio je planiran, ali je odgođen; plan je opisan u [daljnji-razvoj.md](daljnji-razvoj.md).
