# Migrations (Alembic) — how repo push -> DB migration works

This project uses Alembic as the canonical migration mechanism. You already have a CodeBuild runner configured to run `backend/buildspec.yml` inside the VPC that has network access to the RDS instance. That CodeBuild job performs the actual database migration step.

What happens on push
- You push changes to the repository (e.g. `main`).
- Your CI (CodeBuild) is configured to run `backend/buildspec.yml` inside the VPC that can reach the RDS instance.
- The buildspec installs dependencies and runs:

```bash
alembic -c backend/alembic.ini upgrade head
```

- `backend/alembic/env.py` reads `DATABASE_URL` from the environment at runtime. CodeBuild MUST be configured with a `DATABASE_URL` environment variable pointing at the database (for example: `postgresql://user:pass@host:5432/dbname`).

What you must ensure in your CodeBuild project
- The CodeBuild project runs in the RDS VPC (subnets/security groups) so it can access the DB host and port.
- Set the environment variable `DATABASE_URL` in the CodeBuild project (plaintext env var is supported per your setup). Do NOT print it in build logs.
- The buildspec already runs `alembic -c backend/alembic.ini upgrade head` in the `pre_build` phase.

How to test locally (recommended before pushing)
- Export a local `DATABASE_URL` that points to a test DB (never the production DB):

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/tuitter_test"
alembic -c backend/alembic.ini upgrade head
```

- If you only want to print the SQL Alembic will run (dry-run), use offline mode:

```bash
DATABASE_URL="postgresql://..." alembic -c backend/alembic.ini upgrade head --sql
```

How to add new revisions
- Create a new revision (manual message):

```bash
alembic -c backend/alembic.ini revision -m "describe change" --autogenerate
```

- Notes on autogenerate: `env.py` currently does not import `models` automatically to avoid side-effects. If you want autogenerate to work in your environment, ensure the Python import path used by Alembic includes the `backend` package (e.g., run with `PYTHONPATH=.`) or update `backend/alembic/env.py` to import `Base` from `backend.models` and set `target_metadata = models.Base.metadata`. I left `env.py` conservative to reduce surprise imports in CI.

Rollback and safety
- Always snapshot or backup RDS before applying risky migrations. CodeBuild `pre_build` can optionally call `aws rds create-db-snapshot` (commented in `backend/buildspec.yml`).
- Use reversible migrations (include `downgrade()` in your Alembic revisions) where feasible.

Quick checklist before pushing to `main`
- [ ] Code committed and tests passing locally.
- [ ] `alembic` revision(s) added under `backend/alembic/versions/`.
- [ ] CodeBuild project has `DATABASE_URL` env var and is running in the DB VPC.
- [ ] Optional snapshot step enabled if you want a pre-migration backup.

If you'd like, I can:
- Add `target_metadata = models.Base.metadata` to `backend/alembic/env.py` and adjust `backend` imports to make `alembic revision --autogenerate` work in CI.
- Create the next Alembic revision (for example, adding `title` and `is_group` to `conversations`) and commit it so pushing to `main` will apply it automatically in CI.

---
Small, safe note: pushing to `main` will only change the database if the CodeBuild job is configured and receives the push/promotion event and if `DATABASE_URL` is set. I did not change CI outside the repo.
