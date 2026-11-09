// Screenshots for docs/screenshots/ from the deployed site (or SCREENSHOT_BASE_URL).
// Run from frontend/:  node scripts/screenshots.mjs
// Needs Playwright's Chromium (PLAYWRIGHT_BROWSERS_PATH on this machine: E:\dev\ms-playwright).
import { chromium } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const BASE = process.env.SCREENSHOT_BASE_URL ?? 'https://ekoadresa.vercel.app';
const OUT = fileURLToPath(new URL('../../docs/screenshots/', import.meta.url));
const JELACIC = '/adresa?lat=45.813406&lon=15.977322&a=Trg+bana+Josipa+Jela%C4%8Di%C4%87a+6';
const SAVICA = '/adresa?lat=45.790284&lon=15.994318&a=Ulica+Vladimira+Ru%C5%BEdjaka+20';
const COMPARE =
  '/usporedba?a_lat=45.813406&a_lon=15.977322&a=Trg+bana+Josipa+Jela%C4%8Di%C4%87a+6' +
  '&b_lat=45.790284&b_lon=15.994318&b=Ulica+Vladimira+Ru%C5%BEdjaka+20';

const DESKTOP = { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 };
const PHONE = {
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 2,
  isMobile: true,
  hasTouch: true,
};

const shots = [
  {
    file: '01-pocetna.png',
    ctx: DESKTOP,
    path: '/',
    act: async (page) => page.getByRole('button', { name: 'Prikaži kartu Zagreba' }).click(),
  },
  { file: '02-adresa.png', ctx: DESKTOP, path: JELACIC, wait: 'Zelena mobilnost' },
  {
    file: '03-sloj-poplave.png',
    ctx: DESKTOP,
    path: SAVICA,
    wait: 'Zelena mobilnost',
    act: async (page) => page.getByLabel('Poplave').check(),
  },
  {
    file: '04-sloj-buke.png',
    ctx: DESKTOP,
    path: JELACIC,
    wait: 'Zelena mobilnost',
    act: async (page) => {
      await page.getByLabel('Buka').check();
      await page.getByLabel('Stajališta ZET-a').check();
    },
  },
  { file: '05-usporedba.png', ctx: DESKTOP, path: COMPARE, wait: 'Razlike po slojevima' },
  { file: '06-za-grad.png', ctx: DESKTOP, path: '/grad', wait: 'EkoSkor za cijeli Zagreb' },
  {
    file: '07-kako-racunamo.png',
    ctx: DESKTOP,
    path: '/',
    act: async (page) => page.getByRole('button', { name: 'Kako računamo?' }).first().click(),
  },
  {
    file: '08-mobitel-adresa.png',
    ctx: PHONE,
    path: JELACIC,
    wait: 'Zelena mobilnost',
    fullPage: true,
  },
  { file: '09-mobitel-usporedba.png', ctx: PHONE, path: COMPARE, wait: 'Razlike po slojevima' },
];

await mkdir(OUT, { recursive: true });
const browser = await chromium.launch();
for (const shot of shots) {
  const context = await browser.newContext({ ...shot.ctx, colorScheme: 'light', locale: 'hr-HR' });
  const page = await context.newPage();
  await page.goto(BASE + shot.path, { waitUntil: 'networkidle' });
  if (shot.wait)
    await page.getByRole('heading', { name: shot.wait, exact: true }).first().waitFor();
  if (shot.act) {
    await shot.act(page);
    await page.evaluate(() => window.scrollTo(0, 0)); // clicking a layer box scrolls it into view
  }
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1500); // map tiles and the ring animation settle
  await page.screenshot({ path: OUT + shot.file, fullPage: shot.fullPage ?? false });
  console.log('saved', shot.file);
  await context.close();
}
await browser.close();
