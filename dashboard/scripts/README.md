# Raycast Localhost Permission Monitoring

## Problem

Raycast extensions require explicit `"localhost": true` permission in `package.json` to make network requests to `http://localhost:8000`.

Without this permission:
- Backend appears healthy (`make health` returns 200 OK)
- `curl localhost:8000` works fine
- But Raycast extension fails with: **"DSPy backend not available"**

**Root cause**: Auto-formatters (Prettier/ESLint) sometimes remove this permission.

## Solution: Makefile Integration

### Quick Start (using Makefile)

```bash
# Start Raycast dev server with automatic permission check
make ray-dev

# Check permission status anytime
make ray-check

# Check Raycast dev server status
make ray-status

# View Raycast dev server logs
make ray-logs
```

### How It Works

When you run `make ray-dev`:

1. **Pre-flight check** runs automatically (`make ray-check`)
2. ✅ If permission exists → Starts Raycast dev server
3. ❌ If permission missing → Shows error and **exits without starting**

**Example error output:**
```
→ Checking localhost permission...
✗ CRITICAL: Localhost permission MISSING from package.json

   Without this permission, the extension CANNOT connect to the DSPy backend.
   You will see: 'DSPy backend not available' errors.

   🔧 FIX: Add this line to dashboard/package.json after 'license':

   {
     "name": "prompt-improver-local",
     "license": "MIT",
     "localhost": true,  // ← ADD THIS LINE
     "commands": [...]
   }

   Then restart Raycast dev server.
```

## Available Make Commands

| Command | Purpose |
|---------|---------|
| `make ray-check` | Check if localhost permission exists |
| `make ray-dev` | Start Raycast dev server (with pre-check) |
| `make ray-status` | Show Raycast dev server status |
| `make ray-logs` | Tail Raycast dev server logs |

### Integration with Backend

Typical workflow:

```bash
# Start DSPy backend
make dev

# Start Raycast frontend (with permission check)
make ray-dev

# Check both services status
make status          # Backend status
make ray-status     # Raycast status
```

## Runtime Detection (in code)

For runtime error detection when fetch fails:

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
  2. Run: make ray-dev
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Testing the Monitor

### Test 1: Verify permission exists (should pass)
```bash
make ray-check
# Expected: ✓ Localhost permission is present
```

### Test 2: Simulate missing permission (should fail)
```bash
# Temporarily remove permission
sed -i.bak '/"localhost": true/d' dashboard/package.json

# Run check
make ray-check
# Expected: ✗ CRITICAL: Localhost permission MISSING

# Restore permission
mv dashboard/package.json.bak dashboard/package.json
```

## Git Pre-commit Hook

The project includes a git pre-commit hook (in `.git/hooks/pre-commit`) that prevents commits without localhost permission.

When you commit changes:
```bash
git commit -m "some changes"
```

The hook automatically:
1. Checks if `"localhost": true` exists in `dashboard/package.json`
2. ✅ Permission exists → Allows commit
3. ❌ Permission missing → Blocks commit with fix instructions

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

### "make ray-dev doesn't work"

**Cause**: Missing npm dependencies

**Fix**:
```bash
cd dashboard
npm install
cd ..
make ray-dev
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

1. `Makefile` - Updated with Raycast commands (ray-check, ray-dev, ray-status, ray-logs)
2. `dashboard/src/core/monitoring/localhostPermission.ts` - Runtime detection helper
3. `dashboard/scripts/README.md` - This documentation
4. `.git/hooks/pre-commit` - Git hook to prevent commits without permission

## Integration with Existing Code

The monitoring is **non-breaking** - existing code continues to work. To enable runtime detection, update your fetch calls to use `fetchWithPermissionCheck()`.
