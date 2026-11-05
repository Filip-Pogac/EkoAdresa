import { expect, test } from '@playwright/test';

const JELACIC = '/adresa?lat=45.813406&lon=15.977322&a=Trg+bana+Josipa+Jela%C4%8Di%C4%87a+6';

test('clicking the map opens the profile of that point', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(JELACIC);
  await expect(page.getByText('Kliknite bilo gdje na karti za EkoSkor te točke.')).toBeVisible();
  await expect(page.getByRole('img', { name: /^EkoSkor \d+ od 100$/ })).toBeVisible();

  // The marker appears once the map is ready (loading overlay gone); let the ease settle
  const map = page.locator('.maplibregl-canvas');
  await expect(page.locator('.maplibregl-marker')).toBeVisible();
  await page.waitForTimeout(500);
  const box = await map.boundingBox();
  if (!box) throw new Error('map has no size');
  await page.mouse.click(box.x + box.width * 0.25, box.y + box.height * 0.3);

  await expect(page).toHaveURL(/\/adresa\?lat=45\.81\d+&lon=15\.97\d+$/);
  await expect(page).not.toHaveURL(/lat=45\.813406/);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Odabrana točka na karti');
  await expect(page.getByRole('img', { name: /^EkoSkor \d+ od 100$/ })).toBeVisible();
  expect(errors).toEqual([]);
});

/** Pixel offset of (lat, lon) from the map centre at `zoom` (Web Mercator, 512 px tiles). */
function offsetPx(lat: number, lon: number, cLat: number, cLon: number, zoom: number) {
  const scale = (512 * 2 ** zoom) / (2 * Math.PI);
  const y = (la: number) => Math.log(Math.tan(Math.PI / 4 + (la * Math.PI) / 360));
  return {
    dx: ((lon - cLon) * Math.PI * scale) / 180,
    dy: -(y(lat) - y(cLat)) * scale,
  };
}

test('clicking a stop opens its popup and stays on the address', async ({ page, request }) => {
  const [lat, lon] = [45.813406, 15.977322];
  const api = process.env.E2E_API_URL ?? 'https://ekoadresa-api.vercel.app';
  const profile = await (await request.get(`${api}/api/profile?lat=${lat}&lon=${lon}`)).json();
  const stop = profile.layers.mobility.nearest_stop as { lat: number; lon: number };

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(JELACIC);
  await expect(page.locator('.maplibregl-marker')).toBeVisible();
  await page.getByLabel('Stajališta ZET-a').check();
  await page.waitForTimeout(1500); // stops layer loads; the map has eased to zoom 15

  const box = await page.locator('.maplibregl-canvas').boundingBox();
  if (!box) throw new Error('map has no size');
  const { dx, dy } = offsetPx(stop.lat, stop.lon, lat, lon, 15);
  await page.mouse.click(box.x + box.width / 2 + dx, box.y + box.height / 2 + dy);

  await expect(page.locator('.maplibregl-popup')).toContainText('Trg bana J. Jelačića');
  await expect(page).toHaveURL(/lat=45\.813406/); // did not navigate
});
