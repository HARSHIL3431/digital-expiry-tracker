# 🚀 Digital Expiry Tracker

### AI-Assisted Expiry Management for Food & Medicine

---

## 📌 What is Digital Expiry Tracker?

**Digital Expiry Tracker** is a smart web application that helps users track the expiry dates of **food and medicine items** using **OCR (Optical Character Recognition)** and automated reminders.

It prevents health risks caused by expired products and reduces unnecessary wastage by providing timely alerts and a centralized digital inventory.

> **Simply put:**  
> Scan → Track → Get reminded → Stay safe.

---

## ❌ The Problem

Expiry management today is mostly manual and inefficient:

- ⏳ People forget expiry dates
- 🗑️ Food and medicines get wasted
- ⚠️ Health risks due to expired consumption
- 📄 No centralized digital tracking
- 😕 Manual checking is time-consuming

---

## ✅ Our Solution

**Digital Expiry Tracker provides:**

1. 📷 **OCR-Based Scanning** – Extract expiry dates from images  
2. 📦 **Digital Inventory** – Manage all products in one place  
3. ⏰ **Automated Reminders** – Alerts before items expire  
4. 📊 **Expiry Dashboard** – Upcoming & expired item tracking  
5. 🔐 **Reliable Backend APIs** – Secure and validated data handling  

---

## 🧠 How OCR Works

1. User uploads product image  
2. Image is preprocessed (resize, grayscale)  
3. OCR engine extracts text  
4. Expiry date is detected using pattern matching  
5. Date is stored in database  

> OCR integration is designed to be **modular and scalable**.

---

## 🔄 How It Works (User Journey)

Add Product (Image / Manual Entry)
↓

OCR extracts expiry date
↓

Backend validates data
↓

Product stored in database
↓

System monitors expiry timeline
↓

User receives reminder before expiry


---

## 🎯 Core Features

### 👤 For Users
- ✅ Add food & medicine items
- ✅ OCR-based expiry detection
- ✅ Expiry countdown tracking
- ✅ Reminder notifications
- ✅ Simple & clean interface

### 🛠️ For System
- ✅ Product CRUD APIs
- ✅ Input validation
- ✅ Error handling
- ✅ Scalable architecture

---

## 🧱 Technology Stack

| Component | Technology |
|---------|-----------|
| Backend | FastAPI (Python) |
| OCR | Tesseract OCR |
| Image Processing | OpenCV |
| Database | SQLite / PostgreSQL |
| API Docs | Swagger (FastAPI) |
| Tools | Git, GitHub, Thunder Client |

---

## 📂 Project Structure

digital-expiry-tracker/
│
├── backend/
│ ├── main.py
│ ├── routers/
│ ├── models/
│ ├── schemas/
│ ├── services/
│ └── requirements.txt
│
├── docs/
│ └── workflow.md
│
├── README.md
└── .gitignore


---

## ▶️ Setup & Installation

### 1️⃣ Clone Repository
```bash
git clone https://github.com/your-username/digital-expiry-tracker.git
cd digital-expiry-tracker

2️⃣ Create Virtual Environment
python -m venv venv
venv\Scripts\activate   # Windows

3️⃣ Install Dependencies
pip install -r backend/requirements.txt

4️⃣ Run Backend Server
uvicorn backend.main:app --reload or
python -m uvicorn app.main:app --reload

5️⃣ Open API Docs
http://127.0.0.1:8000/docs

API Endpoints
GET    /products
POST   /products
PUT    /products/{id}
DELETE /products/{id}

Test using:

Thunder Client (VS Code)

Postman

| Metric          | Before  | After     |
| --------------- | ------- | --------- |
| Expiry Tracking | Manual  | Automated |
| Food Wastage    | High    | Reduced   |
| Health Risk     | Present | Minimized |
| User Effort     | High    | Low       |

🚀 Future Enhancements
Short Term

📧 Email reminders

📱 Mobile-friendly UI

Medium Term

🔔 Push notifications

📈 Consumption analytics

Long Term

🤖 AI-based expiry prediction

☁️ Cloud deployment

🧠 Smart shopping suggestions

🏆 Why This Project Stands Out

✅ Real-world problem solving

✅ OCR + Backend integration

✅ Clean API architecture

✅ Suitable for hackathons & academics

✅ Scalable for production use

👨‍💻 Author

Harshil Thakkar
B.Tech – Artificial Intelligence & Machine Learning

⭐ Support

If you like this project:

⭐ Star the repository

🍴 Fork it

🧠 Share feedback

## CodeRabbit Integration
This change is made to test CodeRabbit AI code review.
