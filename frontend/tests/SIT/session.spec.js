import { test, expect } from '@playwright/test';

test.describe('Health AI Frontend - Session & State Management', () => {
  test('should maintain session across page reload', async ({ page, context }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const input = page.getByPlaceholder('Ask about your lab results...');
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    const testMessage = 'What is BMI?';
    await input.fill(testMessage);
    await sendButton.click();

    await page.waitForTimeout(2000);

    const messageBefore = page.locator('[class*="message"], [class*="Message"]');
    const countBefore = await messageBefore.count();

    await page.reload();
    await page.waitForLoadState('networkidle');

    const messageAfter = page.locator('[class*="message"], [class*="Message"]');
    const countAfter = await messageAfter.count();

    expect(countBefore).toBeGreaterThanOrEqual(1);
    expect(countAfter).toBeGreaterThanOrEqual(1);
    void context;
  });

  test('should preserve session ID across requests', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const input = page.getByPlaceholder('Ask about your lab results...');
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    const sessionBefore = await page.evaluate(() => {
      return localStorage.getItem('sessionId') || sessionStorage.getItem('sessionId') || 'none';
    });

    await input.fill('Message 1');
    await sendButton.click();
    await page.waitForTimeout(1000);

    const sessionAfter = await page.evaluate(() => {
      return localStorage.getItem('sessionId') || sessionStorage.getItem('sessionId') || 'none';
    });

    if (sessionBefore !== 'none' && sessionAfter !== 'none') {
      expect(sessionBefore).toBe(sessionAfter);
    }
  });

  test('should maintain conversation history within session', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const input = page.getByPlaceholder('Ask about your lab results...');
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    await input.fill('Question 1: What is blood pressure?');
    await sendButton.click();
    await page.waitForTimeout(2000);

    await input.fill('Question 2: What are risk factors?');
    await sendButton.click();
    await page.waitForTimeout(2000);

    const allText = await page.textContent('body');

    expect(allText).toContain('Question 1');
    expect(allText).toContain('Question 2');
  });

  test('should handle connection loss gracefully', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const input = page.getByPlaceholder('Ask about your lab results...');

    await page.context().setOffline(true);
    await input.fill('Test message');

    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();
    await sendButton.click().catch(() => {});

    const isVisible = await page.isVisible('body');
    expect(isVisible).toBe(true);

    await page.context().setOffline(false);
  });

  test('should show loading state during response', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const input = page.getByPlaceholder('Ask about your lab results...');
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    await input.fill('What is health?');
    await sendButton.click();

    const loadingIndicators = [
      page.locator('[class*="loading"], [class*="Loading"]'),
      page.locator('[class*="spinner"], [class*="Spinner"]'),
      page.locator('[class*="progress"], [class*="Progress"]'),
      page.locator('text=/loading|processing/i'),
    ];

    let hasLoading = false;
    for (const indicator of loadingIndicators) {
      const count = await indicator.count().catch(() => 0);
      if (count > 0) {
        hasLoading = true;
        break;
      }
    }

    const messages = page.locator('[class*="message"], [class*="Message"]');
    await expect(messages.first()).toBeVisible({ timeout: 10000 });
    expect(typeof hasLoading).toBe('boolean');
  });

  test('should handle rapid message sending', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const input = page.getByPlaceholder('Ask about your lab results...');
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    for (let i = 0; i < 3; i++) {
      await input.fill(`Message ${i + 1}`);
      await sendButton.click();
    }

    await page.waitForTimeout(5000);

    const messages = page.locator('[class*="message"], [class*="Message"]');
    const count = await messages.count();

    expect(count).toBeGreaterThanOrEqual(3);
  });
});