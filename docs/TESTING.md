# Frontend Testing

This project includes comprehensive frontend testing following Svelte testing best practices from https://svelte.dev/docs/svelte/testing.

## Testing Infrastructure

### Unit Testing with Vitest

We use Vitest with @testing-library/svelte for component unit testing:

- **Test runner**: Vitest (fast, modern test runner with built-in TypeScript support)
- **Component testing**: @testing-library/svelte (follows testing-library principles)
- **Environment**: jsdom (simulates browser environment for tests)
- **Assertions**: jest-dom matchers for better DOM assertions

### End-to-End Testing with Playwright

We use Playwright for E2E testing:

- **E2E runner**: Playwright (cross-browser testing)
- **Configuration**: `playwright.config.ts`
- **Test location**: `tests/e2e/`

## Running Tests

### Unit Tests

```bash
# Run tests once
npm run test:run

# Run tests in watch mode (during development)
npm test

# Run tests with UI (visual interface)
npm run test:ui
```

### E2E Tests

```bash
# Run E2E tests
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui
```

## Test Structure

### Unit Tests (`src/tests/`)

- `GitHubUser.test.ts` - Tests GitHubUser component rendering and props
- `Tooltip.test.ts` - Tests Tooltip positioning and show/hide behavior
- `ConsolePrompt.test.ts` - Tests console prompt rendering
- `Details.test.ts` - Tests collapsible details component
- `Infrastructure.test.ts` - Tests testing infrastructure capabilities

### E2E Tests (`tests/e2e/`)

- `basic.test.ts` - Tests basic page loading and navigation

## Writing Tests

### Unit Test Example

```typescript
import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import MyComponent from '../lib/components/MyComponent.svelte';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(MyComponent, {
      props: {
        title: 'Test Title'
      }
    });
    
    expect(screen.getByText('Test Title')).toBeInTheDocument();
  });
});
```

### E2E Test Example

```typescript
import { test, expect } from '@playwright/test';

test('should navigate to page', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/Expected Title/);
});
```

## Configuration

### Vitest Configuration (`vite.config.ts`)

```typescript
test: {
  include: ["src/**/*.{test,spec}.{js,ts}"],
  environment: "jsdom",
  setupFiles: ["./src/tests/setup.ts"],
  globals: true
}
```

### Setup File (`src/tests/setup.ts`)

```typescript
import '@testing-library/jest-dom';
```

## Best Practices

1. **Test behavior, not implementation**: Focus on what users see and do
2. **Use semantic queries**: Prefer `getByRole`, `getByLabelText` over `getByTestId`
3. **Test accessibility**: Ensure components are accessible
4. **Keep tests simple**: One assertion per test when possible
5. **Mock external dependencies**: Don't test third-party libraries
6. **Use descriptive test names**: Make test intentions clear

## Current Test Coverage

- **GitHubUser**: Avatar rendering, fallback text, props handling
- **Tooltip**: Show/hide behavior, positioning, CSS classes
- **ConsolePrompt**: Prompt rendering, customization
- **Details**: Collapsible behavior, summary handling
- **Infrastructure**: User interactions, form testing, async operations

## Browser Support (E2E)

- Chromium (Chrome, Edge)
- Firefox
- WebKit (Safari)

Tests run against all major browsers to ensure cross-browser compatibility.