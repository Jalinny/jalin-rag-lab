# Frontend Changes

## Login Feature

### What was added

A frontend-only login gate was added to `frontend/src/App.tsx`. The app now shows a login screen before the main chat interface, matching the existing warm beige/yellow/black design system.

### Changes in `frontend/src/App.tsx`

1. **Import update** — Added `type FormEvent` to the React import.

2. **`CREDENTIALS` constant** — Hardcoded username/password for this personal demo:
   ```ts
   const CREDENTIALS = { username: "jalin", password: "raglab2024" };
   ```

3. **Login CSS** — Added the following CSS classes to the `STYLES` constant:
   - `.login-screen` — full-viewport overlay centered on screen
   - `.login-card` — bordered card with neo-brutalist shadow (matches app aesthetic)
   - `.login-title` / `.login-subtitle` — headline with yellow `<mark>` highlight
   - `.login-label` / `.login-input` — styled form fields
   - `.login-btn` — black submit button with press animation
   - `.login-error` — red error text for bad credentials
   - `.btn-logout` — muted outline button shown in the header

4. **`LoginScreen` component** — New component rendered when unauthenticated:
   - Username and password fields
   - On success: writes `rl_auth=1` to `localStorage`, calls `onLogin()`
   - On failure: shows "Invalid username or password." inline error

5. **`authed` state in `App`** — Initialized from `localStorage.getItem("rl_auth") === "1"` so sessions persist across page refreshes.

6. **`logout` function in `App`** — Removes `rl_auth` from `localStorage`, sets `authed` to `false`, and resets the chat state.

7. **Conditional render** — When `!authed`, renders only the `LoginScreen`. Once authenticated, renders the full chat UI.

8. **"Sign out" button in header** — Added a `<button className="btn-logout">` next to the status indicator. Clicking it calls `logout()`.

### Credentials

| Field    | Value        |
|----------|-------------|
| Username | `jalin`     |
| Password | `raglab2024` |
