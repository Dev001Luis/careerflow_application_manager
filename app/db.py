# app/db.py
"""
Database connection helper.

Provides a DBConnection singleton that opens a single mysql.connector connection for the
application lifetime (can be adjusted later for connection pooling). Also provides a
context manager `get_cursor()` that yields a cursor and commits on successful exit.

We use long descriptive names and docstrings for clarity.
"""

import os
from contextlib import contextmanager
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

class DatabaseConnectionSingleton:
    """
    Singleton wrapper around a MySQL connection.
    Usage:
        db_singleton = DatabaseConnectionSingleton()
        connection = db_singleton.get_connection()
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnectionSingleton, cls).__new__(cls)
            cls._instance._connection = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "")
            )
        return cls._instance

    def get_connection(self):
        """Return the underlying mysql.connector connection object."""
        return self._connection


@contextmanager
def get_cursor(dictionary: bool = True):
    """
    Context manager that yields a cursor and commits the connection on exit.
    Example:
        with get_cursor() as cursor:
            cursor.execute("SELECT ...")
            rows = cursor.fetchall()
    """
    connection = DatabaseConnectionSingleton().get_connection()
    cursor = connection.cursor(dictionary=dictionary)
    try:
        yield cursor
        connection.commit()
    finally:
        cursor.close()
