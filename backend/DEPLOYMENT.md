# AccessSlot Backend - Production Deployment Guide

This guide covers deploying the AccessSlot backend to production.

## Prerequisites

- Python 3.11+
- PostgreSQL 12+ database
- Production WSGI server (Gunicorn)
- Domain name with HTTPS/SSL certificate
- Environment variables configured

## Production Checklist

### ✅ Security Configuration

The backend is configured with production security settings that activate when `DEBUG=False`:

- ✅ SECRET_KEY from environment variable
- ✅ DEBUG=False in production
- ✅ ALLOWED_HOSTS from environment
- ✅ SECURE_SSL_REDIRECT enabled
- ✅ SESSION_COOKIE_SECURE enabled
- ✅ CSRF_COOKIE_SECURE enabled
- ✅ HSTS enabled (1 year)
- ✅ XSS protection enabled
- ✅ Content type sniffing protection
- ✅ X-Frame-Options set to DENY
- ✅ Proxy SSL header support

### ✅ Static Files

- ✅ STATIC_ROOT configured: `backend/staticfiles`
- ✅ STATIC_URL configured: `/static/`
- ✅ Run `python manage.py collectstatic` before deployment

### ✅ Database

- ✅ PostgreSQL configuration from environment
- ✅ Database migrations ready
- ✅ Connection pooling ready (configure via DATABASE_URL if needed)

### ✅ API & Authentication

- ✅ JWT authentication configured
- ✅ CORS configured from environment
- ✅ REST Framework configured
- ✅ Password validation enabled

## Required Environment Variables

Create a `.env` file in production (or configure via platform):

```env
# Django Settings
SECRET_KEY=<generate-secure-random-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database Configuration (PostgreSQL)
DB_NAME=accessslot_db
DB_USER=accessslot_user
DB_PASSWORD=<secure-database-password>
DB_HOST=<database-host>
DB_PORT=5432

# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# CORS Settings (frontend URLs)
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Optional: Disable SSL redirect if behind reverse proxy handling SSL
# SECURE_SSL_REDIRECT=False
```

### Generate SECRET_KEY

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Deployment Options

### Option 1: Railway (Recommended for Simplicity)

**Pros:**
- PostgreSQL included
- Automatic deployments from GitHub
- Free tier available
- Simple configuration
- Built-in HTTPS

**Steps:**

1. **Create Railway account**: https://railway.app
2. **Create new project** → Deploy from GitHub repo
3. **Add PostgreSQL database** (Railway will auto-configure DATABASE_URL)
4. **Configure environment variables** in Railway dashboard
5. **Add start command**: 
   ```bash
   gunicorn accessslot.wsgi:application --bind 0.0.0.0:$PORT
   ```
6. **Deploy** - Railway will automatically build and deploy

**Railway Configuration:**
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn accessslot.wsgi:application --bind 0.0.0.0:$PORT`
- Health check path: `/api/auth/login/` (returns 405 Method Not Allowed - indicates API is up)

### Option 2: Render

**Pros:**
- Free PostgreSQL database
- Automatic deployments from GitHub
- Simple dashboard
- Built-in HTTPS

**Steps:**

1. **Create Render account**: https://render.com
2. **Create PostgreSQL database** first
3. **Create Web Service** from GitHub repo
4. **Configure**:
   - Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - Start Command: `gunicorn accessslot.wsgi:application`
   - Environment: Python 3.11
5. **Add environment variables** from Render dashboard
6. **Connect PostgreSQL database**
7. **Deploy**

### Option 3: Fly.io

**Pros:**
- PostgreSQL available
- Docker-based deployment
- Global edge network
- Free tier available

**Steps:**

1. **Install Fly CLI**: `curl -L https://fly.io/install.sh | sh`
2. **Create fly.toml** configuration
3. **Deploy**: `fly deploy`
4. **Add PostgreSQL**: `fly postgres create`
5. **Configure environment variables**: `fly secrets set SECRET_KEY=...`

### Option 4: DigitalOcean App Platform

**Pros:**
- Managed PostgreSQL
- Automatic scaling
- Good performance

**Steps:**

1. **Create DigitalOcean account**
2. **Create App** from GitHub repo
3. **Add PostgreSQL database**
4. **Configure environment**
5. **Deploy**

## Pre-Deployment Steps

### 1. Install Production Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Verify Gunicorn is installed:
```bash
gunicorn --version
```

### 2. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 3. Run Migrations

```bash
python manage.py migrate --noinput
```

### 4. Create Superuser (Optional)

```bash
python manage.py createsuperuser --noinput \
  --username admin \
  --email admin@yourdomain.com
```

