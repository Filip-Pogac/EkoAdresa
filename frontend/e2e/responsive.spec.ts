import { expect, test } from '@playwright/test';

/** PLAN.md Phase 5: check at 375 px, 768 px and 1440 px. */
const VIEWPORTS = [
  { name: '375', width: 375, height: 812 },
  { name: '768', width: 768, height: 1024 },
  { name: '1440', width: 1440, height: 900 },
];

const PAGES = [
  { name: 'home', path: '/', ready: 'Upišite adresu u Zagrebu' },
  {
    name: 'address',
    path: '/adresa?lat=45.813406&lon=15.977322&a=Trg+bana+Josipa+Jela%C4%8Di%C4%87a+6',
    ready: 'Zelena mobilnost',
    heading: true, // the text alone also matches the hidden "Kako računamo?" dialog
  },
  {
    name: 'compare',
    path:
      '/usporedba?a_lat=45.813406&a_lon=15.977322&a=Trg+bana+Josipa+Jela%C4%8Di%C4%87a+6' +
      '&b_lat=45.790284&b_lon=15.994318&b=Ulica+Vladimira+Ru%C5%BEdjaka+20',
    ready: 'Razlike po slojevima',
  },
  { name: 'city', path: '/grad', ready: 'EkoSkor ćelije' },
  { name: 'sources', path: '/izvori', ready: 'Karte opasnosti od poplava' },
];

for (const vp of VIEWPORTS) {
  for (const pg of PAGES) {
    test(`${pg.name} at ${vp.name} px: no horizontal scroll, no console errors`, async ({
      page,
    }, testInfo) => {
      const errors: string[] = [];
      page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
      page.on('pageerror', (e) => errors.push(e.message));

      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto(pg.path);
      const ready =
        'heading' in pg
          ? page.getByRole('heading', { name: pg.ready, exact: true })
          : page.getByText(pg.ready).first();
      await expect(ready).toBeVisible();

      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      await page.screenshot({
        path: testInfo.outputPath(`${pg.name}-${vp.name}.png`),
        fullPage: true,
      });
      expect(overflow, 'page is wider than the viewport').toBeLessThanOrEqual(0);
      expect(errors).toEqual([]);
    });
  }
}
