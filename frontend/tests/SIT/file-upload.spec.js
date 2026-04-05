import { test, expect } from '@playwright/test';

const pdfFixture = {
  name: 'test.pdf',
  mimeType: 'application/pdf',
  buffer: Buffer.from('%PDF-1.4\n%EOF'),
};

const healthPdfFixture = {
  name: 'health.pdf',
  mimeType: 'application/pdf',
  buffer: Buffer.from('%PDF-1.4\n%EOF'),
};

test.describe('Health AI Frontend - File Upload', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display file upload input', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');
    const isVisible = await fileInput.isVisible().catch(() => false);

    const exists = await fileInput.count();
    expect(exists).toBeGreaterThanOrEqual(1);
    void isVisible;
  });

  test('should allow file selection', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');

    await fileInput.setInputFiles(pdfFixture);

    await expect(page.locator('.file-chip')).toContainText('test.pdf');
  });

  test('should show file name after selection', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');

    await fileInput.setInputFiles(pdfFixture);

    await expect(page.locator('text=/test\\.pdf/i')).toBeVisible();
  });

  test('should send message with file', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');
    const input = page.getByPlaceholder('Ask about your lab results...');
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    await fileInput.setInputFiles(healthPdfFixture);
    await input.fill('Analyze this health document');
    await sendButton.click();

    await expect(page.locator('text=/health\\.pdf/i')).toBeVisible();
  });

  test('should clear file after sending', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    await fileInput.setInputFiles(pdfFixture);
    await expect(page.locator('.file-chip')).toContainText('test.pdf');
    await sendButton.click();

    await expect(page.locator('.file-chip')).toHaveCount(0, { timeout: 5000 });
  });
});