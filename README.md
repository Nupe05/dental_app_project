# 🦷 Dental Insurance Automation App

This Django-based application automates the dental insurance claim process for common dental procedures like **crowns**, **occlusal guards**, and **scaling and root planing (SRP)**. It streamlines documentation, generates clinical notes, analyzes x-rays using AI, and submits insurance claims via email — all in a few clicks.

---

## 🚀 Features

- **🔐 Patient Management System (PMS)**
  - Secure login system
  - Patient lookup
  - View and update treatment history

- **👑 Crown Recommendation (D2740)**
  - AI-powered detection of abscesses using dental x-rays
  - Auto-generates clinical note and attaches latest x-ray
  - Submits PDF claim via email

- **🛡️ Occlusal Guard Workflow (D9944)**
  - Clinical note auto-filled for bruxism
  - Generates and sends pre-authorization PDF via email

- **🪥 SRP Treatment Flow**
  - Supports quadrant-based SRP (D4341/D4342)
  - Placeholder perio chart and x-ray included in email submission

- **📊 Dashboard View**
  - Tracks all claims and recommendations
  - Displays status and timestamps

- **📧 Email Integration**
  - Sends all completed claims as PDF attachments to a designated insurance processor

---

## 🧠 AI Integration

- **Abscess Detection Model**
  - Built with **FastAI** and **PyTorch**
  - Uses latest uploaded x-ray to classify as **Healthy** or **Abscessed**
  - Confidence score displayed before submitting treatment

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12, Django 5.2
- **Frontend**: Bootstrap 5, HTML/CSS
- **PDF Generation**: ReportLab
- **Image Processing / AI**: FastAI 2.7, PyTorch 2.0
- **Database**: SQLite (for development)
- **Authentication**: Django auth + DRF token auth (for API)
- **Deployment-ready**: Compatible with Heroku or Docker

---


