# app/__init__.py
"""
Application package initializer.

We keep this minimal: create Flask app instance and expose it for import.
"""

from flask import Flask
from app.db import get_cursor

def create_application():
    """
    Application factory: returns a configured Flask application instance.
    We keep initialization light; DB initialization (creating tables) is done
    here at startup for development convenience.
    """
    application = Flask(__name__)
    application.secret_key = "replace_this_with_a_secure_random_value"

    # initialize database tables if not present (development convenience)
    _initialize_database_tables()

    return application

def _initialize_database_tables():
    """
    Create jobs table if it does not exist yet.
    For Day 1 we keep a simple schema. In production move migrations to Alembic.
    """
    jobs_table_query = """
    CREATE TABLE IF NOT EXISTS jobs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        company VARCHAR(255),
        link TEXT,
        category VARCHAR(100),
        status ENUM('Saved','Applied','Interview','Rejected','Offer') DEFAULT 'Saved',
        applied_date DATE,
        interview_date DATE,
        notes TEXT
    )
    """
    with get_cursor() as cursor:
        cursor.execute(jobs_table_query)
