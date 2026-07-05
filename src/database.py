"""Database.py -> Database connection"""


# --------------------------------------------------------------------
# Importing required libraries
# --------------------------------------------------------------------

import os # To read and write files in system
from dotenv import load_dotenv # To get required data from .env file
from sqlalchemy import create_engine, text # For establishing connection to the database
from sqlalchemy.exc import SQLAlchemyError # To Handle errors  
from urllib.parse import quote_plus # To handle special characters
# -------------------------------------------------------------------


# Reading .env file

load_dotenv()

# ------------------------------------------------------------------
# Establishing connection to the database
# ------------------------------------------------------------------

DB_HOST = os.getenv("MySQL_HOST", 'localhost')
DB_USER = os.getenv("MySQL_USER", "root")
DB_PASSWORD = quote_plus(os.getenv("MySQL_PASSWORD", ""))
DB_NAME = os.getenv("My_DB", "healthcare_DB")


def get_engine():
    connection_url = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"
    return create_engine(
        connection_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        )



# -------------------------------------------------------------------
# Checking the connection
# -------------------------------------------------------------------

def test_connection():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
        print("Connection successful.")
        print("Tables: ",tables)
        return True
    except SQLAlchemyError as e:
        print("Could not connect to the database.")
        print(str(e))
        return False


if __name__ == "__main__":
    test_connection()





