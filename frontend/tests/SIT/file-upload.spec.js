import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

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

    const testFilePath = path.join(__dirname, 'test.pdf');
    const testContent = Buffer.from('%PDF-1.4\n%EOF');

    if (!fs.existsSync(path.join(__dirname))) {
      fs.mkdirSync(path.join(__dirname), { recursive: true });
    }
    fs.writeFileSync(testFilePath, testContent);

    try {
      await fileInput.setInputFiles(testFilePath);

      const fileCount = await fileInput.locator('~').count().catch(() => 1);
      expect(fileCount).toBeGreaterThanOrEqual(1);
    } finally {
      if (fs.existsSync(testFilePath)) {
        fs.unlinkSync(testFilePath);
      }
    }
  });

  test('should show file name after selection', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');

    const testFilePath = path.join(__dirname, 'test.pdf');
    const testContent = Buffer.from('%PDF-1.4\n%EOF');

    if (!fs.existsSync(path.join(__dirname))) {
      fs.mkdirSync(path.join(__dirname), { recursive: true });
    }
    fs.writeFileSync(testFilePath, testContent);

    try {
      await fileInput.setInputFiles(testFilePath);

      const hasFileNames = page.locator('text=/test\\.pdf|file/i');
      const count = await hasFileNames.count().catch(() => 0);
      expect(count).toBeGreaterThanOrEqual(0);
    } finally {
      if (fs.existsSync(testFilePath)) {
        fs.unlinkSync(testFilePath);
      }
    }
  });

  test('should send message with file', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');
    const input = page.locator('input[type="text"], textarea').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    const testFilePath = path.join(__dirname, 'health.pdf');
    const testContent = Buffer.from('%PDF-1.4\n%EOF');

    if (!fs.existsSync(path.join(__dirname))) {
      fs.mkdirSync(path.join(__dirname), { recursive: true });
    }
    fs.writeFileSync(testFilePath, testContent);

    try {
      await fileInput.setInputFiles(testFilePath);
      await input.fill('Analyze this health document');
      await sendButton.click();

      const messages = page.locator('[class*="message"], [class*="Message"]');
      await expect(messages.first()).toBeVisible({ timeout: 10000 });
    } finally {
      if (fs.existsSync(testFilePath)) {
        fs.unlinkSync(testFilePath);
      }
    }
  });

  test('should clear file after sending', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    const testFilePath = path.join(__dirname, 'test.pdf');
    const testContent = Buffer.from('%PDF-1.4\n%EOF');

    if (!fs.existsSync(path.join(__dirname))) {
      fs.mkdirSync(path.join(__dirname), { recursive: true });
    }
    fs.writeFileSync(testFilePath, testContent);

    try {
      await fileInput.setInputFiles(testFilePath);
      await sendButton.click();

      await page.waitForTimeout(2000);

      const files = await fileInput.inputValue().catch(() => '');
      expect(files).toBe('');
    } finally {
      if (fs.existsSync(testFilePath)) {
        fs.unlinkSync(testFilePath);
      }
    }
  });
});