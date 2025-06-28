# 🦷 Dental Insurance Automation App

This Django-based application automates the dental insurance claim process for common dental procedures such as crowns, occlusal guards, and scaling and root planing (SRP). 
It streamlines documentation, generates clinical notes, attaches x-rays and perio charts, and submits insurance claims via email — all in a few clicks.

## 🚀 Features

- **Patient Management System (PMS)**: Secure login, patient lookup, and treatment history.
- **Crown Recommendation**: Recommends and submits insurance claims for D2740 with x-ray and clinical note.
- **Occlusal Guard Workflow**: Automatically generates clinical note and emails pre-authorization for bruxism-related appliances (D9944).
- **SRP Workflow**: Submits SRP pre-auth with placeholder perio chart and x-ray.
- **Dashboard View**: Real-time tracking of all submitted claims with status indicators.
- **Email Integration**: Sends completed claims as PDF attachments to the designated insurance processor.

## 🛠️ Technologies Used

- Python 3.12
- Django
- SQLite (development)
- Bootstrap 5 (UI)
- ReportLab (PDF generation)
- Django Email Backend
