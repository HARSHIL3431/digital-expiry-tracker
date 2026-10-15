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

## Notes

- OCR endpoints require OCR-related dependencies (OpenCV, Tesseract, EasyOCR) to be installed.
- For production, set a strong `SECRET_KEY`, secure token storage, and proper DB engine settings.
