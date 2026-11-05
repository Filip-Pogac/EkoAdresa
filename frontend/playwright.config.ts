import { defineConfig, devices } from '@playwright/test';

/**
 * End-to-end tests (CLAUDE.md §2.6). They run against a running site:
 *   E2E_BASE_URL=http://localhost:5173 pnpm e2e   (dev server + backend)
 *   pnpm e2e                                      (the deployed site)
 * Browsers live outside the repo; on this machine: PLAYWRIGHT_BROWSERS_PATH=E:\dev\ms-playwright
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  expect: { timeout: 15_000 }, // cold serverless start + live map services
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'https://ekoadresa.vercel.app',
    locale: 'hr-HR',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
