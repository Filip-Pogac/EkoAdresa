# Izvori podataka (data sources)

> Work in progress — filled during Phase 0 (data validation). Final table is completed in Phase 7.

## Summary

Licences are quoted exactly as stated by the publisher; "none stated" means the metadata names no licence.

| `source_id` | Dataset | Publisher | Access URL | Format | Licence (as stated) | Last update (as stated / observed) |
|---|---|---|---|---|---|---|
| `hv-poplave` | Karte opasnosti od poplava | Hrvatske vode | `https://servisi.voda.hr/poplave_opasnosti/wms` | OGC WMS 1.3.0 (GetMap; GetFeatureInfo refused) | none stated (Fees/AccessConstraints `NONE`) | `TODO(verify)` in NIPP record `9119600a-…` |
| `zg-buka` | Strateška karta buke Grada Zagreba | Grad Zagreb | `https://geoportal.zagreb.hr/Public/StrategijskoPlaniranje_Public/MapServer/WMSServer` | OGC WMS 1.3.0 (GetFeatureInfo JSON) | none stated (Fees/AccessConstraints `NONE`) | `TODO(verify)` (layer prefix `SKB_R4`, round 4) |
| `rh-buka` | Informacijski sustav strateških karata buke i akcijskih planova | `TODO(verify)` (azo.hr) | `http://servisi.azo.hr/zdravlje/wms`, `/wfs` | OGC WMS / WFS | `TODO(verify)` | not tested |
| `zg-zrak-postaje` | Geoportal Kvaliteta zraka | Grad Zagreb | data.zagreb.hr `geoportal-kvaliteta-zraka` (ArcGIS Hub export) | GeoJSON / CSV / KML / SHP | Otvorena dozvola (OD) | catalogue modified 2024-02-06 |
| `zg-zrak-mjerenja` | Podaci o kvaliteti zraka u Gradu Zagrebu – MP *station* 2023 (6 packages) | Grad Zagreb (measured by IMI) | data.zagreb.hr `podaci-o-kvaliteti-zraka-u-gradu-zagrebu-*-2023` | XLSX, one file per month, daily values | Otvorena dozvola (OD) on data.zagreb.hr; CC BY 4.0 for 2 stations on data.gov.hr (discrepancy) | data up to 2023-08-31 |
| `rh-zrak-indeks` | Indeks kvalitete zraka u Republici Hrvatskoj – INSPIRE | data.gov.hr lists Državna geodetska uprava; service on servisi.azo.hr `TODO(verify)` | `https://servisi.azo.hr/inspire/geos1/hh/wfs` | OGC WFS 2.0.0, INSPIRE HH GML | none stated | same-day values (2026-11-04 06:00Z seen at 21:10Z) |
| `zg-reciklaza` | Geoportal Reciklažna dvorišta grada Zagreba | Grad Zagreb | data.zagreb.hr `reciklazna-dvorista-grada-zagreba1` (ArcGIS Hub export) | GeoJSON / CSV / KML / SHP / GDB | Otvorena dozvola (OD) | resources 2022-12-01 |
| `zg-zeleni-otoci` | Lokacije zelenih otoka | Grad Zagreb | data.zagreb.hr `lokacije-zelenih-otoka` | CSV (cp1250) / XLSX, **no coordinates** | Otvorena dozvola (OD) | resources 2016-10/11 |
| `osm-reciklaza` | Recycling containers (green islands), Grad Zagreb | OpenStreetMap contributors | Overpass API `https://overpass-api.de/api/interpreter` (query below) | JSON | ODbL 1.0, "© OpenStreetMap contributors" | OSM data as of 2026-11-04T22:00:29Z |
| `zg-zet` (bus) | Geoportal Autobusna stajališta ZET | Grad Zagreb | data.zagreb.hr `autobusna-stajalista-zet` | GeoJSON | Otvorena dozvola (OD) | 2026-10-30 (refreshed every 90 days) |
| `zg-zet` (tram) | Geoportal Tramvajska stajališta ZET | Grad Zagreb | data.zagreb.hr `geoportal-tramvajska-stajalista-zet` (ArcGIS Hub export) | GeoJSON / CSV / KML / SHP / GDB | Otvorena dozvola (OD) | resources 2022-12-08 |

