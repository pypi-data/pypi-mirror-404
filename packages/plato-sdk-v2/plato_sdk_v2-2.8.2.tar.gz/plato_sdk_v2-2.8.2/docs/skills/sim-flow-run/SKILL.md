---
name: sim-flow-run
description: Run the login flow to test it works. Use after audit is cleared.
allowed-tools: Bash, Read
context: fork
---

# Simulator Flow Run

**Pipeline Position:** Phase 3, Step 2
**Previous Step:** sim-flow-clear
**Next Step:** sim-flow-mutations

## API Key

**CRITICAL: Export this BEFORE running any plato commands:**
```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
```

---

## Input Required

From previous step (sim-flow-clear):
- Audit log cleared (0 mutations)

From sim-sandbox-login:
- `base/flows.yml` exists with login flow
- Credentials verified working

---

## Action

### Step 1: Verify Flow File Exists

```bash
plato sandbox verify flow
```

Must show login flow found with steps.

### Step 2: Run Login Flow

```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
plato sandbox flow login
```

This executes the login flow from flows.yml:
1. Navigates to login page
2. Fills credentials
3. Clicks submit
4. Waits for logged-in state

### Step 3: Check Flow Completed

The command output shows:
- Each step executed
- Success or failure for each
- Final status

---

## On Success

Output:
```yaml
sandbox_result:
  action: flow-run
  success: true
  flow: login
  steps_completed: 5
```

Proceed to: **sim-flow-mutations**

---

## On Failure

### If selector not found

The flow couldn't find an element. Check:
1. Selector is correct for this app
2. Page loaded before action
3. Element is visible (not hidden)

**Fix flows.yml:**
```yaml
steps:
  - action: fill
    selector: "input[name='email']"  # Try different selector
    value: "{{username}}"
```

### If timeout

Add wait step or increase timeout:
```yaml
steps:
  - action: wait
    timeout: 10000  # Wait up to 10 seconds
    selector: ".login-form"
  - action: fill
    ...
```

### If login fails (still on login page)

Credentials may be wrong or form submission failed:
1. Re-verify manual login works (sim-sandbox-login)
2. Check submit button selector
3. Check for JavaScript form validation

### Common Selector Fixes

**Username field:**
```yaml
# Try these in order
selector: "input[name='username']"
selector: "input[name='email']"
selector: "input[type='email']"
selector: "#username"
selector: "[data-testid='username']"
```

**Password field:**
```yaml
selector: "input[name='password']"
selector: "input[type='password']"
selector: "#password"
```

**Submit button:**
```yaml
selector: "button[type='submit']"
selector: "input[type='submit']"
selector: ".login-btn"
selector: "#login-button"
```

---

## DO NOT

- Run flow without clearing audit first
- Skip checking flow completed successfully
- Proceed if flow fails - fix the selectors
