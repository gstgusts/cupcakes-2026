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

| Username | Password       | Roles           | Has profile in DB                      |
|----------|----------------|-----------------|----------------------------------------|
| `user1`  | `sOhM^8s19eMp` | `admin`, `user` | yes                                    |
| `user2`  | `R4hoc6C_oth2` | `user`          | yes                                    |
| `user3`  | `5BRN7UC9Zs7@` | `user`          | no (shows the "no profile found" page) |

Realm roles are `admin` and `user`. Every new user gets `user` automatically (realm default role). The roles are included in the ID token as the `roles` claim.

The realm is imported only on Keycloak's first start. After changing the realm file, reset it with `docker compose down -v` (this also wipes the database).

## How login works

1. `/auth/login` redirects the browser to Keycloak (authorization code flow with PKCE, confidential client `cupcakes-web`).
2. Keycloak redirects back to `/auth/callback`. The app exchanges the code for tokens over the Docker network (`http://keycloak:8080`) and validates the ID token.
3. The Keycloak identity (username, email) is kept in the Flask session, and the user is sent to `/profile`.
4. `/profile` finds the `User` row whose `email` matches the Keycloak email (case-insensitive). Only verified emails are accepted.

## Pages

- `/` – welcome page (redirects to the profile when logged in)
- `/cupcakes` – cupcake list with search and type filter (any logged-in user)
- `/profile` – profile details of the logged-in user
- `/users` – user list with search (`admin` role only)
- `/users/new` – add a user (`admin` role only)
- `/auth/login`, `/auth/callback`, `/auth/logout`

## Adding users (Keycloak Admin API)

There is no self-registration: an admin adds users on `/users/new`.

1. The form is validated (required fields, lengths, email format).
2. The email must not exist yet, neither as a user profile in our database nor as a Keycloak account.
3. The app creates the Keycloak user through the Keycloak Admin REST API (`app/keycloak_admin.py`) with a generated temporary password, then saves the user profile. If saving the profile fails, the Keycloak user is deleted again.
4. The temporary password is shown once to the admin. Keycloak asks the new user to set their own password at first sign-in.

The app calls the Admin API as the service account of the `cupcakes-web` client (client credentials grant). In `keycloak/realm-cupcakes.json` the service account has only the `realm-management` roles `manage-users` and `view-users`.

## Project layout

- `app/models` – SQLAlchemy models with UUID ids: `User`, `CupcakeType`, `Cupcake`. Tables are plural snake_case; constraint names follow PostgreSQL defaults (`<table>_pkey`, `<table>_<column>_key`, `<table>_<column>_fkey`, `<table>_<column>_idx`)
- `app/web` – blueprints (`auth`, `cupcake`, `profile`, `user`)
- `app/keycloak_admin.py` – Keycloak Admin REST API client (find, create, delete users)
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

`setup-venv.ps1` / `setup-venv.sh` create `.venv` (if it does not exist yet) and install `requirements-dev.txt` (the app requirements plus pytest) into it. When finished, the script prints:

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

## Tests

Tests use pytest and need only PostgreSQL (Keycloak is not used: tests log in by writing the identity into the session, and the Keycloak Admin API calls are replaced with fakes).

```sh
docker compose up -d db
pytest
```

`setup-venv.sh` / `setup-venv.ps1` install pytest from `requirements-dev.txt`. The tests use their own database `cupcakes_test` (created automatically and rebuilt from the migrations on every run), so your data in `cupcakes` is not touched. Use a different server with `TEST_DATABASE_URL`.

- `tests/test_validation.py` – form validation and temporary password rules
- `tests/test_cupcakes.py` – cupcake list, search and type filter
- `tests/test_pages.py` – pages through the Flask test client: login redirects, profile, admin-only user list and user creation

GitHub Actions (`.github/workflows/build.yml`) runs the tests on every push and pull request, then builds the Docker image, smoke-tests it and pushes it to `ghcr.io` (on `main` only).

## Deployment (example: Azure VM)

The `deploy` job in `.github/workflows/build.yml` shows how the app can be deployed automatically after every push to `main`:

```text
test → build image, push to ghcr.io → deploy: SSH to the VM, docker compose pull, docker compose up -d
```

It is switched off, because no VM exists yet: the job is skipped unless the repository variable `DEPLOY_ENABLED` is `true`. The URL `cupcakes-demo.westeurope.cloudapp.azure.com` used in the files is a placeholder.

Files in `deploy/` (copied to `~/cupcakes` on the VM by the deploy job):

- `docker-compose.yml` – the production stack: the app image from `ghcr.io` (no build on the VM), PostgreSQL, Keycloak in production mode with its own PostgreSQL, and Caddy as the HTTPS reverse proxy
- `Caddyfile` – gets an HTTPS certificate automatically and routes `/idp/*` to Keycloak and everything else to the app
- `.env.example` – domain and passwords; copied once by hand to `~/cupcakes/.env` on the VM (never committed)

Only Caddy is exposed (ports 80 and 443). The app talks to Keycloak and the databases over the Docker network.

To switch it on:

1. Create an Ubuntu VM (Azure B2s, 4 GB RAM, is enough with Keycloak), set a DNS name label on its public IP, and allow ports 22, 80 and 443 in the network security group.
2. Install Docker on the VM and create `~/cupcakes/.env` from `deploy/.env.example` with real passwords.
3. Replace the placeholder URL in `.github/workflows/build.yml` and in the `redirectUris` of `keycloak/realm-cupcakes.json` with the VM's DNS name.
4. Create an SSH key pair for deployments. Add the public key to `~/.ssh/authorized_keys` on the VM.
5. In GitHub: *Settings > Secrets and variables > Actions*, add secrets `VM_HOST` (DNS name), `VM_USER` and `VM_SSH_KEY` (the private key), and the variable `DEPLOY_ENABLED` = `true`.

After the first deployment, change the `cupcakes-web` client secret in the Keycloak admin console (`https://<domain>/idp/admin`) and put the new value into `.env`. The realm file contains the dev secret and the sample users with known passwords, which should be removed for real use.
