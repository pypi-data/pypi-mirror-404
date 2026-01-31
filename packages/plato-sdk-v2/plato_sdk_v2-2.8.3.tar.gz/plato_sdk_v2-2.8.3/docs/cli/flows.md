# Creating Flows

Flows are YAML-defined browser automation sequences used to test simulator login and other interactions. They use Playwright under the hood.

## File Structure

Flows are typically stored in a `flows/` directory:

```
mysim/
├── plato-config.yml
├── flows/
│   └── flows.yaml
└── ...
```

Reference the flows file in your `plato-config.yml`:

```yaml
datasets:
  base:
    metadata:
      flows_path: flows/flows.yaml
```

## Flow File Format

```yaml
flows:
  - name: login
    description: Standard login flow for MyApp
    steps:
      - type: navigate
        url: /login
      - type: fill
        selector: "#email"
        value: "admin@example.com"
      # ... more steps
```

## Available Step Types

### Navigation

#### `navigate`
Navigate to a URL (relative or absolute).

```yaml
- type: navigate
  url: /login
  description: Go to login page
```

#### `wait_for_url`
Wait for URL to contain specific text.

```yaml
- type: wait_for_url
  url_contains: /dashboard
  timeout: 10000
```

### Input

#### `fill`
Fill an input field with a value.

```yaml
- type: fill
  selector: "#email"
  value: "admin@example.com"

- type: fill
  selector: "#password"
  value: "secretpassword"
```

#### `click`
Click on an element.

```yaml
- type: click
  selector: "button[type='submit']"
  description: Click login button
```

### Waiting

#### `wait`
Wait for a fixed duration (milliseconds).

```yaml
- type: wait
  duration: 3000
  description: Wait for page to load
```

#### `wait_for_selector`
Wait for an element to appear in the DOM.

```yaml
- type: wait_for_selector
  selector: ".dashboard-content"
  timeout: 10000
```

### Verification

#### `verify_text`
Verify text appears (or doesn't appear) on the page.

```yaml
- type: verify_text
  text: "Welcome back"
  should_exist: true

- type: verify_text
  text: "Invalid credentials"
  should_exist: false
```

#### `verify_url`
Verify the current URL.

```yaml
- type: verify_url
  url: /dashboard
  contains: true  # URL contains this string
```

#### `verify_no_errors`
Verify no error indicators are visible.

```yaml
- type: verify_no_errors
  error_selectors:
    - ".error"
    - ".alert-danger"
    - "[role='alert']"
```

#### `check_element`
Check if an element exists (non-blocking).

```yaml
- type: check_element
  selector: ".user-menu"
  should_exist: true
```

#### `verify`
Generic verification with multiple sub-types.

```yaml
# Verify element exists
- type: verify
  verify_type: element_exists
  selector: ".dashboard"

# Verify element is visible
- type: verify
  verify_type: element_visible
  selector: ".welcome-message"

# Verify element text
- type: verify
  verify_type: element_text
  selector: ".username"
  text: "admin"
  contains: true

# Verify element count
- type: verify
  verify_type: element_count
  selector: ".menu-item"
  count: 5

# Verify page title
- type: verify
  verify_type: page_title
  title: "Dashboard"
  contains: true
```

### Screenshots

#### `screenshot`
Take a screenshot for visual verification.

```yaml
- type: screenshot
  filename: after_login.png
  description: Screenshot after successful login
  full_page: false
```

Screenshots are saved to the `screenshots/` directory with timestamps.

## Common Step Options

All steps support these options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `description` | string | null | Human-readable description |
| `timeout` | int | 10000 | Timeout in milliseconds |
| `retries` | int | 0 | Number of retry attempts |
| `retry_delay_ms` | int | 500 | Delay between retries |

## Example: Complete Login Flow

```yaml
flows:
  - name: login
    description: Standard login flow for MyApp
    steps:
      # Screenshot initial state
      - type: screenshot
        filename: 01_initial.png
        description: Initial page before login

      # Wait for page to load
      - type: wait
        duration: 2000
        description: Wait for page to fully load

      # Navigate to login (if not already there)
      - type: navigate
        url: /login
        description: Go to login page

      # Wait for login form
      - type: wait_for_selector
        selector: "form#login-form"
        timeout: 10000
        description: Wait for login form

      # Fill credentials
      - type: fill
        selector: "#email"
        value: "admin@example.com"
        description: Enter email

      - type: fill
        selector: "#password"
        value: "password123"
        description: Enter password

      # Screenshot before submit
      - type: screenshot
        filename: 02_credentials_entered.png
        description: Form filled with credentials

      # Submit
      - type: click
        selector: "button[type='submit']"
        description: Click login button

      # Wait for redirect
      - type: wait
        duration: 3000
        description: Wait for login to process

      # Verify success
      - type: verify_url
        url: /dashboard
        contains: true
        description: Verify redirected to dashboard

      - type: verify_no_errors
        description: Verify no error messages

      - type: verify_text
        text: "Welcome"
        should_exist: true
        description: Verify welcome message

      # Final screenshot
      - type: screenshot
        filename: 03_logged_in.png
        description: Successfully logged in
```

## Example: Login with OAuth/SSO

```yaml
flows:
  - name: login
    description: OAuth login flow
    steps:
      - type: navigate
        url: /

      - type: wait
        duration: 2000

      # Click OAuth login button
      - type: click
        selector: "button.oauth-login"
        description: Click "Login with Google"

      # OAuth may redirect - wait for callback
      - type: wait
        duration: 5000
        description: Wait for OAuth flow

      # Verify logged in
      - type: wait_for_selector
        selector: ".user-avatar"
        timeout: 15000
        description: Wait for user avatar (logged in indicator)

      - type: screenshot
        filename: logged_in.png
```

## Example: Login with 2FA

```yaml
flows:
  - name: login
    description: Login with 2FA
    steps:
      # Initial login
      - type: navigate
        url: /login

      - type: fill
        selector: "#email"
        value: "admin@example.com"

      - type: fill
        selector: "#password"
        value: "password123"

      - type: click
        selector: "button[type='submit']"

      # Wait for 2FA page
      - type: wait_for_selector
        selector: "#otp-input"
        timeout: 10000

      # Enter OTP (for testing, use a known test OTP)
      - type: fill
        selector: "#otp-input"
        value: "123456"

      - type: click
        selector: "button#verify-otp"

      # Verify success
      - type: wait_for_url
        url_contains: /dashboard
        timeout: 10000
```

## Finding Selectors

Use browser DevTools to find CSS selectors:

1. Right-click element → "Inspect"
2. In Elements panel, right-click element → "Copy" → "Copy selector"

**Best practices for selectors:**
- Prefer `id` selectors: `#login-button`
- Use `data-testid` if available: `[data-testid='submit-btn']`
- Use semantic selectors: `button[type='submit']`
- Avoid fragile selectors: `.class1 > div:nth-child(3)`

## Running Flows

```bash
# Run default login flow
plato sandbox flow

# Run specific flow
plato sandbox flow --flow-name login

# Run a different flow
plato sandbox flow --flow-name checkout
```

## Debugging Flows

If a flow fails:

1. **Check screenshots** - Look in `screenshots/` for visual state
2. **Check selectors** - Use browser DevTools to verify selectors exist
3. **Add wait steps** - Pages may need more time to load
4. **Add verification steps** - Verify state before continuing
5. **Check timeouts** - Increase timeout for slow operations

## See Also

- [Sandbox Commands](sandbox.md) - Running flows with `plato sandbox flow`
- [Simulator Lifecycle](../SIMULATOR_LIFECYCLE.md) - When to create and test flows
