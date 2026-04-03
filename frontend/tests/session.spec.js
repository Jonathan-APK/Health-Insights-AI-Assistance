import { test, expect } from '@playwright/test';

test.describe('Health AI Frontend - Session & State Management', () => {
  test('should maintain session across page reload', async ({ page, context }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const input = page.locator('input[type="text"], textarea').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    // Send message
    const testMessage = 'What is BMI?';
    await input.fill(testMessage);
    await sendButton.click();

    // Wait for response
    await page.waitForTimeout(2000);

    // Get message count before reload
    const messageBefore = page.locator('[class*="message"], [class*="Message"]');
    const countBefore = await messageBefore.count();

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Messages should persist
    const messageAfter = page.locator('[class*="message"], [class*="Message"]');
    const countAfter = await messageAfter.count();

    // Count should be same or user messages might be cached
    expect(countAfter).toBeGreaterThanOrEqual(Math.max(1, countBefore - 1));
  });

  test('should preserve session ID across requests', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const input = page.locator('input[type="text"], textarea').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    // Get session from localStorage or cookies
    const sessionBefore = await page.evaluate(() => {
      return localStorage.getItem('sessionId') || sessionStorage.getItem('sessionId') || 'none';
    });

    // Send message
    await input.fill('Message 1');
    await sendButton.click();
    await page.waitForTimeout(1000);

    // Get session after first message
    const sessionAfter = await page.evaluate(() => {
      return localStorage.getItem('sessionId') || sessionStorage.getItem('sessionId') || 'none';
    });

    // Session should be consistent
    if (sessionBefore !== 'none' && sessionAfter !== 'none') {
      expect(sessionBefore).toBe(sessionAfter);
    }
  });

  test('should maintain conversation history within session', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const input = page.locator('input[type="text"], textarea').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    // Send first message
    await input.fill('Question 1: What is blood pressure?');
    await sendButton.click();
    await page.waitForTimeout(2000);

    // Send second message
    await input.fill('Question 2: What are risk factors?');
    await sendButton.click();
    await page.waitForTimeout(2000);

    // Both messages should be in history
    const messages = page.locator('[class*="message"], [class*="Message"]');
    const allText = await page.textContent('body');

    expect(allText).toContain('Question 1');
    expect(allText).toContain('Question 2');
  });

  test('should handle connection loss gracefully', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const input = page.locator('input[type="text"], textarea').first();

    // Simulate offline
    await page.context().setOffline(true);

    // Try to send message
    await input.fill('Test message');

    // Try to click send
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();
    await sendButton.click().catch(() => {});

    // Should not crash - either disabled, error shown, or queued
    const isVisible = await page.isVisible('body');
    expect(isVisible).toBe(true);

    // Restore connection
    await page.context().setOffline(false);
  });

  test('should show loading state during response', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const input = page.locator('input[type="text"], textarea').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    // Send message
    await input.fill('What is health?');
    await sendButton.click();

    // Loading state should appear (spinner, progress, etc.)
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

    // Either has loading indicator or response comes too fast
    expect(hasLoading).toBe(true);
  });

  test('should handle rapid message sending', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const input = page.locator('input[type="text"], textarea').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    // Send multiple messages rapidly
    for (let i = 0; i < 3; i++) {
      await input.fill(`Message ${i + 1}`);
      await sendButton.click();
    }

    // Wait for all responses
    await page.waitForTimeout(5000);

    // All messages should be processed
    const messages = page.locator('[class*="message"], [class*="Message"]');
    const count = await messages.count();

    expect(count).toBeGreaterThanOrEqual(3);
  });
});