## Phase 0 validation log

### `hv-poplave` — Karte opasnosti od poplava (Hrvatske vode)

- **Checked:** 2026-11-04
- **GetCapabilities:** `https://servisi.voda.hr/poplave_opasnosti/wms?SERVICE=WMS&REQUEST=GetCapabilities` → HTTP 200, WMS 1.3.0 (GeoServer)
- **Advertised operation URL:** `https://servisi.voda.hr/poplave_opasnosti/ows?SERVICE=WMS&`
- **Fees / AccessConstraints:** `NONE` / `NONE` (as declared in capabilities; no licence named)
- **Metadata record (NIPP CSW):** `http://geoportal.nipp.hr/geonetwork/srv/eng/csw?service=CSW&request=GetRecordById&version=2.0.2&outputSchema=http://www.isotc211.org/2005/gmd&elementSetName=full&id=9119600a-fb7f-42e3-ad16-d9d10402eca5`
- **CRS per layer:** `EPSG:3765`, `CRS:84`
- **GetFeatureInfo formats:** `text/plain`, `application/json`, `text/html`, GML variants
- **WFS:** disabled on this server (`Service WFS is disabled`)

| Layer name | Title | `queryable` |
|---|---|---|
| `hr.fd.opasnost-od-poplave-mala-vjerojatnost` | Opasnosti od poplava, mala vjerojatnost pojavljivanja | 0 |
| `hr.fd.opasnost-od-poplave-srednja-vjerojatnost` | Opasnosti od poplava, srednja vjerojatnost pojavljivanja | 0 |
| `hr.fd.opasnost-od-poplave-velika-vjerojatnost` | Opasnosti od poplava, velika vjerojatnost pojavljivanja | 0 |
| `hr.fd.vjerojatnost-pojavljivanja` | Opasnost od poplava, tri scenarija plavljenja | 0 |

Legend for each layer: `https://servisi.voda.hr/poplave_opasnosti/ows?service=WMS&version=1.3.0&request=GetLegendGraphic&format=image/png&width=20&height=20&layer=<layer name>`

**Note:** all layers are advertised as `queryable="0"`.

#### Point query test (2026-11-04)

- `GetFeatureInfo` (with `STYLES=`) → `ServiceException code="LayerNotQueryable"` for every layer. **Point query via GFI is not possible.**
- Layers only render between `MinScaleDenominator 20000` and `MaxScaleDenominator 5000000`; `GetMap` at a larger scale (more zoomed in) returns an empty transparent image.
- **Workaround that works:** `GetMap`, `CRS=CRS:84`, 101×101 px box of ~707 m (≈ 7 m/px, ≈ 1:25 000), read the centre pixel. Transparent = outside that scenario's zone; opaque = inside.
- Legend (`GetLegendGraphic&format=application/json`): fill colour encodes depth class, attribute `m_kl_dub`: `1` `#BEE8FF` Dubina < 0,5 m · `2` `#73DFFF` 0,5–1,5 m · `3` `#73B2FF` 1,5–2,5 m · `4` `#7A8EF5` Dubina > 2,5 m.
- Reliability: one `GetMap` transfer was truncated and one `GetLegendGraphic` returned HTTP 502; both succeeded on retry → caching + retry required.

| Point (EPSG:4326) | mala (low) | srednja (medium) | velika (high) | Result |
|---|---|---|---|---|
| Savica 45.7905, 15.9950 | `#73B2FF` (1,5–2,5 m) | none | none | **low** |
| Trg bana Jelačića 45.8131, 15.9772 | none | none | none | **none** |
| Sljeme 45.8986, 15.9486 | none | none | none | **none** |

Responses differ between points as required. Depth-class interpretation is taken from the legend titles; flagged for a human to confirm.

### `zg-buka` — Strateška karta buke Grada Zagreba (Grad Zagreb)

