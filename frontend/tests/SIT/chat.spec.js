import { test, expect } from '@playwright/test';

test.describe('Health AI Frontend - Chat Interactions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should send a text message', async ({ page }) => {
    const input = page.locator('input[type="text"], textarea').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    await input.fill('What is blood pressure?');
    await sendButton.click();

    const response = page.locator('[class*="message"], [class*="Message"]');
    await expect(response.first()).toBeVisible({ timeout: 10000 });
  });

  test('should display user message in chat', async ({ page }) => {
    const input = page.locator('input[type="text"], textarea').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    const userMessage = 'What is diabetes?';
    await input.fill(userMessage);
    await sendButton.click();

    await expect(page.locator('text=' + userMessage)).toBeVisible({ timeout: 5000 });
  });

  test('should display bot response in chat', async ({ page }) => {
    const input = page.locator('input[type="text"], textarea').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    await input.fill('What is hemoglobin?');
    await sendButton.click();

    const messages = page.locator('[class*="message"], [class*="Message"]');
    await expect(messages.nth(1)).toBeVisible({ timeout: 10000 });
  });

  test('should clear input after sending', async ({ page }) => {
    const input = page.locator('input[type="text"], textarea').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    await input.fill('Test message');
    const initialValue = await input.inputValue();
    expect(initialValue).toBe('Test message');

    await sendButton.click();

    await page.waitForTimeout(1000);
    const finalValue = await input.inputValue();
    expect(finalValue).toBe('');
  });

  test('should handle multiple messages in sequence', async ({ page }) => {
    const input = page.locator('input[type="text"], textarea').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    await input.fill('What is hypertension?');
    await sendButton.click();
    await page.waitForTimeout(2000);

    await input.fill('What are the risk factors?');
    await sendButton.click();

    const messages = page.locator('[class*="message"], [class*="Message"]');
    const count = await messages.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test('should not send empty messages', async ({ page }) => {
    const input = page.locator('input[type="text"], textarea').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    await input.fill('');

    const isDisabled = await sendButton.isDisabled();
    if (isDisabled) {
      expect(isDisabled).toBe(true);
    } else {
      await sendButton.click();
      const messages = page.locator('[class*="message"]');
      const count = await messages.count();
      expect(count).toBeLessThanOrEqual(1);
    }
  });

  test('should handle special characters in messages', async ({ page }) => {
    const input = page.locator('input[type="text"], textarea').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    const specialMessage = '血壓 @#$%^& What is "blood pressure"?';
    await input.fill(specialMessage);
    await sendButton.click();

    await expect(page.locator('[class*="message"], [class*="Message"]').first()).toBeVisible({ timeout: 5000 });
  });

  test('should handle long messages', async ({ page }) => {
    const input = page.locator('input[type="text"], textarea').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    const longMessage = 'What is health? '.repeat(20);
    await input.fill(longMessage);
    await sendButton.click();

    await expect(page.locator('[class*="message"], [class*="Message"]').first()).toBeVisible({ timeout: 10000 });
  });

  test('should maintain conversation history', async ({ page }) => {
    const input = page.locator('input[type="text"], textarea').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit|ask/i }).first();

    await input.fill('What is BMI?');
    await sendButton.click();
    await page.waitForTimeout(2000);

    await input.fill('How is it calculated?');
    await sendButton.click();

    const messages = page.locator('[class*="message"], [class*="Message"]');
    const count = await messages.count();
    expect(count).toBeGreaterThanOrEqual(3);
  });
});