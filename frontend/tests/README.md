# Playwright E2E Tests

This directory contains end-to-end tests for the Health Insights AI Frontend using Playwright.

## Setup

### Install Playwright and dependencies

```bash
npm install --save-dev @playwright/test
npm install
```

### Install browsers

```bash
npx playwright install
```

## Running Tests

### Run all tests

```bash
npx playwright test
```

### Run tests in a specific browser

```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### Run tests in headed mode (see browser)

```bash
npx playwright test --headed
```

### Run tests with UI mode (interactive)

```bash
npx playwright test --ui
```

### Run specific test file

```bash
npx playwright test tests/chat.spec.js
```

### Run tests matching a pattern

```bash
npx playwright test -g "should send a text message"
```

### Run in debug mode

```bash
npx playwright test --debug
```

## Test Structure

### `ui.spec.js`
- Basic UI rendering
- Responsive design (mobile/desktop)
- Accessibility checks

### `chat.spec.js`
- Text message sending
- Message display
- Conversation history
- Input validation

### `file-upload.spec.js`
- File selection
- PDF upload
- File handling
- Upload with message

### `compliance.spec.js`
- No diagnosis provision
- Professional consultation encouragement
- Emergency case redirection (Singapore: 999)
- No medication recommendations
- Safety compliance checks
- Disclaimer display

### `session.spec.js`
- Session persistence
- Conversation history
- Loading states
- Connection loss handling
- Rapid message handling

## Configuration

The `playwright.config.js` file configures:

- **baseURL**: `http://localhost:3000`
- **browsers**: Chromium, Firefox, WebKit
- **devices**: Desktop Chrome, Firefox, Safari, Mobile Chrome
- **webServer**: Auto-starts dev server before tests
- **recording**: Screenshots and videos on failure
- **traces**: Auto-imported on test failure

## CI/CD Integration

For CI pipelines:

```bash
CI=true npx playwright test
```

This enables:
- Slower retries (2 retries)
- Sequential execution (1 worker)
- GitHub Actions/GitLab ready

## Debugging Failed Tests

1. **Check screenshots/videos**:
   ```bash
   npm run test:debug
   ```

2. **View test report**:
   ```bash
   npx playwright show-report
   ```

3. **Use VS Code extension**:
   - Install "Playwright Test for VSCode"
   - Run from editor with debugging

## Best Practices

- ✅ Tests run against live dev server
- ✅ Tests are isolated and don't affect each other
- ✅ Use descriptive test names
- ✅ Wait for elements explicitly (don't rely on timeouts)
- ✅ Clean up test files after upload tests
- ✅ Test critical user workflows first

## Medical Safety Notes

These tests ensure:
- 🏥 No unauthorized medical diagnoses
- 💊 No medication recommendations without caution
- 🚨 Emergency cases properly redirected
- 📋 Compliance and disclaimers shown
- 🔒 Session data properly managed
- 📱 Cross-browser consistency for accessibility

## References

- [Playwright Documentation](https://playwright.dev)
- [Playwright Test API](https://playwright.dev/docs/api/class-test)
- [Locators Guide](https://playwright.dev/docs/locators)