- **Checked:** 2026-11-04
- **Found via NIPP CSW** (`https://geoportal.nipp.hr/geonetwork/srv/eng/csw`, `AnyText LIKE %buk%`):
  - dataset series record `6a586cec-3432-4dce-aa85-5d13aca4dfb2` "Strateška karta buke Grada Zagreba"
  - service record `40ef7b46-1b56-4a4e-8376-80aaf26d460e` "Strateška karta buke Grada Zagreba - WMS"
- **WMS:** `https://geoportal.zagreb.hr/Public/StrategijskoPlaniranje_Public/MapServer/WMSServer` → HTTP 200, WMS 1.3.0 (GeoServer)
- **Fees / AccessConstraints:** `NONE` / `NONE` (no licence named)
- **GetFeatureInfo formats:** `text/plain`, `application/json`, `text/html`, GML variants
- **Layers** (all `queryable="1"`): `SKB_R4_<source>_<indicator>` with
  source ∈ `Cestovni_promet` (road), `Tramvajski_promet` (tram), `Zeljeznicki_promet` (rail), `Industrijski_pogon` (industry)
  and indicator ∈ `Lday`, `Leve`, `Lnight`, `Lden` — 16 layers total.

#### Point query test (2026-11-04)

- `GetFeatureInfo`, `CRS=CRS:84`, `INFO_FORMAT=application/json`, `BUFFER=0`, all 8 `Lden`/`Lnight` layers in one request → works.
- Each feature has attribute `razina` = **lower bound of a 5 dB band**. Legend (`GetLegendGraphic&format=application/json`, same for Lden and Lnight): `<55` → 50–54 dB · `55–59` · `60–64` · `65–69` · `70–74` · `≥75`.
- Without `BUFFER=0` the server's pixel tolerance can return two adjacent bands at a band edge (seen at Savica: 65 and 70) → always send `BUFFER=0` and a small box.
- The map gives **one value per source** (road, tram, rail, industry), not a combined total.

| Point (EPSG:4326) | Result (`razina`, dB band lower bound) |
|---|---|
| Savica 45.7905, 15.9950 | road Lden 70 (70–74), road Lnight 60 (60–64) |
| Trg bana Jelačića 45.8131, 15.9772 | road Lden 50 (50–54), tram Lden 70 (70–74), tram Lnight 60 (60–64) |
| Sljeme 45.8986, 15.9486 | no features |

**Open questions (need a human decision):**
1. "No features" most likely means below the lowest mapped band (Lden < 50 dB), but it could also mean outside map coverage. `TODO(verify)` against the map report / metadata record.
2. Combining sources: take the loudest source (simple, explainable) or sum energetically (10·log10 Σ10^(L/10), more correct, but approximate on 5 dB bands). Decide in Phase 3 (`services/noise.py`).

### `rh-buka` — Informacijski sustav strateških karata buke i akcijskih planova (national, fallback)

Found in the same CSW search; not yet tested.

- WMS: `http://servisi.azo.hr/zdravlje/wms?request=GetCapabilities` (record `4a725707-a111-4322-abc0-ca434a132d25`)
- WFS: `http://servisi.azo.hr/zdravlje/wfs?request=GetCapabilities` (record `35922b69-1ac3-4507-8b4a-92c255f0d39e`)
- INSPIRE harmonised WMS: `http://servisi.azo.hr/inspire/geos2/hh/wms?service=WMS&version=1.3.0&request=GetCapabilities` (record `67286a25-e902-4889-9ac5-141a3a2f7be4`)
- INSPIRE harmonised WFS: `http://servisi.azo.hr/inspire/geos2/hh/wfs?service=WFS&version=2.0.0&request=GetCapabilities` (record `e53d2faa-939a-483c-9afe-f204332c67b3`)
- Publisher: `TODO(verify)` (host `azo.hr`, Agencija za zaštitu okoliša, now part of the ministry)

### `zg-zrak-postaje` — Geoportal Kvaliteta zraka (Grad Zagreb)

