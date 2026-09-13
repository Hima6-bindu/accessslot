# AccessSlot - Quick Deployment Guide

This is a quick reference for deploying AccessSlot to production. For detailed information, see the main README.md.

---

## Pre-Deployment Checklist

- [ ] PostgreSQL 14+ database provisioned
- [ ] Server/hosting environment ready
- [ ] Domain name configured (if applicable)
- [ ] SSL certificate obtained
- [ ] Environment variables prepared (see below)

---

## Environment Variables

### Backend Production .env

Create `backend/.env` with these values (DO NOT COMMIT THIS FILE):

```env
# Django Settings
SECRET_KEY=<generate-a-long-random-50+-character-string>
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database Configuration
DB_NAME=accessslot_production
DB_USER=accessslot_user
DB_PASSWORD=<strong-database-password>
DB_HOST=your-db-host.com
DB_PORT=5432

# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# CORS Settings (your frontend domain)
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com

# Security Settings (add these for production)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

### Frontend Production .env

Create `frontend/.env` (DO NOT COMMIT THIS FILE):

```env
VITE_API_BASE_URL=https://your-backend-domain.com/api
```

---

## Backend Deployment

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Database

```sql
CREATE DATABASE accessslot_production;
CREATE USER accessslot_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE accessslot_production TO accessslot_user;
```

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Create Default Usage Limits

```bash
python manage.py shell
>>> from equipment.models import UsageLimit
>>> from users.models import User
>>> UsageLimit.objects.create(role=User.Role.STUDENT, max_hours_per_week=10)
>>> UsageLimit.objects.create(role=User.Role.FACULTY, max_hours_per_week=20)
>>> UsageLimit.objects.create(role=User.Role.ADMIN, max_hours_per_week=1000)
>>> exit()
```

### 6. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 7. Test Configuration

```bash
python manage.py check --deploy
```

### 8. Run with Gunicorn

```bash
gunicorn accessslot.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

Or use systemd service (recommended):

```ini
# /etc/systemd/system/accessslot.service
[Unit]
Description=AccessSlot Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/accessslot/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn \
  --workers 3 \
  --bind unix:/run/accessslot.sock \
  accessslot.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl start accessslot
sudo systemctl enable accessslot
```

---

## Frontend Deployment

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Build Production Bundle

```bash
npm run build
```

This creates optimized files in `dist/` directory.

### 3. Deploy Static Files

**Option A: Nginx**

Copy `dist/` contents to nginx web root:

```bash
sudo cp -r dist/* /var/www/accessslot/
```

**Option B: CDN/Static Hosting**

Upload `dist/` contents to your CDN or static hosting service (Netlify, Vercel, S3 + CloudFront, etc.)

---

## Nginx Configuration

### Backend Proxy

```nginx
# /etc/nginx/sites-available/accessslot-api
server {
    listen 80;
    server_name api.your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.your-domain.com;
    
    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    
    location / {
        proxy_pass http://unix:/run/accessslot.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /path/to/accessslot/backend/staticfiles/;
    }
}
```

### Frontend

```nginx
# /etc/nginx/sites-available/accessslot-frontend
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    
    root /var/www/accessslot;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable sites:

```bash
sudo ln -s /etc/nginx/sites-available/accessslot-api /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/accessslot-frontend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Database Backup

### Automated PostgreSQL Backup Script

```bash
#!/bin/bash
# /opt/scripts/backup-accessslot.sh

BACKUP_DIR="/backups/accessslot"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="accessslot_production"
DB_USER="accessslot_user"

mkdir -p $BACKUP_DIR

# Dump database
pg_dump -U $DB_USER -d $DB_NAME -F c -f "$BACKUP_DIR/backup_$DATE.dump"

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.dump" -mtime +30 -delete

echo "Backup completed: backup_$DATE.dump"
```

Add to crontab:

```bash
# Run daily at 2 AM
0 2 * * * /opt/scripts/backup-accessslot.sh >> /var/log/accessslot-backup.log 2>&1
```

