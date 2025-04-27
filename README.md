# School-DBMS
This web-based school database management system, built with Flask, manages student records, admissions, and staff data. It features secure login, admin/user dashboards, and a responsive design. Built with Python, SQL (SSMS), Bootstrap, and custom CSS, it streamlines school data management.

## Requirements

- Python 3.8+
- Flask
- SQLAlchemy
- Flask-SQLAlchemy
- Flask-Login
- SSMS

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd flask_school_db
python -m venv venv
venv\Scripts\activate  # On Windows
pip install flask flask-sqlalchemy flask-login
python create_admin_table.sql
python create_admin.py
python run.py
```
Usage
Access the application at http://localhost:5000
Login with admin credentials:
Username: admin@school.com
Password: admin123 (default, change after first login)

