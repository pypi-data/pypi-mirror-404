"""MySQL database connection module for MCP schema server.

This module provides database connectivity specifically for accessing
MySQL INFORMATION_SCHEMA metadata. It does NOT access user data.

Privacy Note: This module is designed to ONLY query INFORMATION_SCHEMA
for table structures, column definitions, and metadata. No user data
is ever accessed or returned.
"""

import os
import re
from contextlib import contextmanager
from typing import Dict, Any, Optional, Generator
from urllib.parse import urlparse

import pymysql
from pymysql import Connection
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class DatabaseConfigError(Exception):
    """Raised when database configuration is invalid or missing."""
    pass


class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""
    pass


def _parse_database_url(url: str) -> Dict[str, Any]:
    """Parse DATABASE_URL into connection parameters.
    
    Expected format: mysql+pymysql://user:password@host:port/dbname
    
    Args:
        url: Database connection URL
        
    Returns:
        Dictionary with connection parameters
        
    Raises:
        DatabaseConfigError: If URL format is invalid
    """
    # Handle mysql+pymysql:// prefix
    if url.startswith('mysql+pymysql://'):
        url = url.replace('mysql+pymysql://', 'mysql://')
    elif url.startswith('mysql://'):
        pass
    else:
        raise DatabaseConfigError(
            f"Invalid DATABASE_URL format. Expected mysql+pymysql:// or mysql://, got: {url[:20]}..."
        )
    
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise DatabaseConfigError(f"Failed to parse DATABASE_URL: {e}")
    
    # Extract components
    config = {
        'host': parsed.hostname or 'localhost',
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/') if parsed.path else None,
    }
    
    if parsed.port:
        config['port'] = parsed.port
    
    # Validate required fields
    if not config['user']:
        raise DatabaseConfigError("DATABASE_URL missing username")
    if not config['password']:
        raise DatabaseConfigError("DATABASE_URL missing password")
    if not config['database']:
        raise DatabaseConfigError("DATABASE_URL missing database name")
    
    return config


def get_db_config() -> Dict[str, Any]:
    """Get database configuration from environment variables.
    
    Configuration priority:
    1. DATABASE_URL (if set)
    2. Individual DB_* variables
    
    Required environment variables (if DATABASE_URL not set):
        - DB_NAME: Database name
        - DB_USER: Database username
        - DB_PASSWORD: Database password
    
    Optional environment variables:
        - DB_HOST: Database host (default: localhost)
        - DB_PORT: Database port (default: 3306)
    
    Returns:
        Dictionary with connection parameters
        
    Raises:
        DatabaseConfigError: If required configuration is missing
    """
    # Check for DATABASE_URL first
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return _parse_database_url(database_url)
    
    # Use individual environment variables
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
    }
    
    # Validate required fields
    missing = []
    if not config['database']:
        missing.append('DB_NAME')
    if not config['user']:
        missing.append('DB_USER')
    if not config['password']:
        missing.append('DB_PASSWORD')
    
    if missing:
        raise DatabaseConfigError(
            f"Missing required database configuration: {', '.join(missing)}. "
            "Set these environment variables or provide DATABASE_URL."
        )
    
    return config


def get_db_connection() -> Connection:
    """Create and return a new MySQL database connection.
    
    Returns:
        PyMySQL Connection object
        
    Raises:
        DatabaseConfigError: If configuration is invalid
        DatabaseConnectionError: If connection fails
    """
    config = get_db_config()
    
    try:
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            charset='utf8mb4',
            cursorclass=DictCursor,
            # Connection pool settings
            autocommit=True,
        )
        return connection
    except pymysql.Error as e:
        raise DatabaseConnectionError(
            f"Failed to connect to database: {e}"
        ) from e
    except Exception as e:
        raise DatabaseConnectionError(
            f"Unexpected error connecting to database: {e}"
        ) from e


def test_connection() -> bool:
    """Test if database connection works.
    
    Returns:
        True if connection succeeds, False otherwise
    """
    connection = None
    try:
        connection = get_db_connection()
        # Execute a simple INFORMATION_SCHEMA query to verify access
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM INFORMATION_SCHEMA.TABLES LIMIT 1")
            cursor.fetchone()
        return True
    except Exception:
        return False
    finally:
        if connection:
            try:
                connection.close()
            except Exception:
                pass


class DatabaseConnection:
    """Context manager for database connections.
    
    Usage:
        with DatabaseConnection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT ... FROM INFORMATION_SCHEMA.TABLES")
                results = cursor.fetchall()
    
    The connection is automatically closed when exiting the context.
    """
    
    def __init__(self):
        self._connection: Optional[Connection] = None
    
    def __enter__(self) -> Connection:
        """Enter context and return connection."""
        self._connection = get_db_connection()
        return self._connection
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and close connection."""
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                # Suppress errors during cleanup
                pass
            finally:
                self._connection = None


@contextmanager
def get_db_cursor() -> Generator:
    """Get a database cursor as a context manager.
    
    Usage:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT ... FROM INFORMATION_SCHEMA.TABLES")
            results = cursor.fetchall()
    
    Yields:
        PyMySQL DictCursor
        
    Raises:
        DatabaseConfigError: If configuration is invalid
        DatabaseConnectionError: If connection fails
    """
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            yield cursor
    finally:
        if connection:
            try:
                connection.close()
            except Exception:
                pass