- **Checked:** 2026-11-04
- **Catalogue:** data.gov.hr / data.zagreb.hr CKAN, package `geoportal-kvaliteta-zraka`, organisation Grad Zagreb
- **Licence (as stated in catalogue):** "Otvorena dozvola (OD)" on both portals
- **Download (ArcGIS Hub export, EPSG:4326):** `https://opendata.arcgis.com/api/v3/datasets/ed9898e63ec94770a8fb37713c36f8ca_0/downloads/data?format=geojson&spatialRefId=4326&where=1%3D1` (CSV, KML, SHP also offered; same dataset)
- **Content:** 6 point features (monitoring stations). Fields: `OBJECTID`, `naziv`, `opis_lokac`, `lokacija`, `tip_podrucja`, `tip_postaje`, `visina_m`, `dimenzija`, `mjerne_tvari`, `odgovorna_inst`, `nadlezan`, `izvor`, `izradio`
- **Measuring institution (`odgovorna_inst`):** Institut za medicinska istraživanja i medicinu rada (IMI)

| `naziv` | `tip_postaje` | lon, lat |
|---|---|---|
| Đorđićeva ulica | Prometna | 15.97945, 45.81077 |
| Ksaverska cesta | Pozadinska | 15.97869, 45.83461 |
| Peščenica | Industrijska | 16.02824, 45.80425 |
| Prilaz baruna Filipovića | Prometna | 15.94454, 45.81135 |
| Siget | Prometna | 15.97922, 45.77340 |
| Susedgrad | Industrijska | 15.86887, 45.81158 |

Each station has a matching measurement dataset "Podaci o kvaliteti zraka u Gradu Zagrebu - MP <station> 2023" (monthly XLSX, see `zg-zrak-mjerenja`).

### `zg-zrak-mjerenja` — Podaci o kvaliteti zraka u Gradu Zagrebu, per station (Grad Zagreb)

- **Checked:** 2026-11-04 (station tested: MP Đorđićeva ulica 2023)
- **Catalogue:** data.zagreb.hr CKAN package `podaci-o-kvaliteti-zraka-u-gradu-zagrebu-dordiceva-2023` (one package per station; 6 stations, see `zg-zrak-postaje`)
- **Licence (as stated):** data.zagreb.hr: "Otvorena dozvola (OD)" (`open-license`) for all six. data.gov.hr mirror lists **CC BY 4.0** for Đorđićeva and Ksaver, "Otvorena dozvola (OD)" for the others. Discrepancy, `TODO(verify)`; cite both as stated.
- **Resources:** one XLSX per month, `.../download/djordjiceva2023<M>.xlsx`, **January–August 2023 only** (8 files). Latest available value: 2023-08-31.
- **Structure:** sheet `Numeričke vrijednosti` (sheet `Grafički prikaz` = chart only, ignore). Row 1 header, then **one row per day** (daily values), then one trailer row.
- **Columns (Đorđićeva):** `Datum` (datetime, daily) · `NO2 [µg/m3]` · `Ozon  [µg/m3]` (two spaces) · `PM10 [µg/m3]` · `Pb u PM10 [µg/m3]` · `Mn u PM10 [µg/m3]` · `Cd u PM10 [ng/m3]` · `Ni u PM10 [ng/m3]` · `As u PM10 [ng/m3]`. Same header in all 8 months; other stations measure different pollutants (see `mjerne_tvari`), so columns will differ per station.
- **Data quality notes:**
  - Missing values are empty cells (e.g. PM10 missing on 2–6 days in Jun–Aug).
  - Metals in PM10 contain many exact `0` values (Ni: 25 of 31 days in January), probably "below detection limit" or missing, `TODO(verify)`. Not used by EkoAdresa.
  - Trailer row: a single number in the PM10 column, most likely the number of days PM10 > 50 µg/m³ in the month (Feb: 9 = 9 computed; Apr–Aug: 0 = 0). Jan (1 vs 2) and Mar (0 vs 1) differ by one, probably due to rounding (Mar max = 50.1). Ignored when parsing.
- **Planned use:** NO2, O3, PM10 (and PM2.5 where measured) daily values → `data/air_history.parquet`; "latest" = last day with data, always shown with its date (2023).

### `rh-zrak-indeks` — Indeks kvalitete zraka u Republici Hrvatskoj (INSPIRE)

