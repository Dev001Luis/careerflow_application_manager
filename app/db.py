import os
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseConnectionSingleton:
    """
    Singleton class to manage a single MySQL connection instance throughout the application.
    Prevents redundant connections and ensures stability.
    """

    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnectionSingleton, cls).__new__(cls)
            try:
                cls._instance._connection = mysql.connector.connect(
                    host=os.getenv("MYSQL_HOST", "localhost"),
                    user=os.getenv("MYSQL_USER", "root"),
                    password=os.getenv("MYSQL_PASSWORD", ""),
                    database=os.getenv("MYSQL_DATABASE", "careerflow_db"),
                    port=int(os.getenv("MYSQL_PORT", 3306))
                )
                print("✅ MySQL connection established successfully.")
            except Error as e:
                print(f"❌ Error while connecting to MySQL: {e}")
                raise e
        return cls._instance

    def get_connection(self):
        """Return the active MySQL connection."""
        return self._connection


@contextmanager
def get_cursor():
    """
    Context manager that yields a MySQL cursor and handles commit/rollback logic.
    Ensures clean resource handling and prevents connection leaks.
    """
    connection = DatabaseConnectionSingleton().get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        yield cursor
        connection.commit()
    except Exception as e:
        connection.rollback()
        print(f"❌ Database error: {e}")
        raise
    finally:
        cursor.close()
