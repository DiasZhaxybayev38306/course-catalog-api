# course-catalog-api

Backend of the course catalog: FastAPI, SQLAlchemy 2.1, PostgreSQL, and Alembic
migrations (Labs 4–7 of "Advanced Web Technologies").

## How to run

You need Python 3.11 or newer and PostgreSQL 16 or newer.

Once, as the `postgres` superuser, create the role and the database:

```sql
CREATE ROLE catalog_app LOGIN PASSWORD 'change-me';
CREATE DATABASE course_catalog OWNER catalog_app;
```

Then, from the project folder:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env               # Windows PowerShell: Copy-Item .env.example .env
alembic upgrade head               # creates the tables (migrations 0001 and 0002)
psql -h localhost -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql
alembic check                      # "No new upgrade operations detected."
fastapi dev main.py
```

Checks (with the server running, in a second window): `python check_db.py`,
`python check_models.py`, `python try_errors.py` (must print `5 of 5 as expected`).

API documentation: http://localhost:8000/docs. The password `change-me` is for
teaching; in a real project, passwords are never put into the repository.

## What changed in the API

- The data now lives in PostgreSQL, not in Python lists. It survives a server restart
  (the likes stay where they were); the schema is managed by Alembic migrations.
- `POST /enrollments` now takes `studentId` instead of `studentName`: a student must first be
  created with `POST /students` and then enrolled. The enrollment form of the frontend from Lab 5
  still sends `studentName`, so it gets 422 until it is updated.
- New routes: `POST /students` (201) and `GET /stats/courses` (enrollments per course, zeros
  included). `GET /enrollments` now returns the course title and the student's name (a JOIN),
  next to the ids and `enrolledAt`.
- Courses have a required `level` field (`beginner`, `intermediate`, `advanced`), added by
  migration `0002`. `GET /courses?level=beginner` filters by it, together with `is_elective`,
  sorting and pages.
- Database constraint violations become API responses by the constraint name: 409 (email taken,
  already enrolled), 404 (unknown course or student), 422 from Pydantic (short name). An unknown
  violation stays a 500, because it means a bug in the code.

## Migrations

| Command | What it does |
|---------|--------------|
| `alembic upgrade head` | applies all the missing migrations |
| `alembic downgrade -1` | rolls back the last migration |
| `alembic current` | shows the version of the database |
| `alembic history` | shows the chain of migrations |
| `alembic revision --autogenerate -m "text"` | writes a draft from models vs. database |
| `alembic check` | reports whether the models and the database have diverged |
| `alembic upgrade 0001:0002 --sql` | prints the SQL of a migration without running it |
| `alembic stamp head` | marks the database as up to date without running migrations |

## Experiment log

All experiments were run on PostgreSQL 16.15, SQLAlchemy 2.1, Alembic 1.20.

| # | Experiment | What I saw | Cause | How I fixed it |
|---|------------|------------|-------|----------------|
| 1 | the `uq` template in `naming_convention` changed | `check_models.py`: names only in models `students_email_unique`, `enrollments_course_id_unique`; only in database `students_email_key`, `enrollments_course_id_student_id_key` | the template builds the constraint names; the new template gave names different from those PostgreSQL chose in Lab 6 (the second one even lost the `student_id` part because `column_0_name` was used instead of `column_0_N_name`) | restored `%(table_name)s_%(column_0_N_name)s_key`; the check printed `none` twice again |
| 2 | `min_length` removed from `StudentIn`, name `N` | `500 Internal Server Error`; the server log ends with `IntegrityError ... CheckViolation ... violates check constraint "students_name_check"`, `Failing row contains (5, N, n@example.com)` | the request passed Pydantic and reached the database; the `CHECK` stopped the bad row (the data is intact), but `students_name_check` is not in `CONSTRAINT_ERRORS`, so the code treated it as an unknown violation (a bug) and gave 500 | restored `Field(min_length=2)`; `try_errors.py` prints `5 of 5` again. The right 422 comes from Pydantic; the `CHECK` is the second line of defense |
| 3 | a typo in a constraint name in the dictionary (`students_email_uniq`) | duplicate email gives `500`; the log shows `UniqueViolation ... unique constraint "students_email_key"` | the response is found by exact name, the key `students_email_uniq` matches nothing, so the violation was re-raised as unknown | restored the key `students_email_key`; the real name is always visible in the server log |
| 4 | `title` without `NOT NULL` in the database, `alembic check` | `Detected NOT NULL on column 'courses.title'`, `FAILED: New upgrade operations detected: [... 'modify_nullable' ...]`; after `title TYPE varchar(100)`: `Detected type change from VARCHAR(length=100) to Text()`, `modify_type` | the database was edited by hand and no longer matches the models; `alembic check` compares models with the real database | `SET NOT NULL` and `TYPE text` in psql; `alembic check` printed `No new upgrade operations detected.` |
| 5 | automatic migration `0002` on existing data | `alembic upgrade head` failed: `NotNullViolation: column "level" of relation "courses" contains null values`, SQL `ALTER TABLE courses ADD COLUMN level TEXT NOT NULL`; `alembic current` stayed `0001` | autogenerate compares schemas, not data: it wrote a required column without a default, and the 6 existing rows have no value for it. The migration ran in a transaction, so it rolled back completely | rewrote `upgrade()` in three steps (add a nullable column, `UPDATE` with `CASE`, then `nullable=False`) and `downgrade()` with `drop_column`; `upgrade head` gave `0002 (head)` |
| 6 | `import models` commented out in `env.py` | autogenerate wrote `0003_oops.py` that drops all the tables: `Detected removed table 'students'`, `'enrollments'`, `'courses'`, and the index | without the import, the models are never loaded, `Base.metadata` is empty and Alembic thinks all the tables in the database are superfluous. Applying that file would destroy the data | did not run it; deleted `0003_oops.py`, put `import models` back; `alembic check` is clean. A `drop_table` in an ordinary migration is a reason to stop |
| 7 | a `phone` field in the model without a migration | `alembic check`: `Detected added column 'students.phone'`, `FAILED: New upgrade operations detected: [('add_column', None, 'students', ...)]` | the model changed but there is no migration, so the database lacks the column (a colleague's or the server's database would be out of date) | deleted the line from `models.py` (in real work: `alembic revision --autogenerate` and commit it together with the model); `alembic check` is clean |
| 8 | two migrations from one revision | `alembic heads` showed `0003 (head)` and `0004 (head)`; `alembic upgrade head` failed with `Multiple head revisions are present for given argument 'head'` | two branches were created from `0002`, so the history has two heads and Alembic can't pick one | `alembic merge heads -m "merge phone and language" --rev-id 0005` made one head `0005`; then deleted all three experimental files, and `alembic heads` shows only `0002 (head)` |

## Decisions

- The response is chosen by the constraint name, not by SQLSTATE: `23505` means "unique
  violated" for any `UNIQUE` (we have several), so the code alone can't say which rule was broken,
  and the message text depends on the server version and language. The constraint name is stable,
  because we set it in `naming_convention` and it matches the database. The error is caught after
  `commit()` rather than checked in advance with a `SELECT`, because between the check and the
  `INSERT` another request can take the same email; the check would be out of date, while the
  database constraint is always right. It is easier to try and handle the refusal.
- A like uses `UPDATE courses SET likes = likes + 1 ... RETURNING`: the database does the adding
  in one command and locks the row while it works. If the program read the number and wrote back
  `likes + 1`, two simultaneous requests would both read the same value and both write the same
  result, so one like would be lost (a lost update).
- Migration `0002` has three steps because a `NOT NULL` column can't be added to a table that
  already has rows (no value for them). So we add the column as nullable, fill the existing rows
  with a rule (elective courses `beginner`, the others `intermediate`), and only then forbid
  `NULL`. The whole migration runs in one transaction, so a failure at any step leaves the
  database at `0001`.

## Migration 0002 self-check

| What to check | Result |
|---------------|--------|
| Goal and steps | Yes. The goal is a required `level` column for courses; three steps (add nullable, fill, set `NOT NULL`) in one small migration that does nothing else. |
| Data | Yes. The six existing rows are filled by a rule before `NOT NULL` is set; checked in psql (2 `beginner`, 4 `intermediate`). |
| Renames and drops | Yes. It is a pure addition, nothing is renamed or dropped, so no data is lost on upgrade. |
| Rollback | Yes. `downgrade()` drops the column; tested with `downgrade -1` and `upgrade head`. It erases the levels, which is acceptable here because the rule restores them, but not if users had chosen them by hand. |
| Verification | Yes. The SQL was read with `alembic upgrade 0001:0002 --sql`; the cycle upgrade, downgrade, upgrade passed on the training database; `alembic check` is clean. |
| History | Yes. One head (`alembic heads` shows `0002`); the migration is committed together with the change to `models.py`, `schemas.py` and the code. |
| Application | Yes. `level` appears in every course response and `?level=` filters the list; `seed.sql` was updated and clears the tables itself. Clients must handle the new field. |
