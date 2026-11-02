import { defineConfig } from "@playwright/test";
import { existsSync } from "node:fs";
const cached =
  "/Users/trai/Library/Caches/ms-playwright/chromium-1248/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing";
export default defineConfig({
  testDir: "./tests/ui",
  workers: 1,
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:8799",
    headless: true,
    launchOptions: existsSync(cached) ? { executablePath: cached } : {},
  },
  webServer: {
    command: "node scripts/test-server.mjs",
    url: "http://127.0.0.1:8799/health",
    reuseExistingServer: false,
    timeout: 30000,
  },
});
