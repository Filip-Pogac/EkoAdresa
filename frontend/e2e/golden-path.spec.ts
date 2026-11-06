import { expect, test, type Page } from '@playwright/test';

const LAYERS = ['Poplave', 'Buka', 'Zrak', 'Otpad', 'Zelena mobilnost', 'Zelenilo'];

/** Console errors collected for the whole test; asserted empty at the end. */
function collectErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  page.on('pageerror', (err) => errors.push(err.message));
  return errors;
}

test('search → address card → compare two addresses', async ({ page }) => {
  const errors = collectErrors(page);
  await page.goto('/');

  // Search by keyboard
  const search = page.getByRole('combobox', { name: 'Upišite adresu u Zagrebu' });
  await search.fill('ilica 10');
  await expect(page.getByRole('option').first()).toContainText('Ilica 10');
  await search.press('Enter');

  // Card: EkoSkor ring + six layer rows, none unavailable
  await expect(page).toHaveURL(/\/adresa\?lat=/);
  await expect(page.getByRole('img', { name: /^EkoSkor \d+ od 100$/ })).toBeVisible();
  for (const layer of LAYERS) {
    await expect(page.getByRole('heading', { name: layer, exact: true })).toBeVisible();
  }
  await expect(page.getByText('Nedostupno')).toHaveCount(0);

  // Compare with a second address
  await page.getByRole('link', { name: 'Usporedi s drugom adresom' }).click();
  const second = page.getByRole('combobox', { name: 'Druga adresa' });
  await second.fill('ruzdjaka 20');
  await expect(page.getByRole('option').first()).toContainText('Ruždjaka 20');
  await second.press('Enter');

  await expect(page.getByRole('heading', { name: 'Razlike po slojevima' })).toBeVisible();
  await expect(page.getByRole('img', { name: /^EkoSkor \d+ od 100$/ })).toHaveCount(2);
  await expect(page.getByText(/ima EkoSkor viši za \d+ bod/)).toBeVisible();
  await expect(page.getByText('Bolje').first()).toBeVisible();

  expect(errors).toEqual([]);
});
