# AccessSlot Deployment to Render

This guide walks through deploying AccessSlot to Render using the included `render.yaml` blueprint.

## Prerequisites

- ✅ GitHub repository: `Hima6-bindu/accessslot`
- ✅ Render account (free tier available)
- ✅ `render.yaml` blueprint file (included in repository root)

## Deployment Architecture

The `render.yaml` blueprint automatically configures:

1. **PostgreSQL Database** (`accessslot-db`)
   - Free tier (90 days)
   - Region: Oregon
   - Database name: `accessslot_db`
   - User: `accessslot_user`

2. **Backend Web Service** (`accessslot-backend`)
   - Django REST Framework API
   - Python 3.11.9
   - Gunicorn WSGI server
   - Automatic migrations on deploy
   - Static files collected automatically
   - PostgreSQL connection auto-configured

3. **Frontend Static Site** (`accessslot-frontend`)
   - React + Vite
   - Node.js 20
   - SPA routing configured
   - API URL auto-configurable

## Automated Configuration

The `render.yaml` blueprint handles:

✅ **Database Setup:**
- Creates PostgreSQL database
- Auto-generates secure credentials
- Configures connection parameters

✅ **Backend Configuration:**
- Sets Python version (3.11.9)
- Installs dependencies (`pip install -r requirements.txt`)
- Collects static files (`collectstatic --noinput`)
- Runs migrations (`migrate --noinput`)
- Starts Gunicorn with correct port binding
- Auto-configures database connection (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
- Auto-sets ALLOWED_HOSTS from service URL
- Generates secure SECRET_KEY automatically
- Sets DEBUG=False for production
- Configures JWT token lifetimes
- Disables SSL redirect (Render handles HTTPS)

✅ **Frontend Configuration:**
- Sets Node version (20)
- Installs dependencies (`npm ci`)
- Builds production bundle (`npm run build`)
- Configures SPA routing (/* → /index.html)

## Deployment Steps

### Step 1: Create Render Account

1. Go to https://render.com
2. Sign up (free tier available)
3. Connect your GitHub account

### Step 2: Deploy from Blueprint

1. **In Render Dashboard**, click **"New"** → **"Blueprint"**

2. **Connect Repository:**
   - Select: `Hima6-bindu/accessslot`
   - Render will detect `render.yaml` automatically

3. **Review Blueprint:**
   - Render shows all services to be created:
     - ✅ PostgreSQL Database
     - ✅ Backend Web Service
     - ✅ Frontend Static Site
   
4. **Click "Apply"**
   - Render will:
     - Create PostgreSQL database
     - Deploy backend (build + migrate)
     - Deploy frontend (build)

### Step 3: Wait for Initial Build

**Backend build** (~3-5 minutes):
- Installing Python dependencies
- Collecting static files
- Running migrations
- Starting Gunicorn

**Frontend build** (~2-3 minutes):
- Installing npm dependencies
- Building production bundle
- Deploying static files

### Step 4: Configure CORS (One Manual Step Required)

After backend is deployed, you'll see its URL (e.g., `https://accessslot-backend-xxxx.onrender.com`)

1. **In Render Dashboard**, go to `accessslot-backend` service
2. **Navigate to "Environment"** tab
3. **Find `CORS_ALLOWED_ORIGINS`** variable
4. **Set value to:**
   ```
   https://accessslot-frontend-xxxx.onrender.com
   ```
   (Use your actual frontend URL from Render)

5. **Save** - Backend will auto-redeploy (takes ~1 minute)

### Step 5: Configure Frontend API URL (One Manual Step Required)

After backend is deployed:

1. **In Render Dashboard**, go to `accessslot-frontend` service
2. **Navigate to "Environment"** tab
3. **Add `VITE_API_BASE_URL`** variable:
   ```
   https://accessslot-backend-xxxx.onrender.com/api
   ```
   (Use your actual backend URL from Render)

4. **Save** - Frontend will auto-redeploy (takes ~1 minute)

### Step 6: Verify Deployment

#### Backend Health Check:
```bash
curl https://accessslot-backend-xxxx.onrender.com/api/
```
Expected: JSON response or DRF browsable API HTML

#### Frontend Check:
Visit: `https://accessslot-frontend-xxxx.onrender.com`
Expected: AccessSlot login page loads

#### End-to-End Test:
1. Open frontend URL
2. Try to register a new user
3. Try to login
4. Should receive JWT tokens and see dashboard

## Environment Variables (Auto-Configured)

### Backend (accessslot-backend)

| Variable | Source | Description |
|----------|--------|-------------|
| `PYTHON_VERSION` | Blueprint | Python 3.11.9 |
| `DEBUG` | Blueprint | False (production) |
| `SECRET_KEY` | Auto-generated | Django secret key (50+ chars) |
| `ALLOWED_HOSTS` | Auto-configured | Service hostname |
| `DB_NAME` | Database | PostgreSQL database name |
| `DB_USER` | Database | PostgreSQL username |
| `DB_PASSWORD` | Database | PostgreSQL password |
| `DB_HOST` | Database | PostgreSQL hostname |
| `DB_PORT` | Database | PostgreSQL port (5432) |
| `JWT_ACCESS_TOKEN_LIFETIME` | Blueprint | 60 minutes |
| `JWT_REFRESH_TOKEN_LIFETIME` | Blueprint | 1440 minutes (24h) |
| `SECURE_SSL_REDIRECT` | Blueprint | False (Render handles SSL) |
| `CORS_ALLOWED_ORIGINS` | **Manual** | Frontend URL (you add this) |

### Frontend (accessslot-frontend)

| Variable | Source | Description |
|----------|--------|-------------|
| `NODE_VERSION` | Blueprint | Node.js 20 |
| `VITE_API_BASE_URL` | **Manual** | Backend API URL (you add this) |

## Build Commands (Automated)

### Backend:
```bash
pip install -r requirements.txt && \
python manage.py collectstatic --noinput && \
python manage.py migrate --noinput
```

### Frontend:
```bash
npm ci && npm run build
```

## Start Commands (Automated)

### Backend:
```bash
gunicorn accessslot.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
```

### Frontend:
Static files served from `./dist`

## Automatic Deployments

After initial setup, Render automatically deploys on every push to `main`:

```bash
git push origin main
```

Render will:
1. Pull latest code
2. Run build commands
3. Run migrations (backend only)
4. Restart services

## Monitoring

### View Logs:

**Backend logs:**
1. Render Dashboard → `accessslot-backend` → "Logs" tab
2. Real-time application logs
3. Gunicorn access logs
4. Django error logs

**Frontend logs:**
1. Render Dashboard → `accessslot-frontend` → "Events" tab
2. Build logs
3. Deployment events

### Database Access:

1. Render Dashboard → `accessslot-db` → "Info" tab
2. Connection details shown
3. Can connect with psql or database client

## Troubleshooting

### Issue: Backend "Service Unavailable"

**Check:**
1. Logs for errors: Dashboard → Backend → Logs
2. Build succeeded: Dashboard → Backend → Events
3. Migrations ran: Look for "Running migrations" in logs

**Common causes:**
- Database connection issue (check DB_* variables)
- Missing environment variable
- Migration failure

### Issue: Frontend loads but API calls fail

**Check:**
1. `VITE_API_BASE_URL` is set correctly
2. Backend URL includes `/api` at the end
3. `CORS_ALLOWED_ORIGINS` includes frontend URL
4. Backend is running (not sleeping on free tier)

**Fix:**
- Update CORS_ALLOWED_ORIGINS in backend
- Ensure VITE_API_BASE_URL ends with `/api`
- Wake backend by visiting backend URL

### Issue: Static files not loading (admin panel)

**Check:**
- `collectstatic` ran in build: Look for "Collecting static files" in logs
- `STATIC_ROOT` configured in settings.py

**Fix:**
- Manually run `collectstatic`: Dashboard → Backend → Shell
  ```bash
  python manage.py collectstatic --noinput
  ```

### Issue: Database connection errors

**Check:**
- Database is running: Dashboard → Database → Status
- All DB_* environment variables set correctly

**Fix:**
- Verify database connection info matches environment variables
- Check database is in same region as backend

## Free Tier Limitations

**Render Free Tier:**
- ✅ PostgreSQL: Free for 90 days, then expires
- ✅ Web Service: 750 hours/month
- ✅ Static Sites: Unlimited
- ⚠️ Services sleep after 15 min of inactivity
- ⚠️ First request after sleep takes ~30 seconds

**To prevent sleeping:**
- Upgrade to paid plan ($7/month per service)
- Or use an uptime monitoring service (UptimeRobot, etc.)

## Upgrading Database After 90 Days

After free PostgreSQL expires:

**Option 1: Upgrade to Paid ($7/month)**
1. Dashboard → Database → "Upgrade"
2. Data is preserved

**Option 2: External Database**
1. Use Neon, Supabase, or ElephantSQL
2. Update DB_* environment variables

**Option 3: Export and Recreate**
1. Export data: `pg_dump`
2. Create new free database
3. Import data

## Custom Domain (Optional)

**Backend custom domain:**
1. Dashboard → Backend → "Settings" → "Custom Domain"
2. Add: `api.yourdomain.com`
3. Update DNS CNAME record
4. Update frontend `VITE_API_BASE_URL`
5. Update backend `ALLOWED_HOSTS`

**Frontend custom domain:**
1. Dashboard → Frontend → "Settings" → "Custom Domain"
2. Add: `yourdomain.com`
3. Update DNS CNAME record
4. Update backend `CORS_ALLOWED_ORIGINS`

## Cost Estimate

**Free tier (90 days):**
- Database: $0
- Backend: $0 (with sleep)
- Frontend: $0
- **Total: $0/month**

**After free tier expires:**
- PostgreSQL: $7/month (Starter)
- Backend: $7/month (to prevent sleep)
- Frontend: $0 (always free)
- **Total: $14/month**

Or use external free PostgreSQL (Neon, Supabase) to reduce cost.

## Next Steps After Deployment

1. ✅ Test user registration
2. ✅ Test login/logout
3. ✅ Test equipment listing
4. ✅ Test booking creation
5. ✅ Create admin superuser:
   ```bash
   # In Render Shell for backend
   python manage.py createsuperuser
   ```
6. ✅ Add test data
7. ✅ Test all features
8. ✅ Set up monitoring (optional)
9. ✅ Configure custom domain (optional)
10. ✅ Add SSL certificate (Render does this automatically)

## Support

- **Render Documentation:** https://render.com/docs
- **Render Community:** https://community.render.com
- **Django Deployment:** https://docs.djangoproject.com/en/5.0/howto/deployment/

---

**AccessSlot is now deployed and ready for production use!** 🎉

**Next:** Add users, create equipment items, start booking!
