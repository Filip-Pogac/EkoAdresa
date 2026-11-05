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