---

## Monitoring

### Health Check Endpoint

Django health check:

```bash
curl https://api.your-domain.com/api/equipment/ -H "Authorization: Bearer <token>"
```

### Log Monitoring

```bash
# Application logs
sudo journalctl -u accessslot -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Error Monitoring (Optional)

Consider integrating:
- **Sentry** for error tracking
- **DataDog** for application monitoring
- **New Relic** for performance monitoring

---

## Post-Deployment Verification

### 1. Test Authentication

```bash
# Register new user
curl -X POST https://api.your-domain.com/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "role": "STUDENT"
  }'

# Login
curl -X POST https://api.your-domain.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123!"
  }'
```

### 2. Test Equipment Listing

```bash
curl https://api.your-domain.com/api/equipment/ \
  -H "Authorization: Bearer <access_token>"
```

### 3. Check Frontend

1. Visit `https://your-domain.com`
2. Register and login
3. Test equipment browsing
4. Create a test booking
5. Check admin dashboard (if admin user)

### 4. Verify Database

```sql
-- Check users
SELECT id, username, email, role FROM users_user;

-- Check equipment
SELECT id, name, type, status FROM equipment_equipment;

-- Check bookings
SELECT id, user_id, equipment_id, start_time, end_time, status 
FROM equipment_booking 
ORDER BY created_at DESC LIMIT 10;
```

---

## Troubleshooting

### Issue: 502 Bad Gateway

**Check:**
- Is gunicorn running? `sudo systemctl status accessslot`
- Check logs: `sudo journalctl -u accessslot -n 50`
- Verify socket file exists: `ls -l /run/accessslot.sock`

### Issue: CORS Errors

**Check:**
- Verify `CORS_ALLOWED_ORIGINS` includes your frontend domain
- Ensure protocol matches (http vs https)
- Check nginx headers

### Issue: Static Files Not Loading

**Check:**
- Run `python manage.py collectstatic`
- Verify nginx static file location
- Check file permissions

### Issue: Database Connection Error

**Check:**
- Verify database credentials in `.env`
- Ensure database exists
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Test connection: `psql -h <host> -U <user> -d <database>`

### Issue: JWT Token Invalid

**Check:**
- Verify SECRET_KEY is set and consistent
- Check token expiry time
- Ensure frontend and backend domains match CORS config

---

## Security Best Practices

✅ **Always:**
- Use HTTPS in production
- Set DEBUG=False
- Use strong SECRET_KEY (50+ random characters)
- Enable security headers (HSTS, etc.)
- Keep dependencies updated
- Regular database backups
- Monitor logs for suspicious activity
- Use strong database passwords
- Limit database access to backend server only

❌ **Never:**
- Commit .env files
- Use DEBUG=True in production
- Expose database publicly
- Use weak passwords
- Ignore security warnings
- Skip SSL certificate

---

## Scaling Considerations

**When to scale:**
- Response times > 500ms
- Server CPU > 80%
- Database connections exhausted
- Growing user base

**Scaling options:**
1. **Vertical:** Increase server resources (CPU, RAM)
2. **Horizontal:** Add more application servers (requires load balancer)
3. **Database:** Read replicas, connection pooling (pgBouncer)
4. **Caching:** Add Redis for sessions and query caching
5. **CDN:** Use CloudFront or similar for static assets
6. **Background Tasks:** Use Celery for async processing

---

## Maintenance

### Regular Tasks

**Daily:**
- Check application logs for errors
- Monitor server resources
- Verify backups completed

**Weekly:**
- Review security logs
- Check database performance
- Update documentation

**Monthly:**
- Update dependencies (after testing)
- Review and optimize database queries
- Security audit

**Quarterly:**
- Full system backup test (restore verification)
- Performance optimization review
- Capacity planning

---

## Support

For issues or questions:
- Check logs first
- Review documentation
- Search existing issues
- Create new issue with details

---

**Good luck with your deployment! 🚀**
