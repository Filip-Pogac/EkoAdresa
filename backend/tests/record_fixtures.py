"""Re-record the WMS fixtures for test_services.py from the live services.

Calls the real hv-poplave and zg-buka WMS through app.services.wms and saves the exact
response bodies wms.py received, so fixtures always match the real request parameters.

Run from backend/:  uv run python -m tests.record_fixtures
"""

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import httpx2 as httpx

from app.services import wms
from tests.reference_points import (
    FIXTURES_DIR_NAME,
    FLOOD_SCENARIOS,
    HV_POPLAVE_URL,
    NOISE_LAYERS,
    NOISE_PROPERTIES,
    POINTS,
    ZG_BUKA_URL,
    flood_layer,
)

OUT_DIR = Path(__file__).parent / "fixtures" / FIXTURES_DIR_NAME


async def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    last_ok: list[bytes] = []

    async def keep_body(response: httpx.Response) -> None:
        await response.aread()
        if response.status_code == 200:
            last_ok.append(response.content)

    async with httpx.AsyncClient(timeout=30, event_hooks={"response": [keep_body]}) as client:
        for name, (lat, lon) in POINTS.items():
            for scenario in FLOOD_SCENARIOS:
                colour = await wms.get_map_pixel(
                    client, HV_POPLAVE_URL, flood_layer(scenario), lat, lon
                )
                (OUT_DIR / f"flood_{name}_{scenario}.png").write_bytes(last_ok[-1])
                print(f"{name} flood {scenario}: {colour}")
            features = await wms.get_feature_info(
                client, ZG_BUKA_URL, NOISE_LAYERS, lat, lon, property_names=NOISE_PROPERTIES
            )
            (OUT_DIR / f"noise_{name}.json").write_bytes(last_ok[-1])
            print(f"{name} noise: {[(f['id'], f['properties']['razina']) for f in features]}")

    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    (OUT_DIR / "RECORDED_AT.txt").write_text(f"{stamp}\n", encoding="utf-8", newline="\n")
    print(f"recorded {stamp} -> {OUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
