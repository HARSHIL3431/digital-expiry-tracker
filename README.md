🧾 Digital Expiry Tracker

Digital Expiry Tracker is a personal-use web application that helps users track expiry dates of food and medicine items using OCR and automated reminders, reducing health risks and wastage.

📖 Table of Contents

Overview

Features

Tech Stack

Workflow Diagram

Project Structure

Setup & Installation

API Usage

Future Scope

🔍 Overview

Managing expiry dates manually often leads to forgotten food items, expired medicines, and unnecessary waste.
This project solves that problem by digitizing expiry tracking through a backend-first, scalable architecture.

The system allows users to:

Store product expiry data

Extract expiry dates from images (OCR)

Receive alerts before expiration

✨ Features

OCR-based expiry date extraction

Product CRUD APIs

Expiry monitoring logic

Input validation & error handling

API documentation with Swagger

Scalable backend architecture

🛠 Tech Stack

Backend

Python

FastAPI

Uvicorn

Pydantic

OCR (Planned)

Tesseract OCR

OpenCV

Database

SQLite (development)

PostgreSQL (production)

Tools

Git & GitHub

Thunder Client (VS Code)

🔄 Workflow Diagram

This diagram will render automatically on GitHub (no images required).

flowchart TD
    A[User] --> B[Frontend / API Client]
    B --> C[Image Upload / Manual Entry]
    C --> D[OCR Engine]
    D --> E[Expiry Date Extraction]
    E --> F[FastAPI Backend]
    F --> G[Database]
    G --> H[Expiry Monitoring Service]
    H --> I[User Notification]

📂 Project Structure
digital-expiry-tracker/
│
├── backend/
│   ├── main.py
│   ├── routers/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── requirements.txt
│
├── docs/
│   └── workflow.md
│
├── README.md
└── .gitignore

▶️ Setup & Installation
Clone Repository
git clone https://github.com/your-username/digital-expiry-tracker.git
cd digital-expiry-tracker

Create Virtual Environment
python -m venv venv
venv\Scripts\activate   # Windows

Install Dependencies
pip install -r backend/requirements.txt

Run Server
uvicorn backend.main:app --reload

API Docs
http://127.0.0.1:8000/docs

🔌 API Usage

Example endpoints:

GET    /products
POST   /products
PUT    /products/{id}
DELETE /products/{id}


Test using:

Thunder Client (VS Code)

Postman

🚀 Future Scope

Email & push notifications

Mobile app integration

AI-based expiry prediction

Consumption analytics

Cloud deployment

👤 Author

Harshil Thakkar
B.Tech – Artificial Intelligence & Machine Learning

⭐ Support

If you like this project:

Star ⭐ the repository

Fork 🍴 and contribute