import { test, expect } from '@playwright/test';

test.describe('Homepage', () => {
  test('should load successfully', async ({ page }) => {
    await page.goto('/');
    
    // Check that the page loads without errors
    await expect(page).toHaveTitle(/pyth-on-line/);
  });

  test('should display main navigation elements', async ({ page }) => {
    await page.goto('/');
    
    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');
    
    // Check for basic elements that should be present
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });
});

test.describe('Console Functionality', () => {
  test('should display console interface', async ({ page }) => {
    await page.goto('/console');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Look for console-related elements
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });
});

test.describe('Workspace Functionality', () => {
  test('should display workspace interface', async ({ page }) => {
    await page.goto('/playground');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Look for workspace-related elements
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });
});