- **Checked:** 2026-11-04 ~21:10 UTC
- **Catalogue:** data.gov.hr package `indeks-kvalitete-zraka-u-republici-hrvatskoj-inspire` (org. Državna geodetska uprava; licence: none stated). Human-facing portal: `https://iszz.azo.hr/iskzl/`
- **WFS 2.0.0:** `https://servisi.azo.hr/inspire/geos1/hh/wfs` (the `http://` URL in the catalogue 302-redirects to https). WMS: `https://servisi.azo.hr/inspire/geos1/hh/wms`
- **Feature type:** `hh1:EnvHealthDeterminantMeasure` (INSPIRE Human Health schema 4.0), 25 features (stations) for all of Croatia
- **Per feature:** `gml:Point` in **EPSG:3765**, `hh1:type` = `air`, `hh1:measureTime/gml:TimePeriod/gml:endPosition` (timestamp), `hh1:measure uom="AQI"` (value, e.g. `1.0`…`5.0`)
- **Freshness observed:** all 25 features had `endPosition` 2026-11-04 06:00Z or 07:00Z when queried at ~21:10Z → data is from **the same day**, but not hourly up-to-date at query time. Update frequency `TODO(verify)` (poll again on 2026-11-05).
- **Zagreb features:**

  | gml:id | lat, lon (EPSG:4326) | endPosition | AQI |
  |---|---|---|---|
  | `EnvHealthDeterminantMeasure.155` | 45.80034, 15.97407 | 2026-11-04T06:00Z | 1.0 |
  | `EnvHealthDeterminantMeasure.157` | 45.76495, 16.00647 | 2026-11-04T06:00Z | 5.0 |

  These are national-network stations (not the six City/IMI stations in `zg-zrak-postaje`); nearest City station to .155 is Đorđićeva ulica at ~900 m.
- **Open questions:** (1) the AQI scale (range, class names, which pollutants) is not stated in the response, `TODO(verify)` on iszz.azo.hr; (2) no station name in the feature, so the name must be matched from another source or shown as "državna mjerna postaja"; (3) licence not stated.
- **Undocumented JSON endpoints** exist behind the iszz.azo.hr web app (`/iskzl/rs/...`, `/iskzl/geojson/<n>.geojson`) but are not a documented public API, so **not used**.

**Decision for the air layer:** use `rh-zrak-indeks` (WFS) for the "current index" with its timestamp shown, and `zg-zrak-mjerenja` (2023, labelled with the date) for the history chart and the City station details. If the WFS is unreachable, fall back to the latest 2023 value, clearly dated.

### `zg-reciklaza` — Reciklažna dvorišta grada Zagreba (Grad Zagreb)

- **Checked:** 2026-11-04
- **Catalogue:** data.zagreb.hr package `reciklazna-dvorista-grada-zagreba1` "Geoportal Reciklažna dvorišta grada Zagreba", org. Grad Zagreb, created 2020-01-30, resources last modified 2022-12-01
- **Licence (as stated):** "Otvorena dozvola (OD)"
- **Download (ArcGIS Hub export, EPSG:4326):** `https://opendata.arcgis.com/api/v3/datasets/249fa384ccf9481abf4fd2de73a822f5_0/downloads/data?format=geojson&spatialRefId=4326&where=1%3D1` (CSV, KML, SHP, GDB also offered)
- **Content:** 20 point features: 10 `RECIKLAŽNO DVORIŠTE` (fixed) + 10 `MOBILNO RECIKLAŽNO DVORIŠTE` (mobile, `NAZIV` prefix `MRD`). `VRSTA` contains embedded newlines → normalise whitespace.
- **Fields:** `OBJECTID_1`, `OBJECTID`, `RBR`, `VRSTA`, `NAZIV`, `ADRESA_LOK`, `NAZIV_PUNI`, `ADRESA`, `TELEFON`, `E_MAIL`, `FAX`, `WEB`, `RADNO_VRIJ` (opening hours), accepted waste flags `PAPIR`, `PLASTIKA`, `STAKLO`, `METALNA_AM`, `STARE_BATE`, `BIOOTPAD`, `OTPAD_GUME`, `OTPAD_MU`, `GRADJ_OTPA`, `ELEK_OTPAD`, `OSTALO` (values `DA`/`NE`), `NAPOMENA`
- **Operator (from `NAZIV_PUNI`):** Zagrebački holding d.o.o., Podružnica Čistoća
- Data is from 2022; opening hours / mobile yard locations may have changed → show "podaci iz 2022." in UI.

