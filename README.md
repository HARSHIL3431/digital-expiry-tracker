# Digital Expiry Tracker

AI-assisted expiry management for food and medicine inventory using FastAPI + OCR + HTML/CSS/JS dashboard.

## Overview

Digital Expiry Tracker helps users:
- Scan and parse expiry dates from product images
- Track expiry timelines in a centralized inventory
- Detect expired and near-expiry products
- View alerts and risk indicators in a dashboard

## Current Tech Stack

- Backend: FastAPI, SQLAlchemy, Pydantic
- Auth: JWT (Bearer token)
- Database: SQLite (default), configurable with `DATABASE_URL`
- OCR: Tesseract / EasyOCR pipeline (optional heavy dependencies)
- Frontend: Vanilla HTML, CSS, JavaScript

## Project Structure

```text
digital-expiry-tracker/
├── app/
│   ├── api/v1/           # auth, products, scan routers
│   ├── core/             # config, dependencies, security
│   ├── schemas/          # request/response models
│   ├── services/         # expiry + OCR + scan pipeline
│   ├── utils/            # database + helpers
│   └── main.py           # FastAPI app entrypoint
├── frontend/
│   ├── assets/
│   └── pages/            # v1, login, register, dashboard
├── tests/
├── requirements.txt
└── README.md
```

## Demo Credentials

A demo user is created at app startup only when explicitly enabled:

- Email: `test@example.com`
- Password: value of `DEMO_USER_PASSWORD` in `.env`
- Enable flag: `ENABLE_DEMO_USER=true` (forced off when `APP_ENV=production`
  unless explicitly enabled, and creation is skipped when
  `DEMO_USER_PASSWORD` is empty)

Do not use the demo account in production. If a real credential was ever
committed to Git history, rotate it with its issuing service; removing it
from the latest commit alone does not revoke exposure.

## Setup (Windows)

1. Clone and enter project:
   ```bash
   git clone <your-repo-url>
   cd digital-expiry-tracker
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create environment file:
   ```bash
   copy .env.example .env
   ```

5. Run the app:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

6. Open:
   - API docs: `http://127.0.0.1:8000/docs`
   - Landing page: `http://127.0.0.1:8000/`
   - Login: `http://127.0.0.1:8000/app/login`
   - Dashboard: `http://127.0.0.1:8000/app/dashboard`

## Environment Variables

Configured via `.env` using `python-dotenv`:

```env
SECRET_KEY=replace-with-strong-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ADMIN_EMAIL=admin@det.com
DATABASE_URL=sqlite:///./expiry_tracker.db
ENABLE_DEMO_USER=true
DEMO_USER_PASSWORD=change-me-local-only
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
OCR_TIMEOUT_SECONDS=30
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

## API Summary

### Authentication
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/google/login`
- `GET /api/v1/auth/google/callback`
- `GET /api/v1/auth/me` (JWT required)
- `POST /api/v1/auth/upgrade` (JWT required)

## Google OAuth Setup (Free)

1. Create OAuth client in Google Cloud Console (Testing mode is fine for localhost).
2. Add authorized redirect URI:
   - `http://127.0.0.1:8000/api/v1/auth/google/callback`
3. Put generated credentials into `.env`:
   - `GOOGLE_CLIENT_ID=...`
   - `GOOGLE_CLIENT_SECRET=...`
4. On login page, click **Continue with Google**.

### Products (JWT required)
- `POST /api/v1/products/`
- `GET /api/v1/products/?page=1&limit=10&search=milk`
- `DELETE /api/v1/products/{product_id}`
- `GET /api/v1/products/expiry-status`
- `GET /api/v1/products/alerts?soon_days=7`

### Scan
- `POST /api/v1/scan/image`
- `GET /api/v1/scan/scans`

## Frontend Behavior

- Login stores JWT in `localStorage` under `auth_token`
- Dashboard validates token against `/api/v1/auth/me`
- Dashboard products use live API data (no static hardcoded rows)
- Product table supports search + pagination
- Expiry alerts (expired + expiring soon) are fetched from API
- In-page loading/success/error states are shown for key actions

## Running Tests

```bash
pytest -q
```

Focused unit tests:
```bash
pytest -q tests/test_expiry_service.py tests/test_expiry_parser.py
```

## Optional OCR Setup (Windows)

The API and tests do not require Tesseract. OCR endpoints return a clear `503`
error when the engine is unavailable.

1. Install OCR Python packages in the dedicated environment:

   ```bash
   conda activate expiry-ocr
   conda install -n expiry-ocr python=3.11
   pip install -r requirements-ocr.txt
   ```

