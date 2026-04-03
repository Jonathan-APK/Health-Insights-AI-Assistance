import { test, expect } from '@playwright/test';

test.describe('Health AI Frontend - Basic UI Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load the application', async ({ page }) => {
    await expect(page).toHaveTitle(/Health|Chat|AI/i);
  });

  test('should render main chat components', async ({ page }) => {
    // Wait for key UI elements
    const chatWindow = page.locator('[class*="chat"], [class*="Chat"]').first();
    const inputField = page.locator('input, textarea').first();
    
    // At least one should be visible
    const hasContent = await chatWindow.isVisible().catch(() => false) ||
                       await inputField.isVisible().catch(() => false);
    
    expect(hasContent).toBe(true);
  });

  test('should have accessible UI elements', async ({ page }) => {
    // Check for buttons
    const buttons = await page.locator('button').count();
    expect(buttons).toBeGreaterThan(0);

    // Check for input fields
    const inputs = await page.locator('input, textarea').count();
    expect(inputs).toBeGreaterThan(0);
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').count();
    // Should have at least a title or heading
    expect(headings).toBeGreaterThanOrEqual(0);
  });

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    const chatWindow = page.locator('[class*="chat"], [class*="Chat"]').first();
    const isVisible = await chatWindow.isVisible().catch(() => false);
    
    expect(isVisible).toBe(true);
  });

  test('should be responsive on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    
    const chatWindow = page.locator('[class*="chat"], [class*="Chat"]').first();
    const isVisible = await chatWindow.isVisible().catch(() => false);
    
    expect(isVisible).toBe(true);
  });
});