### 5. Test Gunicorn Locally

```bash
# Test with environment variables
gunicorn accessslot.wsgi:application --bind 0.0.0.0:8000
```

Visit: http://localhost:8000/api/

## Production Commands

### Start Gunicorn

**Basic:**
```bash
gunicorn accessslot.wsgi:application
```

**With options:**
```bash
gunicorn accessslot.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 30 \
  --access-logfile - \
  --error-logfile -
```

**Recommended for production:**
```bash
gunicorn accessslot.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers $(( 2 * $(nproc) + 1 )) \
  --threads 2 \
  --timeout 60 \
  --keepalive 5 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

### Worker Count Formula

```
workers = (2 × CPU_cores) + 1
```

For Railway/Render/Fly.io:
- Use 3-4 workers (they typically provide 1-2 vCPUs on free tier)

## Health Checks

Most platforms require a health check endpoint.

**Options:**

1. **Use Django admin** (requires authentication):
   - Path: `/admin/`
   - Returns 302 redirect when healthy

2. **Use API endpoint** (returns error but confirms API is running):
   - Path: `/api/auth/login/`
   - Returns 405 Method Not Allowed (expected for GET request)

3. **Create custom health check** (optional):
   ```python
   # In accessslot/urls.py
   from django.http import JsonResponse
   
   def health_check(request):
       return JsonResponse({"status": "healthy"})
   
   urlpatterns = [
       path('health/', health_check),
       # ... other patterns
   ]
   ```

## Post-Deployment Verification

### 1. Check API is accessible

```bash
curl https://your-api-domain.com/api/
```

Expected: JSON response or 404 with DRF error page

### 2. Test user registration

```bash
curl -X POST https://your-api-domain.com/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User",
    "role": "STUDENT"
  }'
```

### 3. Test login

```bash
curl -X POST https://your-api-domain.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123!"
  }'
```

Expected: JSON with access/refresh tokens

### 4. Check static files

```bash
curl https://your-api-domain.com/static/admin/css/base.css
```

Expected: CSS file content

## Monitoring & Maintenance

### Database Backups

- **Railway**: Automatic daily backups
- **Render**: Configure backup schedule
- **Manual**: Use `pg_dump` for PostgreSQL backups

### Logs

View application logs:
```bash
# Railway
railway logs

# Render
# View in dashboard

# Fly.io
fly logs
```

### Update Deployment

Most platforms auto-deploy on git push to main:
```bash
git push origin main
```

## Troubleshooting

### Issue: Static files not loading

**Solution:**
1. Ensure `collectstatic` runs in build command
2. Verify `STATIC_ROOT` and `STATIC_URL` are configured
3. Check platform serves static files (or use WhiteNoise middleware)

### Issue: Database connection errors

**Solution:**
1. Verify DATABASE_URL or DB_* environment variables
2. Check database is running and accessible
3. Verify database credentials

### Issue: CORS errors from frontend

**Solution:**
1. Add frontend URL to `CORS_ALLOWED_ORIGINS`
2. Ensure both http:// and https:// versions if needed
3. Verify `corsheaders` middleware is enabled

### Issue: 500 Internal Server Error

**Solution:**
1. Check application logs
2. Verify `DEBUG=False` in production
3. Ensure `SECRET_KEY` is set
4. Check `ALLOWED_HOSTS` includes your domain

## Security Best Practices

✅ **Never commit `.env` files** to git  
✅ **Use strong SECRET_KEY** (50+ random characters)  
✅ **Use environment variables** for all secrets  
✅ **Enable HTTPS** on production domain  
✅ **Keep dependencies updated** (`pip list --outdated`)  
✅ **Monitor security advisories** for Django/dependencies  
✅ **Use strong database passwords**  
✅ **Restrict database access** to application only  
✅ **Regular backups** of database  
✅ **Monitor logs** for suspicious activity  

## Next Steps

After backend deployment:

1. **Deploy frontend** (Vercel/Netlify recommended)
2. **Update frontend** `VITE_API_BASE_URL` to production API URL
3. **Update backend** `CORS_ALLOWED_ORIGINS` to frontend URL
4. **Test end-to-end** functionality
5. **Set up monitoring** (Sentry, LogRocket, etc.)
6. **Configure custom domain** (if applicable)
7. **Set up CI/CD** (already done via GitHub Actions)

## Support

For deployment issues:
- Check platform documentation
- Review Django deployment docs: https://docs.djangoproject.com/en/5.0/howto/deployment/
- Check Gunicorn docs: https://docs.gunicorn.org/

---

**AccessSlot Backend is Production-Ready!** 🚀
