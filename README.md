# stay-as-home-backend

A production-ready Django REST Framework backend API for the QuickStay Hotel Management and Booking Platform.

## 🚀 Key Features

- **🏨 Hotel & Room Management**: RESTful API endpoints for hotels, room types, pricing, amenities, and photo galleries.
- **📅 Booking Engine & Concurrency Locks**: Distributed in-memory locking preventing race condition double-bookings during concurrent checkouts.
- **🐘 Neon PostgreSQL Cloud Database**: Preconfigured with `dj-database-url`, SSL mode, and connection health checks.
- **💳 Cashfree Payment Gateway**: Order session creation and instant payment verification endpoints.
- **📬 Apache Kafka Event Streaming**: Event producer and background consumer for real-time domain event streaming.
- **🔒 Rate Limiting & Security**: Sliding window rate limiter protecting payment and booking endpoints.
- **📦 Cloud Deployment Ready**: Includes `Procfile`, `build.sh`, `runtime.txt`, and WhiteNoise static asset compression.

## 🛠️ Tech Stack

- **Python 3.10+ / 3.12**
- **Django 5.2 / 6.0**
- **Django REST Framework (DRF)**
- **Neon PostgreSQL** (`psycopg2-binary`, `dj-database-url`)
- **Apache Kafka** (`kafka-python-ng`)
- **Gunicorn & WhiteNoise**

## 🏁 Quick Start Guide

### 1. Clone the repository
```bash
git clone https://github.com/Abhishekkumar2590/stay-as-home-backend.git
cd stay-as-home-backend
```

### 2. Set up virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file (see `.env.example`):
```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend.vercel.app
FRONTEND_URL=http://localhost:5173

# Neon PostgreSQL
DATABASE_URL=postgresql://neondb_owner:YOUR_PASSWORD@ep-restless-frost-b5mdk9qy-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require
```

### 4. Run migrations & start server
```powershell
python manage.py migrate
python manage.py runserver
```

## 📜 License
MIT
