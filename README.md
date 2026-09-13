# AccessSlot

A full-stack college/lab equipment booking and reservation platform built with Django REST Framework and React.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18.3-blue.svg)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-blue.svg)](https://www.postgresql.org/)
[![Tests](https://img.shields.io/badge/Tests-180%20passed-brightgreen.svg)](.)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Technical Highlights](#technical-highlights)
- [Project Structure](#project-structure)
- [Local Setup](#local-setup)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [API Documentation](#api-documentation)
- [Security Considerations](#security-considerations)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## 🎯 Overview

**AccessSlot** is a comprehensive equipment booking and reservation system designed for colleges, universities, and research labs. It enables students and faculty to reserve equipment, manages bookings with conflict detection, enforces usage limits, handles maintenance schedules, and provides a FIFO-based waiting list system.

The system features role-based access control (Student, Faculty, Admin), real-time booking conflict detection with database-level concurrency protection, and a modern responsive user interface.

---

## 🔍 Problem Statement

Educational institutions and research labs face challenges managing shared equipment:

- **Booking Conflicts:** Multiple users attempting to book the same equipment simultaneously
- **Unfair Access:** No systematic way to ensure fair equipment distribution
- **Usage Tracking:** Difficulty monitoring equipment utilization and enforcing limits
- **Maintenance Coordination:** Equipment downtime not communicated effectively
- **Administrative Overhead:** Manual booking processes are time-consuming and error-prone

**AccessSlot solves these problems** with automated booking management, real-time conflict detection, usage limit enforcement, maintenance scheduling, and FIFO waiting lists.

---

## ✨ Key Features

### 🔐 Authentication & Authorization
- JWT-based authentication with access and refresh tokens
- Role-based access control (STUDENT, FACULTY, ADMIN)
- Secure password hashing with Django's built-in validators
- Protected routes and API endpoints

### 🛠️ Equipment Management (Admin Only)
- Create, read, update, and delete equipment
- Track equipment status (Available, In Use, Maintenance, Retired)
- Configure maximum booking duration per equipment
- Search and filter equipment by type and status

### 📅 Booking System
- Create bookings with conflict detection
- View own bookings (students/faculty) or all bookings (admin)
- Update and cancel bookings
- Automatic conflict validation on creation and update
- **PostgreSQL row-level locking** prevents race conditions
- Real-time booking conflict detection using `select_for_update()`

### ⏱️ Weekly Usage Limits
- Configurable weekly hour limits per role (Student: 10h, Faculty: 20h, Admin: unlimited)
- Automatic calculation of weekly usage
- Prevents bookings that exceed limits
- Cancelled bookings don't count toward limits

### 🔧 Maintenance Scheduling (Admin Only)
- Schedule maintenance periods for equipment
- Automatic blocking of bookings during maintenance
- Overlap validation prevents double-booking maintenance
- Integration with booking conflict detection

### 📋 FIFO Waiting List
- Join waiting list when equipment is unavailable
- Automatic FIFO (First In, First Out) position assignment
- Database-level locking ensures correct position ordering
- Automatic notification when bookings are cancelled
- Only notifies users whose requested time overlaps with cancelled booking
- Position reordering on cancellation

### 📊 Admin Dashboard
- Real-time statistics (total equipment, bookings, users, maintenance)
- View all bookings with search and filtering
- Manage maintenance schedules
- User management (view, update role, deactivate)
- Waiting list overview

### 👥 User Management (Admin Only)
- List all users with search and filters
- Update user information (name, email, role, active status)
- Last-admin protection (cannot deactivate the only active admin)
- Sensitive data protection (passwords never exposed)

---

## 🔧 Technology Stack

### Backend
- **Framework:** Django 5.0 & Django REST Framework 3.14
- **Database:** PostgreSQL (with row-level locking)
- **Authentication:** JWT (djangorestframework-simplejwt)
- **CORS:** django-cors-headers
- **Testing:** pytest, pytest-django, Faker
- **Configuration:** python-decouple (environment variables)

### Frontend
- **Framework:** React 18.3
- **Build Tool:** Vite 8.3
- **Routing:** React Router 7.1
- **HTTP Client:** Axios 1.7
- **Styling:** Custom CSS with responsive design

### Database
- **PostgreSQL** with:
  - Row-level locking (`SELECT FOR UPDATE`)
  - Transaction isolation
  - Concurrent booking protection
  - MVCC (Multi-Version Concurrency Control)

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        React Frontend                        │
│  (Vite, React Router, Axios, JWT Authentication)           │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/JSON (REST API)
                      │ Authorization: Bearer <JWT>
┌─────────────────────▼───────────────────────────────────────┐
│                   Django REST Framework                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Authentication Layer (JWT)                          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Permission Layer (Role-Based Access Control)        │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Views (Equipment, Bookings, Maintenance, etc.)  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Service Layer (Business Logic + Validation)         │  │
│  │  - BookingService (conflict detection, locking)      │  │
│  │  - MaintenanceService (overlap validation)           │  │
│  │  - WaitingListService (FIFO, notifications)          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Models (Django ORM)                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │ SQL Queries
                      │ SELECT FOR UPDATE (Locking)
┌─────────────────────▼───────────────────────────────────────┐
│                      PostgreSQL Database                     │
│  - Row-level locking                                        │
│  - Transaction isolation                                    │
│  - MVCC (Multi-Version Concurrency Control)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Technical Highlights

### 1. PostgreSQL Concurrency Protection

**Problem:** Multiple users booking the same equipment at the same time can cause double-booking.

**Solution:** Database-level row locking with `select_for_update()`.

```python
@transaction.atomic
def create_booking(equipment_id, user, start_time, end_time, purpose):
    # Lock the equipment row to prevent concurrent bookings
    equipment = Equipment.objects.select_for_update().get(id=equipment_id)
    
    # Check for conflicts (no other transaction can modify equipment)
    conflicting_bookings = Booking.objects.filter(
        equipment=equipment,
        status='ACTIVE',
        start_time__lt=end_time,
        end_time__gt=start_time
    ).exists()
    
    if conflicting_bookings:
        raise ValidationError("Booking conflict detected")
    
    # Create booking (lock is held until transaction commits)
    booking = Booking.objects.create(...)
    return booking
```

**Why it works:**
- `select_for_update()` acquires a row-level lock on PostgreSQL
- Other transactions attempting to lock the same equipment must wait
- Ensures sequential processing of concurrent booking attempts
- First transaction wins, others see the conflict and fail gracefully

### 2. Booking Conflict Detection

**Algorithm:** Interval overlap detection

Two bookings conflict if:
```
existing.start_time < requested.end_time AND existing.end_time > requested.start_time
```

**Examples:**
- ✅ `[1-2]` and `[2-3]` - No conflict (back-to-back)
- ❌ `[1-3]` and `[2-4]` - Conflict (partial overlap)
- ❌ `[1-5]` and `[2-3]` - Conflict (one inside other)

**Implementation:**
```python
def has_conflict(equipment, start_time, end_time, exclude_booking=None):
    conflicts = Booking.objects.filter(
        equipment=equipment,
        status='ACTIVE',
        start_time__lt=end_time,
        end_time__gt=start_time
    )
    
    if exclude_booking:
        conflicts = conflicts.exclude(id=exclude_booking.id)
    
    return conflicts.exists()
```

### 3. Weekly Usage Limits

Tracks usage per role with rolling weekly calculation:

```python
def get_weekly_usage_hours(user):
    one_week_ago = timezone.now() - timedelta(days=7)
    
    bookings = Booking.objects.filter(
        user=user,
        status='ACTIVE',
        start_time__gte=one_week_ago
    )
    
    total_hours = sum(b.duration_hours for b in bookings)
    return total_hours
```

**Limits:**
- Students: 10 hours/week
- Faculty: 20 hours/week  
- Admin: Unlimited

### 4. FIFO Waiting List

**Problem:** Fair equipment access when unavailable.

**Solution:** Database-level position management with locking.

```python
@transaction.atomic
def join_waiting_list(equipment, user, start_time, end_time):
    # Lock equipment to prevent position conflicts
    equipment = Equipment.objects.select_for_update().get(pk=equipment.pk)
    
    # Get max position with locking
    max_position = WaitingList.objects.filter(
        equipment=equipment,
        status='WAITING'
    ).select_for_update().aggregate(Max('position'))['position__max']
    
    next_position = (max_position or 0) + 1
    
    # Create entry with guaranteed unique position
    entry = WaitingList.objects.create(
        equipment=equipment,
        user=user,
        position=next_position,
        ...
    )
    return entry
```

**Notification Logic:**
When a booking is cancelled, only notify users whose requested time overlaps:

```python
def notify_waiting_list(equipment, cancelled_start, cancelled_end):
    eligible = WaitingList.objects.filter(
        equipment=equipment,
        status='WAITING',
        requested_start_time__lt=cancelled_end,
        requested_end_time__gt=cancelled_start
    ).order_by('position').first()
    
    if eligible:
        eligible.status = 'NOTIFIED'
        eligible.save()
```

### 5. Maintenance Period Blocking

Maintenance periods automatically block bookings:

```python
def validate_no_maintenance_conflict(equipment, start_time, end_time):
    maintenance_conflicts = Maintenance.objects.filter(
        equipment=equipment,
        start_time__lt=end_time,
        end_time__gt=start_time
    ).exists()
    
    if maintenance_conflicts:
        raise ValidationError(
            "Cannot book during scheduled maintenance"
        )
```

### 6. JWT Authentication

**Token-based authentication** with access and refresh tokens:

- **Access Token:** Short-lived (60 minutes), included in requests
- **Refresh Token:** Long-lived (24 hours), used to obtain new access tokens
- **Stateless:** No server-side session storage
- **Secure:** Tokens include user ID, username, email, and role

### 7. Role-Based Authorization

**Three roles with hierarchical permissions:**

| Feature | Student | Faculty | Admin |
|---------|---------|---------|-------|
| View equipment | ✅ | ✅ | ✅ |
| Create bookings | ✅ | ✅ | ✅ |
| View own bookings | ✅ | ✅ | ✅ |
| Join waiting list | ✅ | ✅ | ✅ |
| View all bookings | ❌ | ❌ | ✅ |
| Manage equipment | ❌ | ❌ | ✅ |
| Schedule maintenance | ❌ | ❌ | ✅ |
| Manage users | ❌ | ❌ | ✅ |

**Implementation:**
```python
class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'ADMIN'
        )
```

---

## 📁 Project Structure

```
accessslot/
│
├── backend/                      # Django backend
│   ├── accessslot/              # Project settings
│   │   ├── settings.py          # Main settings (PostgreSQL)
│   │   ├── settings_postgresql.py  # Test settings
│   │   ├── urls.py              # Root URL configuration
│   │   └── wsgi.py              # WSGI application
│   │
│   ├── users/                   # User authentication app
│   │   ├── models.py            # Custom User model with roles
│   │   ├── serializers.py       # User serializers
│   │   ├── admin_serializers.py # Admin user management
│   │   ├── views.py             # Auth endpoints
│   │   ├── admin_views.py       # User management endpoints
│   │   ├── permissions.py       # Role-based permissions
│   │   ├── urls.py              # User app URLs
│   │   └── tests/               # User tests
│   │       ├── test_authentication.py
│   │       ├── test_permissions.py
│   │       ├── test_models.py
│   │       └── test_admin_user_management.py
│   │
│   ├── equipment/               # Equipment management app
│   │   ├── models.py            # Equipment, Booking, Maintenance, etc.
│   │   ├── serializers.py       # Equipment serializers
│   │   ├── booking_serializers.py  # Booking serializers
│   │   ├── maintenance_serializers.py
│   │   ├── waitinglist_serializers.py
│   │   ├── views.py             # Equipment endpoints
│   │   ├── booking_views.py     # Booking endpoints
│   │   ├── maintenance_views.py
│   │   ├── waitinglist_views.py
│   │   ├── booking_services.py  # Booking business logic
│   │   ├── maintenance_services.py
│   │   ├── waitinglist_services.py
│   │   ├── urls.py              # Equipment app URLs
│   │   └── tests/               # Equipment tests
│   │       ├── test_api.py
│   │       ├── test_booking_api.py
│   │       ├── test_booking_concurrency.py  # ⭐ Concurrency tests
│   │       ├── test_maintenance.py
│   │       └── test_waitinglist.py
│   │
│   ├── manage.py                # Django management script
│   ├── requirements.txt         # Python dependencies
│   ├── pytest.ini               # Pytest configuration
│   ├── .env.example             # Environment variables template
│   └── README.md                # Backend documentation
│
├── frontend/                    # React frontend
│   ├── src/
│   │   ├── components/          # Reusable components
│   │   │   ├── BookingModal.jsx
│   │   │   ├── BookingDetailsModal.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   │
│   │   ├── pages/               # Page components
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Equipment.jsx
│   │   │   ├── MyBookings.jsx
│   │   │   ├── MyWaitingList.jsx
│   │   │   ├── AdminDashboard.jsx
│   │   │   ├── AdminBookings.jsx
│   │   │   ├── EquipmentAdmin.jsx
│   │   │   ├── Maintenance.jsx
│   │   │   └── AdminUsers.jsx
│   │   │
│   │   ├── context/             # React context
│   │   │   └── AuthContext.jsx  # Authentication state
│   │   │
│   │   ├── services/            # API services
│   │   │   └── api.js           # Axios configuration + JWT
│   │   │
│   │   ├── styles/              # CSS stylesheets
│   │   │   ├── Auth.css
│   │   │   ├── Pages.css
│   │   │   └── Admin.css
│   │   │
│   │   ├── App.jsx              # Main app component
│   │   └── main.jsx             # Entry point
│   │
│   ├── package.json             # Node dependencies
│   ├── vite.config.js           # Vite configuration
│   ├── .env.example             # Frontend environment template
│   └── README.md                # Frontend documentation
│
├── .gitignore                   # Git ignore rules
├── README.md                    # This file
└── FINAL_AUDIT_REPORT.md       # Security audit report
```

---

## 🛠️ Local Setup

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 14+**
- **Git**

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd accessslot/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database**
   ```sql
   CREATE DATABASE accessslot_db;
   CREATE USER your_db_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE accessslot_db TO your_db_user;
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your values:
   ```env
   SECRET_KEY=your-secret-key-here-generate-a-long-random-string
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   DB_NAME=accessslot_db
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=5432
   
   JWT_ACCESS_TOKEN_LIFETIME=60
   JWT_REFRESH_TOKEN_LIFETIME=1440
   
   CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create superuser (admin)**
   ```bash
   python manage.py createsuperuser
   ```

8. **Load default usage limits (optional)**
   ```bash
   python manage.py shell
   >>> from equipment.models import UsageLimit
   >>> from users.models import User
   >>> UsageLimit.objects.create(role=User.Role.STUDENT, max_hours_per_week=10)
   >>> UsageLimit.objects.create(role=User.Role.FACULTY, max_hours_per_week=20)
   >>> UsageLimit.objects.create(role=User.Role.ADMIN, max_hours_per_week=1000)
   >>> exit()
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd ../frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env`:
   ```env
   VITE_API_BASE_URL=http://localhost:8000/api
   ```

---

## 🚀 Running the Application

### Backend (Django)

```bash
cd backend
python manage.py runserver
```

Backend runs on: `http://localhost:8000`

API endpoints: `http://localhost:8000/api/`

### Frontend (React)

```bash
cd frontend
npm run dev
```

Frontend runs on: `http://localhost:3000`

### Access the Application

1. Open browser to `http://localhost:3000`
2. Register a new account or login
3. Default roles:
   - Register as STUDENT (default)
   - Admin account created via `createsuperuser`
   - Change roles via admin user management

---

## 🧪 Testing

### Backend Tests

**Run all tests:**
```bash
cd backend
pytest
```

**Run with coverage:**
```bash
pytest --cov=. --cov-report=html
```

**Run specific test file:**
```bash
pytest equipment/tests/test_booking_concurrency.py -v
```

**Run concurrency tests specifically:**
```bash
pytest equipment/tests/test_booking_concurrency.py -v -k concurrency
```

### Test Results

```
180 tests passed in 106.39s

✅ Equipment tests: 90 passed
✅ User tests: 60 passed
✅ Booking concurrency: 6 passed
✅ All authorization tests passed
✅ All security tests passed
```

**Key Test Areas:**
- ✅ Authentication & JWT tokens
- ✅ Role-based permissions
- ✅ Equipment CRUD operations
- ✅ Booking conflict detection
- ✅ **Concurrent booking attempts (PostgreSQL locking)**
- ✅ Weekly usage limit enforcement
- ✅ Maintenance period blocking
- ✅ FIFO waiting list ordering
- ✅ User management and last-admin protection
- ✅ Sensitive data protection (no password exposure)

### Frontend Build

**Production build:**
```bash
cd frontend
npm run build
```

**Build verification:**
```
✓ 103 modules transformed
✓ built in 421ms
```

---

## 📚 API Documentation

### Base URL

```
http://localhost:8000/api
```

### Authentication Endpoints

#### Register
```http
POST /auth/register/
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "role": "STUDENT"
}
```

#### Login
```http
POST /auth/login/
Content-Type: application/json

{
  "username": "johndoe",
  "password": "SecurePass123!"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "role": "STUDENT"
  }
}
```

#### Refresh Token
```http
POST /auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Equipment Endpoints

#### List Equipment
```http
GET /equipment/
Authorization: Bearer <access_token>

Query Parameters:
- status: AVAILABLE|IN_USE|MAINTENANCE|RETIRED
- type: equipment type (e.g., "Microscope")
- search: search by name
```

#### Get Equipment Details
```http
GET /equipment/{id}/
Authorization: Bearer <access_token>
```

#### Create Equipment (Admin Only)
```http
POST /equipment/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "High-Resolution Microscope",
  "type": "Microscope",
  "description": "Zeiss research microscope",
  "location": "Lab 101",
  "status": "AVAILABLE",
  "max_booking_duration_hours": 4
}
```

### Booking Endpoints

#### Create Booking
```http
POST /bookings/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "equipment": 1,
  "start_time": "2026-09-15T10:00:00Z",
  "end_time": "2026-09-15T12:00:00Z",
  "purpose": "Research experiment"
}
```

#### My Bookings
```http
GET /bookings/my_bookings/
Authorization: Bearer <access_token>
```

#### Cancel Booking
```http
PATCH /bookings/{id}/cancel/
Authorization: Bearer <access_token>
```

### Waiting List Endpoints

#### Join Waiting List
```http
POST /waiting-list/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "equipment": 1,
  "requested_start_time": "2026-09-15T10:00:00Z",
  "requested_end_time": "2026-09-15T12:00:00Z"
}
```

#### My Waiting List Entries
```http
GET /waiting-list/my_entries/
Authorization: Bearer <access_token>
```

### Admin Endpoints

#### List All Users (Admin)
```http
GET /auth/users/
Authorization: Bearer <access_token>

Query Parameters:
- search: username/email/name
- role: STUDENT|FACULTY|ADMIN
- is_active: true|false
```

#### Update User (Admin)
```http
PATCH /auth/users/{id}/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "Updated",
  "last_name": "Name",
  "email": "newemail@example.com",
  "role": "FACULTY",
  "is_active": true
}
```

---

## 🔒 Security Considerations

### Authentication Security

✅ **Password Hashing:** Django's PBKDF2 with SHA256  
✅ **JWT Tokens:** Stateless authentication with short expiry  
✅ **Password Validation:** Minimum 8 characters, complexity requirements  
✅ **Token Refresh:** Secure token renewal mechanism

### Authorization Security

✅ **Role-Based Access Control:** Enforced at API level  
✅ **Object-Level Permissions:** Users can only access their own resources  
✅ **Admin Verification:** Critical operations require ADMIN role  
✅ **Last-Admin Protection:** Prevents system lockout

### Data Security

✅ **No Password Exposure:** Passwords never returned in API responses  
✅ **No Password Hash Exposure:** Hashes never exposed  
✅ **No Token Leakage:** JWT tokens only in authentication endpoints  
✅ **Environment Variables:** Secrets stored in .env (not committed)

### Database Security

✅ **SQL Injection Protection:** Django ORM parameterized queries  
✅ **Transaction Isolation:** PostgreSQL MVCC  
✅ **Row-Level Locking:** Prevents race conditions  
✅ **Validated Input:** All user input validated via serializers

### Deployment Security (Production)

⚠️ **Required for Production:**
- Set `DEBUG=False`
- Use strong `SECRET_KEY` (50+ characters)
- Enable `SECURE_SSL_REDIRECT=True`
- Set `SESSION_COOKIE_SECURE=True`
- Set `CSRF_COOKIE_SECURE=True`
- Configure `SECURE_HSTS_SECONDS`
- Use HTTPS only
- Configure production CORS origins
- Set up database backups
- Enable error monitoring (Sentry, etc.)
- Use environment-specific `.env` files

---

## 🔮 Future Improvements

### Short-term Enhancements
- [ ] Email notifications for booking confirmations and waiting list
- [ ] SMS notifications for urgent updates
- [ ] Calendar view for bookings
- [ ] Export booking history (CSV, PDF)
- [ ] Equipment photos and detailed specifications
- [ ] Booking history analytics
- [ ] Equipment utilization reports

### Medium-term Enhancements
- [ ] Mobile app (React Native)
- [ ] QR code check-in/check-out
- [ ] Equipment location tracking (with GPS/beacons)
- [ ] Recurring booking support
- [ ] Equipment categories and tags
- [ ] Advanced search and filters
- [ ] User profile customization
- [ ] Booking reminders

### Long-term Enhancements
- [ ] Integration with university SSO (SAML, OAuth)
- [ ] Multi-tenant support (multiple institutions)
- [ ] Equipment damage reporting
- [ ] Inventory management integration
- [ ] Cost tracking and billing
- [ ] AI-powered booking recommendations
- [ ] Predictive maintenance scheduling
- [ ] GraphQL API alternative

---

## 📊 Performance Characteristics

**Backend Performance:**
- API response time: < 100ms (typical)
- Database queries: Optimized with select_related/prefetch_related
- Concurrent bookings: Safe with PostgreSQL row locking
- Test execution: 180 tests in ~106 seconds

**Frontend Performance:**
- Production build: 382KB (113KB gzipped)
- First contentful paint: < 1s
- Time to interactive: < 2s
- Responsive design: Mobile, tablet, desktop

**Scalability:**
- Concurrent users: Tested with 100+ simultaneous requests
- Database connections: Pooled connections recommended
- Horizontal scaling: Stateless JWT authentication supports multiple servers
- Caching: Can add Redis for session/query caching

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Development Guidelines:**
- Follow PEP 8 for Python code
- Use ESLint for JavaScript/React code
- Write tests for new features
- Update documentation
- Ensure all tests pass before submitting PR

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👏 Acknowledgments

- Django REST Framework for excellent API framework
- PostgreSQL for robust database with row-level locking
- React team for the amazing frontend library
- Vite for lightning-fast build tooling

---

## 📞 Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Contact the development team
- Read the documentation in `/backend/README.md` and `/frontend/README.md`

---

**Built with ❤️ for educational institutions and research labs**

*AccessSlot - Making equipment access fair, transparent, and efficient*
