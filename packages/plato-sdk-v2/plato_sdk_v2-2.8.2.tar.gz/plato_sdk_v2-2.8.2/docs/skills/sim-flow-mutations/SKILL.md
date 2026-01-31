---
name: sim-flow-mutations
description: Check mutations after login flow. Use after flow completes.
allowed-tools: Bash, Read, Edit
context: fork
---

# Simulator Flow Mutations

**Pipeline Position:** Phase 3, Step 3
**Previous Step:** sim-flow-run
**Next Step:** sim-flow-audit (if 0 mutations) or loop back to fix

## API Key

**CRITICAL: Export this BEFORE running any plato commands:**
```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
```

---

## Input Required

From previous step (sim-flow-run):
- Login flow completed successfully

---

## Goal

Verify login flow creates 0 mutations.

**Login should be read-only.** If it creates mutations, we need to either:
1. Fix the flow (it's doing something wrong)
2. Add tables/columns to `audit_ignore_tables` (legitimate app behavior)

---

## Action

### Step 1: Check Mutations

```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
plato sandbox verify mutations
```

---

## If 0 Mutations (SUCCESS)

Output shows:
```
✅ Mutation verification passed
Mutations after login: 0
Login is read-only - ready for snapshot.
```

Proceed to: **sim-flow-audit**

---

## If Mutations Found (NEEDS FIX)

The verify command will show:
1. Table breakdown (which tables have mutations)
2. Operation breakdown (INSERT vs UPDATE)
3. Suggested fixes

### Understanding the Output

```
Mutations after login: 170

Table                           INSERT  UPDATE  DELETE
common_inventreesetting         85      0       0
common_inventreeusersetting     45      0       0
plugin_pluginsetting            40      0       0
```

### Fixing Mutations

Add tables/columns to `audit_ignore_tables` in plato-config.yml:

**Ignore entire table:**
```yaml
listeners:
  db:
    audit_ignore_tables:
      - sessions                    # Ignore all changes to this table
      - common_inventreesetting
```

**Ignore specific columns (inline format - PREFERRED):**
```yaml
listeners:
  db:
    audit_ignore_tables:
      - users: [last_login, updated_at]
      - kimai2_users: [last_login, totp_secret]
```

**Verbose format (also supported):**
```yaml
listeners:
  db:
    audit_ignore_tables:
      - table: users
        columns: [last_login, updated_at]
```

**IMPORTANT:** Do NOT use a separate `ignore_columns` field. Column-level ignores must be inside `audit_ignore_tables`.

### After Fixing Config

Must restart worker and re-test:

```bash
plato sandbox stop-worker
plato sandbox start-worker --wait
plato sandbox clear-audit
plato sandbox flow login
plato sandbox verify mutations
```

---

## Decision Tree

1. **Are mutations INSERT operations?**
   - YES → Ignore entire table (column-level won't help)
   - NO → Continue

2. **Are mutations UPDATE on timestamp columns?**
   - YES → Use column-level ignore
   - NO → Investigate what's actually changing

3. **Is the table important user data?**
   - YES → Be very careful, maybe don't ignore
   - NO (sessions, settings, cache) → Safe to ignore

---

## DO NOT

- Ignore tables blindly - understand what's being ignored
- Use column-level ignores for INSERT mutations - they don't work
- Proceed to snapshot with mutations - fix them first
- Ignore user data tables entirely - use column-level for timestamps