2. Install the standalone Windows Tesseract OCR engine from the official
   Tesseract installer (for example the UB Mannheim build) or with Conda:

   ```bash
   conda activate expiry-ocr
   conda install -c conda-forge tesseract
   ```

   Do not rely on `pip`/Python packages alone; `pytesseract` and `easyocr`
   are wrappers around the actual engines. `python -m pip install pytesseract`
   does not install the Windows `tesseract.exe` executable.

3. Verify the standalone engine outside Python:

   ```powershell
   tesseract --version
   ```

4. If `tesseract` is not on `PATH`, copy the actual path from Windows and set it
   in `.env`:

   ```env
   TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
   OCR_TIMEOUT_SECONDS=30
   ```

   You can leave `TESSERACT_CMD` unset to let the application search common
   Windows installation locations and `PATH`.

5. PDF/image uploads and OCR requests have a maximum size and timeout as
   configured by the environment. Missing or corrupt OCR engines never return a
   successful OCR result.

## Deployment (Vercel Frontend + Render Backend)

This repository is prepared for a split deployment:

- Vercel serves the content under `frontend/` only.
- Render runs FastAPI from the repository root as a Python web service.
- Vercel rewrites (`vercel.json`) proxy `/api/*` and `/health` to the Render URL.

### Required environment variables

Configure these on Render and/or Vercel. Do not commit real values.

- `APP_ENV=production`
- `ENVIRONMENT=production`
- `SECRET_KEY`
- `ADMIN_EMAIL`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `DATABASE_URL` (use a durable location or external database)
- `CORS_ALLOWED_ORIGINS` (comma-separated exact origins, e.g. `https://your-app.vercel.app`)
- `FRONTEND_URL` (optional; can feed the comma-separated allowlist)
- `VERCEL_FRONTEND_URL` (optional alias for an allowlisted Vercel origin)
- `SESSION_COOKIE_SECURE=true`
- `ENABLE_DEMO_USER=false`
- `ENABLE_OCR=true` or `false`
- `TESSERACT_CMD=` (absolute path if Tesseract is not on `PATH`)
- `OCR_TIMEOUT_SECONDS=30`
- `MAX_UPLOAD_SIZE_BYTES=10485760`
- `UPLOAD_DIR=/var/data/uploads` on a persistent Render disk
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `TELEGRAM_BOT_TOKEN` only if Telegram notifications are used

### Vercel steps

1. Import the repository in Vercel.
2. Keep the root directory as the project root; `vercel.json` sets `outputDirectory` to `frontend`.
3. Set framework preset to Other / static if Vercel asks.
4. Replace `https://YOUR_RENDER_SERVICE.onrender.com` in `vercel.json` with the real Render service URL, or configure the same rewrite manually in Vercel.
5. Configure any Vercel build settings as needed; no frontend build command is required.
6. Redeploy Vercel after the Render service URL is finalized.

### Render steps

1. Create a Python web service from the repository.
2. Build command: `pip install -r requirements.txt`; add `pip install -r requirements-ocr.txt` if OCR and Tesseract are required.
3. Start command:

   ```text
   mkdir -p /var/data/uploads && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

4. Set `healthCheckPath` to `/health`.
5. Use a persistent disk at `/var/data` for SQLite and uploads, or switch `DATABASE_URL` to an external database after approving that migration.
6. Install Tesseract in the Render build environment if OCR is enabled.
7. Set all required environment variables; use a strong auto-generated `SECRET_KEY`.
8. Update `GOOGLE_REDIRECT_URI` to the final callback route, such as `https://your-app.vercel.app/api/v1/auth/google/callback`.

### Data persistence

SQLite is already configurable through `DATABASE_URL`. For a private or free Render service, writing SQLite to the local container is not durable, and Render upgrades/redeploys can lose data and uploaded files. Two safe options are:

- Attach a paid Render persistent disk and use `sqlite:////var/data/expiry_tracker.db` with `UPLOAD_DIR=/var/data/uploads`.
- Later migrate to an external managed database. Do not run that migration in this code without approval; the current engine, models, user data, authentication, sessions, and upload routes are intended to remain unchanged.

OCR is also optional. The backend checks OCR/engine availability and returns a safe `503` error if Tesseract or another required dependency is unavailable; it will not silently disable a successful scan.

## Notes

- OCR endpoints require OCR-related dependencies (OpenCV, Tesseract, EasyOCR) to be installed.
- For production, set a strong `SECRET_KEY`, secure token storage, and proper DB engine settings.
- Run `python -m compileall -q .` and `pytest` after changing deployment configuration code.
