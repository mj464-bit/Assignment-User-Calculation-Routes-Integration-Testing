# User & Calculation Routes + Integration Testing

A FastAPI backend with JWT-authenticated user registration/login and full
BREAD (Browse, Read, Edit, Add, Delete) endpoints for calculations. Built for
IS601 Module 12.

**Docker Hub:** https://hub.docker.com/r/mj464/assignment-user-calculation-routes-integration-testing

## Tech stack

- FastAPI + Pydantic v2 (request/response validation)
- SQLAlchemy 2.0 + PostgreSQL
- JWT auth (`python-jose`) with bcrypt password hashing (`passlib`)
- pytest for integration tests
- Docker + Docker Compose for local dev
- GitHub Actions for CI/CD (test → build → push to Docker Hub)

## Project structure
app/
 main.py # FastAPI app, router registration
 database.py # SQLAlchemy engine/session setup
 database_init.py # create_all/drop_all helpers
core/config.py # environment-driven settings
models/ # SQLAlchemy models (User, Calculation + subclasses)
schemas/ # Pydantic request/response schemas
auth/jwt.py # password hashing, JWT create/verify, current-user dependency
routers/
 users.py # POST /users/register, POST /users/login
 calculations.py # BREAD for /calculations
tests/
  integration/ # pytest suite (35 tests) against a real Postgres DB

## Running locally with Docker (recommended)

Requires Docker Desktop.

```bash
docker compose up --build
```

This starts:
- **web** — the FastAPI app at http://localhost:8000
- **db** — a Postgres 17 instance (data persisted in a Docker volume)

Once it's up, open **http://localhost:8000/docs** for the interactive Swagger UI.

### Trying it out in Swagger

1. Expand `POST /users/register`, "Try it out", fill in the example fields
   (password must contain an uppercase letter, a lowercase letter, and a digit),
   Execute — expect `201`.
2. Expand `POST /users/login`, use the same username/password, Execute — copy
   the `access_token` from the response body.
3. Click the green **Authorize** button (top right), paste the raw token
   (no `Bearer ` prefix — Swagger adds that), click Authorize.
4. Now `POST /calculations`, `GET /calculations`, `GET /calculations/{id}`,
   `PUT /calculations/{id}`, and `DELETE /calculations/{id}` will all include
   your token automatically.

## Running locally without Docker

Requires Python 3.10+ and a running Postgres instance.

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt

cp .env.example .env            # then edit DATABASE_URL etc. as needed
uvicorn app.main:app --reload
```

## Running the integration tests

**With Docker** (the container already has Postgres available):

```bash
docker compose up -d --build
docker compose exec web pytest tests/integration/ -v
```

**Without Docker**, point `DATABASE_URL` at any Postgres instance you have
running and run pytest directly:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db pytest tests/integration/ -v
```

The suite (35 tests) covers:
- **Users**: registration success/validation (duplicate username/email, weak
  password, mismatched confirm_password, invalid email, missing fields),
  persistence to the database, login by username or email, wrong password,
  nonexistent user, and that a valid token unlocks protected routes while a
  missing one is blocked.
- **Calculations**: create for all four operation types, division-by-zero and
  invalid-type rejection, that an authenticated request is required, that a
  client-supplied `user_id` is ignored in favor of the token's user, browse
  (including that one user never sees another user's calculations), read
  (including 404 for missing/other-user calculations and 422 for a malformed
  UUID), edit (recomputes the result, 404 for missing, validation for too few
  inputs), and delete (204, then a 404 on subsequent read).

## API endpoints

| Method | Path | Auth required | Description |
|---|---|---|---|
| GET | `/health` | No | Health check |
| POST | `/users/register` | No | Register a new user |
| POST | `/users/login` | No | Log in, returns a JWT access token |
| POST | `/calculations` | Yes | Create a calculation (Add) |
| GET | `/calculations` | Yes | List your calculations (Browse) |
| GET | `/calculations/{id}` | Yes | Get one calculation (Read) |
| PUT | `/calculations/{id}` | Yes | Update a calculation's inputs (Edit) |
| DELETE | `/calculations/{id}` | Yes | Delete a calculation (Delete) |

Calculations are always scoped to the authenticated user — you can't list,
read, edit, or delete another user's calculations, and the `user_id` on
create always comes from your token, never from the request body.

## CI/CD

`.github/workflows/ci.yml` runs on every push/PR to `main`:

1. **test** — spins up a Postgres service container, installs dependencies,
   runs the full integration test suite.
2. **deploy** — only runs on a push to `main`, and only if `test` passes;
   builds the Docker image and pushes it to Docker Hub tagged `latest` and
   with the commit SHA.

Required GitHub repo secrets (Settings → Secrets and variables → Actions):
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN` (a Docker Hub access token, not your account password)

## Pulling the published image

```bash
## docker pull mj464/assignment-user-calculation-routes-integration-testing:latest
```