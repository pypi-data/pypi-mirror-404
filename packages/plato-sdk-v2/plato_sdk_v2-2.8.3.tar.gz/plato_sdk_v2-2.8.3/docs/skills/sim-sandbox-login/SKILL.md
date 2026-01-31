---
name: sim-sandbox-login
description: Manually log into the app via browser to verify it works. Use after services are started.
allowed-tools: Bash, Read, Write, Edit, mcp__playwright__browser_navigate, mcp__playwright__browser_snapshot, mcp__playwright__browser_type, mcp__playwright__browser_click, mcp__playwright__browser_take_screenshot
context: fork
---

# Simulator Sandbox Login

**Pipeline Position:** Phase 2, Step 3
**Previous Step:** sim-sandbox-services
**Next Step:** sim-sandbox-worker

## Purpose

Manually verify the app works by logging in via browser BEFORE starting the worker.
This catches issues early and avoids infinite error loops in the worker.

---

## Input Required

From previous step (sim-sandbox-services):
- Services running and healthy
- Public URL accessible (returns 200)

From research/config:
- Login credentials (username, password)
- Login URL (usually / or /login)

---

## Action

### Step 1: Get Public URL

```bash
cat .sandbox.yaml | grep public_url
```

Or read from .sandbox.yaml file.

### Step 2: Navigate to Login Page

```
mcp__playwright__browser_navigate to {public_url}
mcp__playwright__browser_snapshot
```

### Step 3: Analyze the Page

Look for:
- Login form (username/email field, password field, submit button)
- Setup wizard (if first-time setup required)
- Error messages

**If setup wizard appears:**
1. Complete the setup wizard
2. Save any admin credentials you create
3. Continue to login

### Step 4: Log In

```
mcp__playwright__browser_type username into username/email field
mcp__playwright__browser_type password into password field
mcp__playwright__browser_click submit/login button
mcp__playwright__browser_snapshot
```

### Step 5: Verify Logged In

After login, verify:
- Dashboard or home page visible (NOT login page)
- User menu, profile dropdown, or logout button visible
- URL is NOT /login, /signin, etc.
- No error messages

### Step 6: Save Credentials for flows.yml

Create or update `base/flows.yml` with the working credentials:

```yaml
login:
  steps:
    - action: navigate
      url: "{login_url}"
    - action: fill
      selector: "input[name='username']"  # Adjust selector
      value: "{{username}}"
    - action: fill
      selector: "input[name='password']"  # Adjust selector
      value: "{{password}}"
    - action: click
      selector: "button[type='submit']"   # Adjust selector
    - action: wait
      selector: ".dashboard"              # Adjust to logged-in indicator
```

### Step 7: Verify (Manual)

```bash
plato sandbox verify login
```

This will prompt you to confirm:
- Dashboard visible
- No setup wizards
- Credentials saved

---

## On Success

Output:
```yaml
sandbox_result:
  action: login
  success: true
  login_verified: true
  credentials:
    username: "{username}"
    password: "{password}"
  flows_yml_created: true
```

Proceed to: **sim-sandbox-worker**

---

## On Failure

### If login page not found

- Check public_url is correct
- Check start_url in plato-config.yml
- App may redirect to different URL

### If login fails (still on login page after submit)

- Credentials incorrect - check research report
- Form selectors wrong - inspect the page
- App requires email verification or 2FA

### If setup wizard appears

This is normal for first-time setup:
1. Complete the wizard
2. Create admin account (save credentials!)
3. The credentials you create become the login credentials
4. Update research report and flows.yml with new credentials

### If error message after login

- Check credentials
- App may have additional requirements (terms acceptance, etc.)
- Check browser console for errors

---

## Selector Discovery

To find the right selectors, use browser snapshot and look for:

**Username field patterns:**
- `input[name="username"]`
- `input[name="email"]`
- `input[type="email"]`
- `input[id="username"]`
- `[data-testid="username"]`

**Password field patterns:**
- `input[name="password"]`
- `input[type="password"]`
- `input[id="password"]`

**Submit button patterns:**
- `button[type="submit"]`
- `button.login-btn`
- `input[type="submit"]`
- `[data-testid="login-button"]`

**Logged-in indicators:**
- `.dashboard`
- `.home`
- `[data-testid="user-menu"]`
- `.logout-button`
- URL change to /dashboard, /home, etc.

---

## DO NOT

- Start worker before verifying login works
- Skip this step - login issues cause worker to loop forever
- Proceed if login fails
- Create test data during login verification
