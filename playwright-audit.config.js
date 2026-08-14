const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './playwright-audit',
  timeout: 30000,
  expect: { timeout: 7000 },
  workers: 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-audit/reports/html', open: 'never' }],
    ['json', { outputFile: 'playwright-audit/reports/results.json' }]
  ],
  use: {
    baseURL: 'http://localhost:5173',
    headless: false,
    screenshot: 'on',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    actionTimeout: 10000
  }
});
