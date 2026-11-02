import { test, expect } from "@playwright/test";
test("LLM-free consultant workflow, immutable analysis and narrow layout", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await page
    .getByLabel("Access token")
    .fill("ui-test-token-not-a-production-secret");
  await page.getByRole("button", { name: "Open workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "From workload to requirements" }),
  ).toBeVisible();
  await page.screenshot({ path: "test-results/cases.png", fullPage: true });
  await page
    .getByRole("button", { name: "Open original incomplete story" })
    .first()
    .click();
  await expect(
    page.getByRole("heading", { name: "Meridian Industrial Services" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "4 Demand" }).click();
  await expect(page.getByLabel("users · state", { exact: true })).toBeVisible();
  await page.screenshot({ path: "test-results/builder.png", fullPage: true });
  await page.getByRole("button", { name: "Freeze and compile" }).click();
  await expect(
    page.getByRole("heading", { name: "Workload analysis" }),
  ).toBeVisible();
  await expect(page.getByText("12.5 request/s", { exact: true })).toBeVisible();
  await expect(
    page.getByText("GPU count is unresolved.", { exact: false }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Inspect", exact: true })
    .first()
    .click();
  await expect(page.locator("#inspector")).toBeVisible();
  await page.screenshot({ path: "test-results/analysis.png", fullPage: true });
  await page.setViewportSize({ width: 320, height: 700 });
  await page
    .getByRole("button", { name: "Workload builder", exact: true })
    .click();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({ path: "test-results/mobile.png", fullPage: true });
  expect(errors).toEqual([]);
});
