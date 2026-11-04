"""Re-record the WMS fixtures for test_services.py from the live services.

Calls the real hv-poplave and zg-buka WMS through app.services.wms and saves the exact
response bodies wms.py received, so fixtures always match the real request parameters.

Run from backend/:  uv run python -m tests.record_fixtures
"""

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import httpx2 as httpx

from app.services import flood, noise, wms
from tests.reference_points import FIXTURES_DIR_NAME, POINTS

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
            for zone, scenario in flood.SCENARIOS.items():
                colour = await wms.get_map_pixel(
                    client, flood.HV_POPLAVE_URL, flood.layer_name(zone), lat, lon
                )
                (OUT_DIR / f"flood_{name}_{scenario}.png").write_bytes(last_ok[-1])
                print(f"{name} flood {scenario}: {colour}")
            features = await wms.get_feature_info(
                client,
                noise.ZG_BUKA_URL,
                noise.LAYERS,
                lat,
                lon,
                property_names=noise.PROPERTY_NAMES,
            )
            (OUT_DIR / f"noise_{name}.json").write_bytes(last_ok[-1])
            print(f"{name} noise: {[(f['id'], f['properties']['razina']) for f in features]}")

    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    (OUT_DIR / "RECORDED_AT.txt").write_text(f"{stamp}\n", encoding="utf-8", newline="\n")
    print(f"recorded {stamp} -> {OUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