### `zg-zeleni-otoci` — Lokacije zelenih otoka (Grad Zagreb)

- **Checked:** 2026-11-04
- **Catalogue:** data.zagreb.hr package `lokacije-zelenih-otoka`, org. Grad Zagreb, created 2016-10-17; licence "Otvorena dozvola (OD)"
- **Download:** `https://data.zagreb.hr/dataset/0b532fd6-fa24-4f90-8c5e-698b5cbe94b7/resource/5d15eae4-6aa7-426c-b02c-a8fdb3d61a74/download/zeleniotoci.csv` (also XLSX)
- **Format:** CSV, `;`-separated, **cp1250** encoding, CRLF. Columns: `ULICA`, `LOKACIJA (OPIS)`, `GRADSKA ČETVRT`. ~297 rows.
- **Problem: no coordinates.** Locations are free-text street descriptions ("Križanje Potočnica-Narcisa", "Brestovečka 55"). Data is from **2016**.
- **Options (decision needed, Phase 2 `fetch_waste.py`):**
  1. Geocode the ~297 descriptions with Nominatim (≈ 5 min at 1 req/s), keep only street-number-level hits, and mark the precision. Lower precision and 2016 data.
  2. Use OpenStreetMap recycling containers (`amenity=recycling` + `recycling_type=container`) via Overpass: exact points, ODbL, but not a public-sector dataset.
  3. Combine: OSM for the distance, the City list as the official reference in docs.
- **Decision (2026-11-04): option 3.** Green-island distance comes from OpenStreetMap (`amenity=recycling` + `recycling_type=container`, Zagreb, via Overpass; licence ODbL 1.0, attribution "© OpenStreetMap contributors"), registered as a separate source `osm-reciklaza`. The City list `zg-zeleni-otoci` stays the official reference in the documentation. The UI states that green-island locations come from OSM. Exact Overpass query and fetch date are recorded below.

#### `osm-reciklaza` — fetch record (`scripts/fetch_waste.py`)

- **Fetched:** 2026-11-04, OSM data as of `2026-11-04T22:00:29Z` (`osm3s.timestamp_osm_base`)
- **Endpoint:** `https://overpass-api.de/api/interpreter` (fallback `https://maps.mail.ru/osm/tools/overpass/api/interpreter`). The main endpoint returned HTTP 502 "at capacity" twice before succeeding → the script retries with backoff.
- **Query:**
  ```
  [out:json][timeout:90];
  area["ISO3166-2"="HR-21"]["admin_level"]->.zg;
  nwr["amenity"="recycling"]["recycling_type"="container"](area.zg);
  out center tags;
  ```
- **Transform:** 716 elements (712 nodes, 4 ways → centre point). Kept only containers with at least one `recycling:paper*`, `recycling:plastic*` or `recycling:glass*` = `yes` → **628 green islands**. Dropped 88 that take only garden waste, clothes, scrap metal etc. (not a *zeleni otok*). OSM coverage is volunteer-mapped and may be incomplete; not validated against the City list.

#### `zg-reciklaza` — transform (`scripts/fetch_waste.py`)

- **Fetched:** 2026-11-04 → 20 yards: **10 fixed, 10 mobile** (`kind` from `VRSTA`). Whitespace normalised in all text fields.
- Accepted-waste flags `DA`/`NE` → `accepts` list. `OTPAD_MU` kept under its original name, meaning `TODO(verify)`.
- Mobile yards (`MRD …`) operate only on certain days; whether they count as "yard within 1 km" for EkoSkor is `TODO(decide)` in Phase 3.

