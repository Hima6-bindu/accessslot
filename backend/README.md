# AccessSlot Backend - Equipment Booking System

Django REST API backend for the AccessSlot equipment booking system.

## Tech Stack

- **Framework**: Django 5.0.1
- **API**: Django REST Framework 3.14.0
- **Database**: PostgreSQL
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Testing**: pytest, pytest-django

## Project Structure

```
backend/
├── accessslot/          # Django project configuration
│   ├── settings.py      # Main settings file
│   ├── urls.py          # Root URL configuration
│   └── wsgi.py          # WSGI configuration
├── users/               # User management app
│   ├── models.py        # User model with roles
│   ├── serializers.py   # DRF serializers
│   ├── views.py         # API views
│   ├── permissions.py   # Role-based permissions
│   ├── urls.py          # User app URLs
│   ├── admin.py         # Django admin config
│   └── tests/           # Test suite
├── manage.py            # Django management script
├── requirements.txt     # Python dependencies
├── pytest.ini           # Pytest configuration
├── .env                 # Environment variables (local)
└── .env.example         # Environment variables template
```

## Setup Instructions

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 12+
- pip (Python package manager)

### 2. Create Virtual Environment

```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
cd backend
pip install -r requirements.txt
```

### 4. Configure PostgreSQL Database

1. Install PostgreSQL if not already installed
2. Create a database:

```sql
CREATE DATABASE accessslot_db;
CREATE USER postgres WITH PASSWORD 'your_password';
ALTER ROLE postgres SET client_encoding TO 'utf8';
ALTER ROLE postgres SET default_transaction_isolation TO 'read committed';
ALTER ROLE postgres SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE accessslot_db TO postgres;
```

### 5. Configure Environment Variables

Copy `.env.example` to `.env` and update the values:

```powershell
cp .env.example .env
```

Edit `.env` with your configuration:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=accessslot_db
DB_USER=postgres
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432

JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**Important**: Generate a secure `SECRET_KEY` for production:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### 6. Run Database Migrations

```powershell
python manage.py migrate
```

### 7. Create Superuser (Optional)

```powershell
python manage.py createsuperuser
```

### 8. Run Development Server

```powershell
python manage.py runserver
```

The API will be available at: `http://localhost:8000/`

## API Endpoints

### Authentication Endpoints

| Method | Endpoint                      | Description                | Auth Required |
|--------|-------------------------------|----------------------------|---------------|
| POST   | `/api/auth/register/`         | Register new user          | No            |
| POST   | `/api/auth/login/`            | Login (get JWT tokens)     | No            |
| POST   | `/api/auth/logout/`           | Logout                     | Yes           |
| POST   | `/api/auth/token/refresh/`    | Refresh access token       | No            |
| GET    | `/api/auth/profile/`          | Get current user profile   | Yes           |
| PUT    | `/api/auth/profile/update/`   | Update profile             | Yes           |
| PATCH  | `/api/auth/profile/update/`   | Partial profile update     | Yes           |
| POST   | `/api/auth/password/change/`  | Change password            | Yes           |

### User Roles

- **STUDENT**: Default role, can book equipment
- **FACULTY**: Extended privileges for faculty members
- **ADMIN**: Full system access, can manage users and equipment

### Authentication

The API uses JWT (JSON Web Tokens) for authentication.

**Login to get tokens:**

```bash
POST /api/auth/login/
{
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**

```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
        "id": 1,
        "username": "your_username",
        "email": "user@example.com",
        "role": "STUDENT"
    }
}
```

**Use access token in requests:**

```bash
Authorization: Bearer <access_token>
```

**Refresh token when expired:**

```bash
POST /api/auth/token/refresh/
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## Running Tests

### Run all tests:

```powershell
pytest
```

### Run tests with coverage:

```powershell
pytest --cov=users --cov-report=html
```

### Run specific test file:

```powershell
pytest users/tests/test_authentication.py
```

### Run specific test:

```powershell
pytest users/tests/test_authentication.py::TestUserRegistration::test_register_user_success
```

## Django Admin

Access the admin interface at `http://localhost:8000/admin/`

Use the superuser credentials you created with `createsuperuser` command.

## Development

### Create new Django app:

```powershell
python manage.py startapp app_name
```

### Make migrations after model changes:

```powershell
python manage.py makemigrations
python manage.py migrate
```

### Run Django shell:

```powershell
python manage.py shell
```

### Collect static files (for production):

```powershell
python manage.py collectstatic
```

## Common Issues

### Issue: Database connection error

**Solution**: Verify PostgreSQL is running and credentials in `.env` are correct.

### Issue: Module not found errors

**Solution**: Ensure virtual environment is activated and dependencies are installed:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Issue: Migration errors

**Solution**: Try resetting migrations (development only):

```powershell
python manage.py migrate --run-syncdb
```

## Next Steps

Phase 1 (Foundation) is complete. Next phases will add:

- **Phase 2**: Equipment management (models, APIs, CRUD operations)
- **Phase 3**: Booking system with validation and concurrency control
- **Phase 4**: Maintenance periods and conflict handling
- **Phase 5**: Waiting list functionality
- **Phase 6**: Admin dashboard and analytics
- **Phase 7**: Complete testing and deployment

## License

Proprietary - AccessSlot Equipment Booking System
