# Raycast Localhost Permission Monitoring

## Problem

Raycast extensions require explicit `"localhost": true` permission in `package.json` to make network requests to `http://localhost:8000`.

Without this permission:
- Backend appears healthy (`make health` returns 200 OK)
- `curl localhost:8000` works fine
- But Raycast extension fails with: **"DSPy backend not available"**

**Root cause**: Auto-formatters (Prettier/ESLint) sometimes remove this permission.

## Solution: Automated Monitoring

### 1. Pre-flight Check (runs automatically)

```bash
npm run dev
```

The `predev` script automatically checks for localhost permission **before** starting Raycast dev server.

**If permission is missing:**
```
❌ CRITICAL: Localhost permission MISSING from package.json

🔧 FIX: Add this line to package.json after 'license':
   "localhost": true,

Then restart Raycast dev server.
```

### 2. Manual Check Script

```bash
./scripts/check-localhost-permission.sh
```

Use this anytime to verify permission status.

### 3. Runtime Detection (in code)

Import the monitoring helper in your code:

```typescript
import { fetchWithPermissionCheck, logLocalhostError } from "./core/monitoring/localhostPermission";

// Automatic permission check with detailed error messages
const response = await fetchWithPermissionCheck("http://localhost:8000/health");

// Or manually log errors
try {
  const response = await fetch("http://localhost:8000/api/v1/improve-prompt", {...});
} catch (error) {
  logLocalhostError("http://localhost:8000/api/v1/improve-prompt", error);
  throw error;
}
```

When localhost permission is missing, you'll see detailed console logs:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 LOCALHOST PERMISSION ERROR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Raycast cannot connect to localhost - missing permission

FIX: Add this line to dashboard/package.json:
  "localhost": true,

Then restart Raycast dev server:
  1. Stop current dev server (Cmd+C)
  2. Run: cd dashboard && npm run dev
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## How It Works

### Pre-flight Check (`check-localhost-permission.sh`)

1. Scans `package.json` for `"localhost": true`
2. If found → ✅ Proceeds with dev server startup
3. If missing → ❌ Exits with error message and fix instructions

### Runtime Detection (`localhostPermission.ts`)

1. Wraps fetch calls with `fetchWithPermissionCheck()`
2. Catches fetch errors
3. Analyzes error type to distinguish:
   - **Missing permission** → TypeError with no server response
   - **Backend not running** → Connection refused but permission exists
4. Logs specific, actionable error messages

## Prevention: Git Hook (Optional)

To prevent commits without localhost permission:

```bash
# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Check localhost permission before committing

if grep -q '"localhost": true' dashboard/package.json; then
  exit 0
else
  echo "❌ Cannot commit: Missing localhost permission in dashboard/package.json"
  echo "   Add: \"localhost\": true,"
  exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

## Testing the Monitor

### Test 1: Verify permission exists (should pass)
```bash
./scripts/check-localhost-permission.sh
# Expected: ✅ Localhost permission is present
```

### Test 2: Simulate missing permission (should fail)
```bash
# Temporarily remove permission
sed -i.bak '/"localhost": true/d' dashboard/package.json

# Run check
./scripts/check-localhost-permission.sh
# Expected: ❌ CRITICAL: Localhost permission MISSING

# Restore permission
mv dashboard/package.json.bak dashboard/package.json
```

## Troubleshooting

### "permission check fails but permission exists"

**Cause**: Whitespace/formatting differences

**Fix**: The script looks for exact match: `"localhost": true`

Check your package.json:
```json
{
  "license": "MIT",
  "localhost": true,  // ← Must be exactly here
  "commands": [...]
}
```

### "npm run dev doesn't run predev script"

**Cause**: npm version doesn't support pre hooks

**Fix**: Run check manually:
```bash
./scripts/check-localhost-permission.sh && npm run dev
```

### "Runtime detection doesn't work"

**Cause**: Using `fetch` directly instead of `fetchWithPermissionCheck()`

**Fix**: Wrap your fetch calls:
```typescript
// Before
const response = await fetch(url, options);

// After
import { fetchWithPermissionCheck } from "./core/monitoring/localhostPermission";
const response = await fetchWithPermissionCheck(url, options);
```

## Files Added

1. `dashboard/scripts/check-localhost-permission.sh` - Pre-flight check script
2. `dashboard/src/core/monitoring/localhostPermission.ts` - Runtime detection
3. `dashboard/scripts/README.md` - This documentation

## Integration with Existing Code

The monitoring is **non-breaking** - existing code continues to work. To enable runtime detection, update your fetch calls to use `fetchWithPermissionCheck()`.
