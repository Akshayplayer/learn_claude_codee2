# Spec: Registration

## Overview

Registration lets a visitor create a Spendly account with a name, email and password, so they can sign in and track their own expenses. It is the entry point to every logged-in feature, which is why it sits right after the database setup in step 1. The core flow already exists (`register()` in `app.py`, `create_user()` in `database/db.py`, `templates/register.html`). This spec defines the complete expected behaviour and closes the gaps in the current implementation: validation errors are never shown on the register page, the password length promised by the form is not enforced, and typed values are lost after an error.

## Depends on

- Step 1 — Database setup (`users` table, `get_db()`, `init_db()`, `create_user()`, `get_user_by_email()`)

## Routes

- `GET /register` — render the registration form; redirect to `/profile` if already logged in — public
- `POST /register` — validate the form, create the user, redirect to `/login` with a success flash; re-render the form with an error flash and the typed values on failure — public

No other new routes.

## Database changes

No database changes. The existing `users` table already has everything needed (`name`, `email UNIQUE NOT NULL`, `password_hash`, `created_at`). Duplicate emails are rejected by the `UNIQUE` constraint, which `register()` catches as `sqlite3.IntegrityError`.

## Templates

- **Create:** none
- **Modify:**
  - `templates/register.html`
    - Remove the empty `{% block flash %}{% endblock %}` override so flash messages from `base.html` render on this page.
    - Repopulate `name` and `email` from a `form` variable after a failed submit (never repopulate the password fields).
    - Add `minlength="8"` to both password inputs to match the "Min. 8 characters" placeholder.

## Files to change

- `app.py` — in `register()`: normalise email (strip and lowercase), reject passwords shorter than 8 characters, reject an email without `@`, and pass `form=request.form` to `render_template` on every error path.
- `templates/register.html` — as described above.

## Files to create

- `tests/test_registration.py` — pytest-flask tests for the register route (see Definition of done).

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (`generate_password_hash`), never stored or logged in plain text
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic stays in `database/db.py`; the route only validates input, calls `create_user()` and renders or redirects
- Use `url_for()` for every link and redirect — no hardcoded URLs
- Do not change the port (5001) and do not touch the stub routes
- Validation errors use `flash(message, "error")`; success uses `flash(message, "success")`
- Re-render the form with status 200 on validation errors (no `abort()` for user input mistakes)
- Never repopulate password fields in the re-rendered form

## Definition of done

- [ ] `GET /register` shows the form with name, email, password and confirm password fields
- [ ] A logged-in user who visits `/register` is redirected to `/profile`
- [ ] Submitting with any field empty shows "All fields are required." on the register page
- [ ] Submitting a password shorter than 8 characters shows an error on the register page and creates no user
- [ ] Submitting mismatched passwords shows "Passwords do not match." and creates no user
- [ ] Submitting an email already in `users` (including a different letter case, e.g. `Demo@Spendly.com`) shows "Email already registered." and creates no second row
- [ ] After any failed submit, the name and email fields keep what was typed and the password fields are empty
- [ ] A valid submission creates exactly one new row in `users` with `password_hash` set (not the plain password) and redirects to `/login` showing "Account created! Please sign in."
- [ ] The new user can sign in at `/login` with the password they registered with
- [ ] The email is stored lowercase and trimmed
- [ ] `pytest tests/test_registration.py` passes
- [ ] The app starts on port 5001 without errors
