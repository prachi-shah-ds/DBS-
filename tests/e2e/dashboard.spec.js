const { test, expect } = require('@playwright/test');

test('add reorder and save dashboard layout', async ({ page }) => {
  await page.goto('http://localhost:5000/_dev/dashboard');
  // open customize
  await page.click('#open-customize');
  await page.click('.btn-add[data-panel-id="stock_alerts"]');
  // ensure panel added
  await expect(page.locator('[data-panel-id="stock_alerts"]')).toHaveCount(1);
  // reorder by keyboard: focus then ArrowRight
  const item = page.locator('#dashboard-grid .grid-stack-item').first();
  await item.focus();
  await page.keyboard.press('ArrowRight');
  // save and check localStorage has key
  await page.click('#save-layout');
  const ls = await page.evaluate(() => localStorage.getItem('jodo_dashboard_layout_v1'));
  expect(ls).not.toBeNull();
});
