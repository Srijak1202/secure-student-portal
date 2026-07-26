# Secure Academic Progress & Risk Monitoring System

## Overview
A Flask-based secure web application designed for universities to monitor student academic progress, attendance, and risk levels. The system features strict security implementation including Role-Based Access Control (RBAC), Encryption, and Digital Signatures.

## Features by Role
-   **Student**: View secure academic records, attendance graphs, and risk analysis (Attendance/Marks). Two-row CGPA/SGPA display.
-   **Faculty**: Upload marks (Encrypted), log mentoring sessions, and view at-risk student lists.
-   **Admin (HOD)**: User management, system health monitoring, and CSV Risk Report generation.

## Security Implementations
1.  **Authentication**:
    -   Secure Login with Hashed Passwords (Salted SHA256).
    -   Multi-Factor Authentication (OTP simulation).
    -   Controlled Registration: Students (Public), Faculty (Admin-only).
2.  **Authorization**:
    -   Role-Based Access Control (RBAC) enforced via `@role_required`.
    -   Access Control Matrix implemented for Admin, Faculty, Student, Parent.
3.  **Data Protection**:
    -   **Encryption**: AES/Fernet encryption for Marks and Risk Scores.
    -   **Integrity**: HMAC-SHA256 Digital Signatures to detect data tampering.
    -   **Encoding**: Base64 encoding for secure data transport.

## Setup Instructions

### Prerequisites
-   Python 3.8+
-   Virtual Environment (Recommended)

### Installation
1.  Clone the repository.
2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Database Initialization
The system uses SQLite. To reset and seed the database with sample data (Admin, Faculty, Student, Parent):
```bash
python init_db.py
```

### Running the Application
```bash
python app.py
```
Access the application at: `http://127.0.0.1:5000`

## Default Credentials
| Role | Username | Password |
| :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` |
| **Faculty** | `faculty` | `faculty123` |
| **Student** | `student` | `student123` |

## Project Structure
-   `app.py`: Main application entry point.
-   `models.py`: Database models (User, Profile, AcademicRecord, etc.).
-   `routes/`: Blueprints for each role (`auth`, `admin`, `faculty`, `student`, `parent`).
-   `utils/`: Security & Logic helpers (`crypto.py`, `auth.py`, `risk_engine.py`).
-   `templates/`: HTML frontends.
