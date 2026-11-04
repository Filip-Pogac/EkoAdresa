# EkoSkor — kako računamo (methodology)

> EkoSkor v1. Implemented in `backend/app/services/ekoskor.py`, tested in `backend/tests/test_ekoskor.py`.
> Any change to a threshold or weight updates the code, the tests and this file in the same commit.

EkoSkor is a number from 0 to 100. Each of five layers gets a sub-score from 0 to 100; EkoSkor is their weighted mean, **rounded half up** (42.5 → 43).

## Layers, weights and thresholds

| Layer | Weight | 100 | 50 | 0 | Source |
|---|---|---|---|---|---|
| Poplave (flood) | 25 % | outside all flood zones | low-probability zone | medium- or high-probability zone | `hv-poplave` |
| Buka (noise), L<sub>den</sub> | 25 % | ≤ 53 dB | 54–64 dB | ≥ 65 dB | `zg-buka` |
| Zrak (air), PM10 | 20 % | ≤ 15 µg/m³ | 27,5 µg/m³ | ≥ 40 µg/m³ | `zg-zrak-mjerenja` |
| Otpad (waste) | 15 % | fixed recycling yard ≤ 1 km **and** green island ≤ 300 m | one of the two | neither | `zg-reciklaza`, `osm-reciklaza` |
| Zelena mobilnost | 15 % | ≥ 3 stops within 300 m | at least one stop within 500 m | no stop within 500 m | `zg-zet` |

### How each layer is read

- **Flood.** The Hrvatske vode map has three probability scenarios. The point gets the highest-probability scenario whose flood extent covers it. Depth class is shown as extra information but does not change the score.
- **Noise.** The City noise map gives a separate L<sub>den</sub> band per source (road, tram, rail, industry) in 5 dB steps. We take the **loudest source** (decision 2026-11-05) and use the band's lower bound: band 50–54 → 100, 55–59 and 60–64 → 50, 65 and louder → 0. **No mapped band** at a point inside the City is read as quieter than 50 dB → 100. The road-noise layer's extent covers the whole City, which supports this reading; `TODO(verify)` against the noise map report. The 53 dB threshold is the WHO (2018) guideline for road-traffic noise, L<sub>den</sub>.
- **Air.** Mean PM10 at the **nearest City monitoring station**, January–August 2023 (the latest published data). The score is 100 at or below 15 µg/m³ (WHO 2021 annual air quality guideline), 0 at or above 40 µg/m³ (EU annual limit value, Directive 2008/50/EC), linear in between. The value is always shown with its period. Nearest-station is a coarse approximation: there are only 6 City stations.
- **Waste.** Straight-line distance to the nearest **fixed** recycling yard (the 10 mobile yards operate only on certain days and do not count, decision 2026-11-05) and to the nearest green island (OpenStreetMap recycling containers for paper, plastic or glass).
- **Mobility.** Number of ZET bus and tram **platforms** (one published point per stop and direction, decision 2026-11-05) within 300 m and 500 m, straight-line. The rule table leaves "no platform within 300 m but one within 500 m" open; we score it 50, and 0 only when nothing is within 500 m.

## Missing data

If a layer is unavailable (service down, no data), it is left out and the remaining weights are renormalised to 100 %. With fewer than 3 layers available there is no EkoSkor.

## City heatmap (*Za grad*)

The heatmap uses the same formula on a 250 × 250 m grid (EPSG:3765, HTRS96/TM) clipped to the City of Zagreb, evaluated at each cell centre. See `scripts/build_heatmap.py`.

- **Build of 2026-11-05:** 10 260 cells, 641 km². EkoSkor min 12, median 63, max 89 (10th–90th percentile 38–74). Noise available in all cells.
- **A cell is one sample point.** Each cell shows the value at its centre, up to ~175 m from any address in it. Example: the cell containing Trg bana Jelačića has its centre 63 m south of the square, inside a building block with no mapped noise band, so the cell scores noise 100 while the square itself (tram, 70–74 dB) scores 0. The address card is always computed at the exact address.
- **Waste rarely scores.** No cell reaches 100 and only 1 136 cells reach 50: there are 10 fixed yards for the whole City, and OSM green-island coverage is sparse. This is what the thresholds give with the current data; flagged for review of the threshold or the green-island source.

## Limitations

- Distances are straight-line, not walking routes.
- Noise and flood maps are strategic maps at city scale; a single building can differ.
- Air uses 2023 data from the nearest of 6 stations; it does not describe the air at the exact address.
- Green islands come from OpenStreetMap and may be incomplete.
- EkoSkor is an orientation, not an expert assessment, and not legal, insurance or real-estate advice.
