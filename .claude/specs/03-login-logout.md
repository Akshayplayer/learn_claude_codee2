# Spec: Login and Logout

## Overview

Login and logout let a registered visitor sign in to Spendly with email and password, and sign out again. They sit right after registration (step 2) because a user created there has no way to reach `/profile`, the expense pages or analytics without a session. The core flow already exists (`login()` and `logout()` in `app.py`, `get_user_by_email()` in `database/db.py`, `templates/login.html`, the session-aware navbar in `base.html`). This spec defines the complete expected behaviour and closes the gaps in the current implementation: the login page never shows its error flash (the same empty `{% block flash %}` override that hid errors on the register page), the typed email is lost after a failed attempt, email matching is case-sensitive, and the session is not reset on sign-in.

## Depends on

- Step 1 — Database setup (`users` table, `get_db()`, `get_user_by_email()`)
- Step 2 — Registration (creates the users that sign in; redirects to `/login` with a success flash)

## Routes

- `GET /login` — render the sign-in form; redirect to `/profile` if already logged in — public
- `POST /login` — validate credentials, start the session and redirect to `/profile`; re-render the form with an error flash and the typed email on failure — public
- `GET /logout` — clear the session, flash "You have been logged out." and redirect to `/` — public (harmless if not logged in)

No other new routes. All three already exist in `app.py`; this step finishes and hardens them. `CLAUDE.md` still lists `/logout` as a stub for Step 3 — update that row to Implemented once this step is done.

## Database changes

No database changes. The existing `users` table already has everything needed (`id`, `name`, `email`, `password_hash`). Only the query in `get_user_by_email()` changes (see Files to change).

## Templates

- **Create:** none
- **Modify:**
  - `templates/login.html`
    - Remove the empty `{% block flash %}{% endblock %}` override so flash messages from `base.html` render on this page (this is what currently hides "Invalid email or password." and the "Account created! Please sign in." message from registration).
    - Repopulate `email` from a `form` variable after a failed submit (never repopulate the password field).

## Files to change

- `app.py` — in `login()`:
  - Normalise the email (strip and lowercase) before the lookup.
  - Return the same generic "Invalid email or password." for an unknown email and for a wrong password (do not reveal which one failed).
  - Reject an empty email or password with "All fields are required." before touching the database.
  - Call `session.clear()` before setting `user_id` and `user_name`, so no stale session data survives a sign-in.
  - Pass `form=request.form` to `render_template` on every error path.
  - Leave `logout()` as is: `session.clear()`, success flash, redirect to `landing`.
- `database/db.py` — `get_user_by_email()`: match case-insensitively with `WHERE LOWER(email) = LOWER(?)` (still parameterised), so accounts stored with mixed-case emails before the registration step normalised them can still sign in.
- `templates/login.html` — as described above.
- `CLAUDE.md` — update the routes table: `GET /logout` and `GET /profile` status.

## Files to create

- `tests/test_login_logout.py` — pytest tests for the login and logout routes (see Definition of done).

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug; verify with `check_password_hash`, never compare or log plain-text passwords
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic stays in `database/db.py`; the route only validates input, calls `get_user_by_email()` and renders or redirects
- Use `url_for()` for every link and redirect — no hardcoded URLs
- Do not change the port (5001) and do not touch the stub routes
- Validation errors use `flash(message, "error")`; success uses `flash(message, "success")`
- Re-render the form with status 200 on failed sign-in (no `abort()` for user input mistakes)
- Never repopulate the password field in the re-rendered form
- The error message must be identical for "no such email" and "wrong password"

## Definition of done

- [ ] `GET /login` shows the form with email and password fields
- [ ] A logged-in user who visits `/login` is redirected to `/profile`
- [ ] Submitting a wrong password shows "Invalid email or password." on the login page and does not start a session
- [ ] Submitting an unknown email shows the exact same "Invalid email or password." message
- [ ] Submitting with an empty field shows "All fields are required." on the login page
- [ ] After a failed submit, the email field keeps what was typed and the password field is empty
- [ ] Signing in as `demo@spendly.com` / `demo123` redirects to `/profile` and the navbar shows Analytics, Dashboard and Sign out instead of Sign in and Get started
- [ ] Signing in works with the email in a different letter case or with surrounding spaces, e.g. ` Demo@Spendly.com `
- [ ] A user who has just registered sees "Account created! Please sign in." on `/login` and can sign in with that password
- [ ] Clicking Sign out clears the session, redirects to `/` and shows "You have been logged out."
- [ ] After signing out, visiting `/profile` redirects to `/login`
- [ ] Visiting `/logout` while not logged in redirects to `/` without an error
- [ ] `pytest tests/test_login_logout.py` passes
- [ ] The app starts on port 5001 without errors
