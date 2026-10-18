# Plan: Spec 01 – Database Setup

## Context
Spec `.claude/specs/01-database-setup` (no `.md` extension) asks for a working SQLite data layer in `database/db.py` (`get_db`, `init_db`, `seed_db`) and startup calls in `app.py`. The code is already ahead of the spec: nearly everything is implemented. This plan covers the one real gap and verifies the rest against the spec's Definition of Done.

## Current state (verified)
- `database/db.py`: `get_db()` (sqlite3.Row, `PRAGMA foreign_keys = ON`, module-level `DB_PATH` read at call time), `init_db()` (both tables, `CREATE TABLE IF NOT EXISTS`, schema matches spec section 4), `seed_db()` (early return if users exist, hashed demo user, 8 expenses covering all 7 categories, parameterized SQL).
- `app.py`: line 17 imports `get_db, init_db, seed_db`; lines 42-44 run `init_db()` + `seed_db()` in `app.app_context()`.
- Tests monkeypatch `database.db.DB_PATH` and clear seed data themselves, so they don't depend on seed dates.

## Gap
Spec section 5C: "Dates spread across current month". `seed_db()` hardcodes `2026-04-01`..`2026-04-08`; today is 2026-10-18.

## Change (only `database/db.py`)
1. Add `from datetime import date` (stdlib, no new packages).
2. In `seed_db()`, compute `today = date.today()` and build each expense date as `today.replace(day=min(n, today.day)).isoformat()` using day offsets `[1, 2, 4, 6, 9, 12, 15, 18]`. This keeps dates in the current month, never in the future, always `YYYY-MM-DD`.
3. Keep the same 8 tuples (amounts, categories, descriptions), the early-return guard, hashing and `executemany`.

No change to `app.py` (the unused `get_db` import is required by spec section 6, so it stays). No schema changes, no new files, no new packages.

## Risks
- The existing root `spendly.db` is already seeded with April data, so `seed_db()` returns early on it. To see the change, the file must be deleted or renamed first. Do this only with user approval; otherwise verify against a temp DB by setting `database.db.DB_PATH`.
- Stray DBs (`database/spendly.db`, `spendly-backup.db`) are out of scope; leave untouched.

## Verification (map to Definition of Done)
Run against a temp DB (set `database.db.DB_PATH` to a temp path) unless the user approves removing `spendly.db`.
1. DB file created on startup: `init_db()` creates the file.
2. Schema: `PRAGMA table_info(users)`, `table_info(expenses)`, `foreign_key_list(expenses)` match spec section 4.
3. Demo user: `password_hash != "demo123"` and `check_password_hash(hash, "demo123")` is True.
4. Expenses: count = 8; distinct categories = exactly the 7 spec categories; all dates match `YYYY-MM-DD`, start with the current `YYYY-MM`, and are not after today.
5. Idempotency: call `init_db()` and `seed_db()` three times; still 1 user and 8 expenses.
6. App starts: `python -c "import app"` succeeds.
7. Constraints: expense with `user_id=9999` and a duplicate email each raise `sqlite3.IntegrityError`.
8. Parameterized SQL: grep `db.py` for f-string/`%`/`.format` in SQL; expect none.
9. Regression: `pytest` passes as before. Per CLAUDE.md, use a subagent to verify the test results.
