# Cupcakes (Flask)

Server-rendered Flask web app with PostgreSQL, Alembic migrations (Flask-Migrate), Keycloak login and Tailwind CSS, run together with Docker Compose.

## Run

```sh
./start.sh        # macOS/Linux/Git Bash
.\start.ps1       # Windows PowerShell
```

Both scripts run `docker compose up -d --build` from the project folder. Stop everything with `docker compose down`.

If PowerShell refuses to run the script because of the execution policy, run it like this:

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

| Service  | URL                    | Notes                                             |
|----------|------------------------|---------------------------------------------------|
| Web      | http://localhost:5000  | Flask app; runs `flask db upgrade` on start       |
| Keycloak | http://localhost:8080  | Admin console: `admin` / `admin`                  |
| Postgres | `localhost:5432`       | `cupcakes` / `cupcakes`, database `cupcakes`      |

Sample users in the `cupcakes` realm (see `keycloak/realm-cupcakes.json`):

| Username | Password       | Has profile in DB                      |
|----------|----------------|----------------------------------------|
| `user1`  | `sOhM^8s19eMp` | yes                                    |
| `user2`  | `R4hoc6C_oth2` | yes                                    |
| `user3`  | `5BRN7UC9Zs7@` | no (shows the "no profile found" page) |

The realm is imported only on Keycloak's first start. After changing the realm file, reset it with `docker compose down -v` (this also wipes the database).

## How login works

1. `/auth/login` redirects the browser to Keycloak (authorization code flow with PKCE, confidential client `cupcakes-web`).
2. Keycloak redirects back to `/auth/callback`. The app exchanges the code for tokens over the Docker network (`http://keycloak:8080`) and validates the ID token.
3. The Keycloak identity (username, email) is kept in the Flask session, and the user is sent to `/profile`.
4. `/profile` finds the `User` row whose `email` matches the Keycloak email (case-insensitive). Only verified emails are accepted.

## Pages

- `/` – welcome page (redirects to the profile when logged in)
- `/profile` – profile details of the logged-in user
- `/auth/login`, `/auth/callback`, `/auth/logout`

## Project layout

- `app/models` – SQLAlchemy models (`User` with UUID `id`, `name`, `surname`, `email`)
- `app/web` – blueprints (`auth`, `profile`)
- `app/auth.py` – Keycloak client registration and `login_required`
- `app/templates` – Jinja templates styled with Tailwind
- `app/static/src/input.css` – Tailwind entry; compiled to `app/static/css/app.css` in the Docker build
- `migrations` – Alembic (Flask-Migrate)
- `keycloak` – realm imported on Keycloak's first start

## Alembic migrations

Migrations run automatically when the web container starts. To create a new one after changing models:

```sh
flask --app run db migrate -m "describe the change"
flask --app run db upgrade
```

Review the generated file in `migrations/versions` before committing it.

## Local development and debugging (Flask outside Docker)

Run PostgreSQL and Keycloak in Docker, and Flask itself on your machine so you can use the debugger.

```sh
.\setup-venv.ps1                # once; macOS/Linux/Git Bash: ./setup-venv.sh
.venv\Scripts\Activate.ps1      # macOS/Linux: source .venv/bin/activate

.\start-deps.ps1                # macOS/Linux/Git Bash: ./start-deps.sh
flask --app run db upgrade      # first time and after pulling new migrations
flask --app run run --debug     # http://localhost:5000
```

`start-deps` does the following:

1. stops the `web` container if it is running (it would occupy port 5000),
2. starts `db` and `keycloak`,
3. builds the Tailwind CSS into `app/static/css/app.css` with a Node container (`docker compose run --rm css`), so Node.js is not needed locally,
4. waits until Keycloak is ready.

Run it again (or just `docker compose run --rm css`) after adding new Tailwind classes to templates.

Defaults in `config.py` point to Postgres and Keycloak on `localhost`, so no extra environment variables are needed.

### Debugging in VS Code

Select the `.venv` interpreter (*Python: Select Interpreter*), then press **F5** and pick **Flask (debug)**. It runs `start-deps` first (VS Code task *Start dependencies*) and then starts Flask under the debugger, so breakpoints work in Python code and Jinja templates. Use **Flask (debug, skip dependencies)** when the containers are already running.

### Python virtual environment

`setup-venv.ps1` / `setup-venv.sh` create `.venv` (if it does not exist yet) and install `requirements.txt` into it. When finished, the script prints:

```text
Done. Activate the environment with:
  .\.venv\Scripts\Activate.ps1
```

A script cannot activate the environment in your terminal, so run the printed command yourself:

```sh
.\.venv\Scripts\Activate.ps1    # Windows PowerShell
source .venv/Scripts/activate   # Git Bash on Windows
source .venv/bin/activate       # macOS/Linux
```

The prompt then starts with `(.venv)`. Run `deactivate` to leave the environment. If PowerShell blocks `Activate.ps1` because of the execution policy, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
