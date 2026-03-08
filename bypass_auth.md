# Authentication Bypass Log

This file documents the application code bypassed to facilitate easier local development and testing without authentication.

## 1. Frontend Route Guard Bypass

**File:** `frontend/src/auth/RequireAuth.tsx`

**Description:** The React application utilizes Azure MSAL to protect routes via the `RequireAuth` component.
The following logic has been explicitly commented out to temporarily disable route protection:
* **Lines 14-16:** Block redirecting users to the `/login` page if no MSAL account is logged in (`accounts.length === 0`).
* **Lines 28-62:** Block the "Access Denied" return block which previously checked for the `SmartFactory.Admin` user role.

Since the backend API currently operates without authentication middleware, commenting out the MSAL validations locally grants complete access to the web app frontend.

## 2. Cosmos DB Initialization Bypass

**Files:**
- `backend/shared/cosmos.py`
- `azure-functions/shared/cosmos.py`

**Description:** Manual edits were made by the developer to read `COSMOS-CONN-READ` and `COSMOS-CONN-WRITE` strings from `os.getenv` via a local `.env` instead of calling `get_secret` from the Azure Key Vault. This bypasses the need for the server to authenticate identity using Azure Identity.
Exact lines modified in both files:
* **Line 11:** Commented out `from shared.secrets import get_secret`.
* **Lines 12-15:** Added imports for `dotenv` and `os`, and called `load_dotenv()`.
* **Lines 23-27:** Replaced `get_secret("COSMOS-CONN-READ")` and `get_secret("COSMOS-CONN-WRITE")` with `os.getenv("...")`. The original `get_secret` calls were commented out on lines 24/25 and 26/27 depending on the file.

## 3. App Router Bypass

**File:** `frontend/src/App.tsx`

**Description:** The application router was modified to skip the login page entirely and direct all users straight to the dashboard without checking authentication status.
The following exact lines were removed/modified:
* **Line 8:** Removed the `import RequireAuth from "./auth/RequireAuth";` statement.
* **Lines 38-46:** Removed the `<RequireAuth>` component wrapper that protected the `<ProtectedLayout />`. The route now simply renders `<ProtectedLayout />` directly.
* **Lines 48-49:** Modified the catch-all wildcard route (`*`) to redirect to `"/dashboard"` instead of `"/login"`.
