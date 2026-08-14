const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './playwright-tests',
  use: {
    baseURL: 'http://localhost:5173',
    headless: false,
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
    video: 'retain-on-failure',
  },
});