**Output:** `data/waste.geojson` (EPSG:4326), one FeatureCollection, `properties.type` = `recycling_yard` | `green_island`, every feature carries `source_id`. Raw downloads in `data/raw/` (not committed).

### `zg-zet` — ZET bus and tram stops (Grad Zagreb)

- **Checked:** 2026-11-04
- **Bus stops:** data.zagreb.hr package `autobusna-stajalista-zet` "Geoportal Autobusna stajališta ZET", org. Grad Zagreb, licence "Otvorena dozvola (OD)". Resource last modified **2026-10-30**; the description states it is refreshed every 90 days.
  - Download: `https://data.zagreb.hr/dataset/cc7e45ae-4bad-4a07-bca2-25e82f1e082c/resource/3b12a182-afa3-4b07-833f-17d8bcf80ea9/download/data.geojson`
  - 1 888 points; no `crs` member (GeoJSON default WGS84 / EPSG:4326; coordinates confirmed lon, lat)
  - Fields: `Naziv_stajališta`, `Opis` (direction), `Linije` (comma-separated lines), `OBJECTID`, `Nadstresnica`, `Displej`, `Klupa`, `Rampa`, `TaktilnaCrta`, `Pristup*`, `UzdignutaPloha`, `StajalisteURazini`, `DimenzijaStajalista`, `Teren`, `Teren_napomena`, `Parking`, `CityLight`, `KosZaOtpad`, `PMUzObjekt`, `Napomena`. Names may have trailing spaces → strip.
  - The package slug `geoportal-autobusna-stajalista-zet` (listed in `package_list`) returns a non-JSON response from `package_show`; the slug above is the current one.
- **Tram stops:** data.zagreb.hr package `geoportal-tramvajska-stajalista-zet`, licence "Otvorena dozvola (OD)", resources from **2022-12-08**
  - Download (ArcGIS Hub export, EPSG:4326): `https://opendata.arcgis.com/api/v3/datasets/8f84d42e684141eaa7ceb26d9c9b8f5a_0/downloads/data?format=geojson&spatialRefId=4326&where=1%3D1`
  - 260 points; fields `OBJECTID`, `Naziv_stajališta`, `Linije`, `Opis`, `Napomena`
- **One point per platform/direction** (names end in "- jug", "- istok"…). For "stops within 300 m" decide whether to count platforms or group by name without the direction suffix. `TODO(decide)` in Phase 3.
- **GTFS:** no GTFS package on data.zagreb.hr (`q=gtfs` → 0).

| Point | bus ≤300 m / ≤500 m / nearest | tram ≤300 m / ≤500 m / nearest |
|---|---|---|
| Savica | 2 / 7 / 57 m | 0 / 0 / 598 m |
| Trg bana Jelačića | 4 / 10 / 101 m | 2 / 6 / 27 m |
| Sljeme | 1 / 3 / 147 m | 0 / 0 / 4 907 m |

(Platform counts, straight-line distance, equirectangular approximation.)

## Go / no-go per layer — APPROVED 2026-11-04

| Layer | Proposed status | Basis |
|---|---|---|
| Poplave | **OK with workaround** | `hv-poplave` GetFeatureInfo refused → GetMap centre-pixel at ~1:25 000 against the legend; gives zone **and** depth class. Server flaky (1× truncated, 1× 502) → cache + retry. |
| Buka | **OK** | `zg-buka` GetFeatureInfo JSON works with `BUFFER=0`; 5 dB bands per source (road, tram, rail, industry). Open: combining sources, meaning of "no feature". |
| Zrak | **OK** (two sources) | Current index from `rh-zrak-indeks` WFS (2 stations in Zagreb, same-day values); history and station details from `zg-zrak-mjerenja` (Jan–Aug 2023, labelled with date). Open: AQI scale definition. |
| Otpad | **OK with workaround** | Yards: `zg-reciklaza` OK (20 points). Green islands: City dataset has no coordinates (2016) → distance from OSM (`osm-reciklaza`), City list kept as official reference. |
| Zelena mobilnost | **OK** | `zg-zet` bus (2026-10-30) + tram (2022) stops, point data. Open: count platforms vs. named stops. |
