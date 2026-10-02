# Docker Setup — AccessSlot

Local development and testing using Docker and Docker Compose.

---

## 1. Requirements

| Tool | Minimum Version | Check |
|---|---|---|
| Docker Desktop | 4.x | `docker --version` |
| Docker Compose | V2 (built into Docker Desktop) | `docker compose version` |
| Git | Any recent version | `git --version` |

**Windows users:** Docker Desktop requires WSL 2. It installs and configures this automatically.

---

## 2. Verify Docker is Working

After installing and starting Docker Desktop, open a terminal and run:

```powershell
docker --version
docker compose version
docker run hello-world
```

Expected output from `hello-world`:
```
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

If you see `cannot connect to the Docker daemon`, Docker Desktop is not running. Open it from the Start menu and wait for the whale icon in the system tray to become steady.

---

## 3. Environment Variable Setup

The backend requires a `.env` file for Docker Compose. The frontend API URL is baked in at build time.

### Backend `.env`

```powershell
# From the repo root:
Copy-Item backend\.env.example backend\.env
```

Then edit `backend/.env` and set at minimum:

```env
SECRET_KEY=<generate a random string>
DB_PASSWORD=<any local password>
```

To generate a secure `SECRET_KEY`:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

**Never commit `backend/.env` to Git.** It is gitignored by default.

### Frontend API URL

The frontend reads `VITE_API_BASE_URL` at **build time**. For local Docker testing the default (`http://localhost:8000/api`) is already set in `docker-compose.yml`. You do not need a `frontend/.env` for Docker Compose.

---

## 4. Docker Build Commands

Build images individually (without running them):

```powershell
# From the repo root:

# Build backend image
docker build -t accessslot-backend:latest ./backend

# Build frontend image (with local API URL baked in)
docker build -t accessslot-frontend:latest ./frontend

# Build frontend image for production (with real API URL)
docker build `
  --build-arg VITE_API_BASE_URL=https://accessslot-backend.onrender.com/api `
  -t accessslot-frontend:prod `
  ./frontend
```

---

## 5. Docker Compose Commands

Docker Compose runs the full stack: database + backend + frontend together.

```powershell
# From the repo root:

# Start everything (builds images if not already built)
docker compose --env-file backend/.env up --build

# Start in background (detached mode)
docker compose --env-file backend/.env up --build -d

# View logs (all services)
docker compose logs -f

# View logs for one service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db

# Stop all containers (keeps volumes)
docker compose --env-file backend/.env down

# Stop and remove volumes (wipes local database)
docker compose --env-file backend/.env down -v

# Rebuild a single service
docker compose --env-file backend/.env up --build backend

# Run a one-off command inside the backend container
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py shell
```

---

## 6. Accessing the Application

Once `docker compose up` is running:

| Service | URL |
|---|---|
| Frontend (React app) | http://localhost:3000 |
| Backend API | http://localhost:8000/api/ |
| Backend health check | http://localhost:8000/api/health/ |
| Django admin | http://localhost:8000/admin/ |
| PostgreSQL | localhost:5432 |

---

## 7. Image Sizes

| Image | Base | Approximate Size |
|---|---|---|
| `accessslot-backend` | python:3.11-slim | ~600 MB |
| `accessslot-frontend` | nginx:alpine | ~95 MB |

The backend is larger due to psycopg2 requiring gcc and libpq at build time. The final image does not contain gcc — it is only used during the `pip install` step.

---

## 8. Troubleshooting

### Docker daemon not running

**Symptom:** `error during connect: ... The system cannot find the file specified`

**Fix:** Open Docker Desktop from the Start menu. Wait for the whale icon to become steady (not animated). This can take 1–3 minutes on first start.

---

### Port already in use

**Symptom:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Fix:** Something else is using that port. Either stop it, or change the port mapping in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"   # maps host 8001 → container 8000
```

---

### Database connection refused

**Symptom:** Backend container exits with `connection refused` or `could not connect to server`

**Cause:** Backend started before the database was ready.

**Fix:** Docker Compose has a `depends_on: db: condition: service_healthy` — the db container has a healthcheck. If it keeps failing:
```powershell
docker compose logs db
```
Check that `DB_USER` and `DB_NAME` in `backend/.env` match what is set in `docker-compose.yml`.

---

### Migration errors on startup

**Symptom:** `django.db.utils.ProgrammingError: relation does not exist`

**Fix:** Run migrations manually:
```powershell
docker compose exec backend python manage.py migrate
```

---

### Frontend shows blank page or 404

**Symptom:** `http://localhost:3000` loads but the app is blank.

**Cause:** `VITE_API_BASE_URL` was not set correctly at build time, or the backend container is not running.

**Check:**
```powershell
# Is the backend healthy?
docker compose ps

# Check what API URL is baked into the frontend image
docker compose exec frontend cat /usr/share/nginx/html/index.html
```

**Fix:** Rebuild with the correct URL:
```powershell
docker compose --env-file backend/.env up --build frontend
```

---

### Cannot reach backend from browser (CORS error)

**Symptom:** Browser console shows `Access to XMLHttpRequest blocked by CORS policy`

**Cause:** `CORS_ALLOWED_ORIGINS` in `backend/.env` does not include the origin the browser is using.

**Fix:** Add the frontend origin to `backend/.env`:
```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```
Then restart the backend container:
```powershell
docker compose --env-file backend/.env up -d backend
```

---

### SECRET_KEY error at startup

**Symptom:** `KeyError: 'SECRET_KEY'` or `UndefinedValueError`

**Cause:** `backend/.env` is missing or `SECRET_KEY` is not set.

**Fix:** Make sure `backend/.env` exists and contains a `SECRET_KEY` value. See section 3 above.

---

## 9. Common Docker Commands Reference

```powershell
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# List images
docker images

# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove everything (containers, images, volumes, networks)
# WARNING: This wipes all local Docker data
docker system prune -a --volumes

# Inspect a container's environment variables
docker inspect accessslot_backend | Select-String "Env" -Context 0,20

# Copy a file out of a container
docker cp accessslot_backend:/app/staticfiles ./local-staticfiles
```
