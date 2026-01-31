"""MCP Schema Server - MySQL schema introspection tools for MCP.

This package provides an MCP server that exposes 5 schema introspection tools
for MySQL databases. All tools only access INFORMATION_SCHEMA metadata -
never user data tables.

Tools:
    - list_tables: Returns all table names in the database
    - get_table_schema: Returns detailed schema for a specific table
    - get_relationships: Returns foreign key relationships for a table
    - search_tables: Searches tables by keywords in names
    - get_column_stats: Returns metadata statistics for a column

Usage:
    # Run the server
    python -m mcp_schema_server.server

    # Or use the console script
    mcp-schema-server

Environment Variables:
    MCP_SERVER_NAME: Server name (default: "schema-only-mcp")
    MCP_LOG_LEVEL: Logging level (default: INFO)
    DATABASE_URL: MySQL connection URL (mysql+pymysql://user:pass@host/db)
    DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT: Alternative connection params
"""

__version__ = "0.1.0"

# Expose key components for programmatic use
from mcp_schema_server.tools.schema_tools import (
    list_tables,
    get_table_schema,
    get_relationships,
    search_tables,
    get_column_stats,
    SchemaToolError,
)
from mcp_schema_server.db.connection import (
    get_db_cursor,
    DatabaseConnectionError,
    DatabaseConfigError,
)

__all__ = [
    # Version
    "__version__",
    # Tools
    "list_tables",
    "get_table_schema",
    "get_relationships",
    "search_tables",
    "get_column_stats",
    # Exceptions
    "SchemaToolError",
    "DatabaseConnectionError",
    "DatabaseConfigError",
    # Database
    "get_db_cursor",
]
