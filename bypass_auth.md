# Authentication Bypass Log

This file documents the application code bypassed to facilitate easier local development and testing without authentication.

## 1. Frontend Route Guard Bypass

**File:** `frontend/src/auth/RequireAuth.tsx`

**Description:** The React application utilizes Azure MSAL to protect routes via the `RequireAuth` component.
The following logic has been explicitly commented out to temporarily disable route protection:
* Block redirecting users to the `/login` page if no MSAL account is logged in (`accounts.length === 0`).
* Block the "Access Denied" return block which previously checked for the `SmartFactory.Admin` user role.

Since the backend API currently operates without authentication middleware, commenting out the MSAL validations locally grants complete access to the web app frontend.

## 2. Cosmos DB Initialization Bypass

**Files:**
- `backend/shared/cosmos.py`
- `azure-functions/shared/cosmos.py`

**Description:** Manual edits were made by the developer to read `COSMOS-CONN-READ` and `COSMOS-CONN-WRITE` strings from `os.getenv` via a local `.env` instead of calling `get_secret` from the Azure Key Vault. This bypasses the need for the server to authenticate identity using Azure Identity.
