"""
database.py
-----------
Handles the MySQL connection and loads data from the database views
into pandas DataFrames at application startup.

The data is cached in memory so we don't hit the database on every request.
"""

import os
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load credentials from the .env file
load_dotenv()

# ──────────────────────────────────────────────
# Build the database connection engine
# ──────────────────────────────────────────────

def get_engine():
    """Create and return a SQLAlchemy engine using .env credentials."""
    host     = os.getenv("HOST")
    port     = os.getenv("PORT", "3306")
    db       = os.getenv("DB")
    user     = os.getenv("USER")
    # quote_plus encodes special characters in the password (like & ! :)
    password = quote_plus(os.getenv("PASSWORD", ""))

    connection_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
    return create_engine(connection_url, pool_pre_ping=True)


# ──────────────────────────────────────────────
# In-memory cache — loaded once at startup
# ──────────────────────────────────────────────

_data_cache: dict = {}


def load_all_data() -> None:
    """
    Called once when FastAPI starts.
    Loads the main view vw_harvest_full into memory.
    This is the single source of truth for all 8 endpoints.
    """
    engine = get_engine()

    print("⏳ Loading data from database...")

    _data_cache["harvest"] = pd.read_sql("SELECT * FROM vw_harvest_full", engine)

    # Print column names so you can verify they match what we expect
    print("✅ Data loaded successfully!")
    print(f"   Rows: {len(_data_cache['harvest'])}")
    print(f"   Columns: {list(_data_cache['harvest'].columns)}")


def get_harvest_df() -> pd.DataFrame:
    """
    Returns the main DataFrame loaded at startup.
    All endpoint functions call this to get their data.
    """
    return _data_cache["harvest"].copy()
