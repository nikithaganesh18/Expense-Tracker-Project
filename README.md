Cloud-Based Expense Tracker
Overview

Cloud-Based Expense Tracker is a DevOpsSec web application developed using Django and deployed on AWS EC2. It also enables users to have a centralized system to control daily expenses, spending patterns and budgets effectively. The system enables anyone to add expenses, classify them, and see the financial insights with the help of a dashboard.

The main characteristic of the application is the option to upload the receipt with the OCR processing. The users are allowed to upload the receipt pictures and the system automatically extracts key information such as total amount and date from the receipt. The results of such extractions are directly saved in the records of expenses and are displayed in the dashboard in real-time. The files uploaded are stored in AWS S3 which is secure and scalable and data durable.

SQLite is used to store the data in the development phase with prospects of upgrading to PostgreSQL in the production stage. Security and automation wise, the application is deployed through a CI/CD pipeline that is developed with GitHub Actions. When each time code goes to the main branch, it gets automatically tested, pip-audited and the quality of the code is checked with SonarCloud. Deployment to AWS is triggered only after all checks are successfully passed. Such a shift-left approach can be used to detect such problems as exposed Django SECRET KEY and dependency vulnerabilities early in development, not after deployment.
The application was developed using AWS Cloud9, a cloud-based development environment that provides built-in terminal access and seamless integration with AWS services.

Features

User Features
- User login and authentication
- Add expenses
- Categorize expenses
- View expense history
- Edit or delete expenses
- Track spending through dashboard
  
Expense Management

Stores (amount, category, date) Prevents invalid entries Live dashboard update.

Receipt Management

Image upload receipt image OCR-based extraction Secure storage with the help of AWS S3.

Technology Stack

Backend: Python (Django)
Frontend HTML, CSS (Django Templates)
Database: SQLite
Cloud: AWS EC2, AWS S3
Development Environment: AWS Cloud9  
Version Control: GitHub

DevSecOps Implementation

In this project, security is part of the development life cycle:

Security Tools

SonarCloud - Identifies code quality issues, bugs, and vulnerabilities.  
pip-audit - Finds vulnerabilities in project dependencies.  
Pylint - Performs static code analysis to detect coding issues, errors, and maintain coding standards.  
Coverage - Ensures testing and reliability.

Sensitive data such as the Django SECRET KEY is stored securely using environment variables instead of hardcoding in the source code, reducing the risk of exposure and improving application security.
CI/CD Pipeline

Tests and build process Automated testing and Continuous integration on GitHub actions Security scans before deploying Docker image creation and deployment.

Deployment

The application is hosted on a cloud 9 platform so that it can be accessed and scaled. The system is supported by AWS EC2 through the Docker and AWS S3 to store the uploaded receipt files safely.

Installation Guide
Clone Repository

git clone https://github.com/nikithaganesh18/Devopsec-Project

Create Virtual Environment

python -m venv venv

Activate Environment

source venv/bin/activate

Install Dependencies

pip install -r requirements.txt

Run Application

python manage.py migrate
python manage.py runserver

Deployment

AWS EC2
