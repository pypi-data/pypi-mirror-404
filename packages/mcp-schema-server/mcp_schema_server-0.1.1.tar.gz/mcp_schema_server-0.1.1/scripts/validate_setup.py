#!/usr/bin/env python3
"""
Validation script for MCP Schema Server setup.

This script tests:
1. Database connectivity
2. INFORMATION_SCHEMA access
3. All tool functions
4. Environment configuration

Usage:
    python scripts/validate_setup.py

Exit codes:
    0 - All tests passed
    1 - Configuration error
    2 - Database connection error
    3 - Tool functionality error
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_schema_server.db.connection import (
    get_db_config,
    test_connection,
    DatabaseConfigError,
    DatabaseConnectionError,
)
from mcp_schema_server.tools.schema_tools import (
    list_tables,
    get_table_schema,
    get_relationships,
    search_tables,
    get_column_stats,
    SchemaToolError,
)


def print_header(title: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"  ✓ {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"  ✗ {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"  ⚠ {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"  ℹ {message}")


def check_environment() -> bool:
    """Check if required environment variables are set."""
    print_header("Environment Configuration")
    
    # Check for .env file
    env_file = Path(".env")
    if env_file.exists():
        print_success("Found .env file")
    else:
        print_warning("No .env file found (using system environment variables)")
    
    # Check configuration
    try:
        config = get_db_config()
        print_success("Database configuration is valid")
        print_info(f"Host: {config['host']}")
        print_info(f"Port: {config['port']}")
        print_info(f"Database: {config['database']}")
        print_info(f"User: {config['user']}")
        # Don't print password!
        return True
    except DatabaseConfigError as e:
        print_error(f"Configuration error: {e}")
        print("\n  Please ensure you have set the required environment variables:")
        print("    - DB_HOST (optional, default: localhost)")
        print("    - DB_PORT (optional, default: 3306)")
        print("    - DB_NAME (required)")
        print("    - DB_USER (required)")
        print("    - DB_PASSWORD (required)")
        print("  Or use DATABASE_URL instead")
        return False


def check_database_connection() -> bool:
    """Test database connectivity."""
    print_header("Database Connection")
    
    try:
        if test_connection():
            print_success("Successfully connected to database")
            return True
        else:
            print_error("Failed to connect to database")
            return False
    except DatabaseConnectionError as e:
        print_error(f"Connection error: {e}")
        print("\n  Troubleshooting tips:")
        print("    1. Verify MySQL server is running")
        print("    2. Check host and port settings")
        print("    3. Verify username and password")
        print("    4. Ensure database exists")
        print("    5. Check firewall settings")
        return False


def check_tool_list_tables() -> bool:
    """Test list_tables tool."""
    print_header("Tool Test: list_tables")
    
    try:
        result = list_tables()
        tables = result.get("tables", [])
        print_success(f"Retrieved {len(tables)} tables")
        
        if tables:
            print_info(f"First 5 tables: {', '.join(tables[:5])}")
            if len(tables) > 5:
                print_info(f"... and {len(tables) - 5} more")
        
        return True
    except SchemaToolError as e:
        print_error(f"Tool error: {e}")
        return False


def check_tool_get_table_schema(tables: list) -> bool:
    """Test get_table_schema tool."""
    print_header("Tool Test: get_table_schema")
    
    if not tables:
        print_warning("No tables available to test")
        return True
    
    test_table = tables[0]
    try:
        result = get_table_schema(test_table)
        columns = result.get("columns", [])
        primary_key = result.get("primary_key", [])
        
        print_success(f"Retrieved schema for '{test_table}'")
        print_info(f"Columns: {len(columns)}")
        print_info(f"Primary Key: {', '.join(primary_key) if primary_key else 'None'}")
        
        if columns:
            print_info(f"First column: {columns[0]['name']} ({columns[0]['type']})")
        
        return True
    except SchemaToolError as e:
        print_error(f"Tool error: {e}")
        return False


def check_tool_get_relationships(tables: list) -> bool:
    """Test get_relationships tool."""
    print_header("Tool Test: get_relationships")
    
    if not tables:
        print_warning("No tables available to test")
        return True
    
    test_table = tables[0]
    try:
        result = get_relationships(test_table)
        foreign_keys = result.get("foreign_keys", [])
        referenced_by = result.get("referenced_by", [])
        
        print_success(f"Retrieved relationships for '{test_table}'")
        print_info(f"Foreign Keys: {len(foreign_keys)}")
        print_info(f"Referenced By: {len(referenced_by)}")
        
        return True
    except SchemaToolError as e:
        print_error(f"Tool error: {e}")
        return False


def check_tool_search_tables() -> bool:
    """Test search_tables tool."""
    print_header("Tool Test: search_tables")
    
    try:
        # Search for common terms
        search_terms = ["user", "order", "product", "id"]
        found_results = False
        
        for term in search_terms:
            result = search_tables(term)
            results = result.get("results", [])
            if results:
                print_success(f"Search for '{term}' returned {len(results)} results")
                found_results = True
                break
        
        if not found_results:
            print_warning("No search results found (this may be normal for empty databases)")
        
        return True
    except SchemaToolError as e:
        print_error(f"Tool error: {e}")
        return False


def check_tool_get_column_stats(tables: list) -> bool:
    """Test get_column_stats tool."""
    print_header("Tool Test: get_column_stats")
    
    if not tables:
        print_warning("No tables available to test")
        return True
    
    test_table = tables[0]
    
    try:
        # Get schema to find a column
        schema = get_table_schema(test_table)
        columns = schema.get("columns", [])
        
        if not columns:
            print_warning(f"Table '{test_table}' has no columns")
            return True
        
        test_column = columns[0]["name"]
        result = get_column_stats(test_table, test_column)
        
        print_success(f"Retrieved stats for '{test_table}.{test_column}'")
        print_info(f"Type: {result['type']}")
        print_info(f"Nullable: {result['nullable']}")
        print_info(f"Has Index: {result['has_index']}")
        
        return True
    except SchemaToolError as e:
        print_error(f"Tool error: {e}")
        return False


def check_security() -> bool:
    """Check security-related configurations."""
    print_header("Security Checks")
    
    # Check if .env file exists and has proper permissions
    env_file = Path(".env")
    if env_file.exists():
        import stat
        mode = env_file.stat().st_mode
        
        # Check if file is readable by others (Unix-like systems)
        if hasattr(stat, 'S_IRGRP') and hasattr(stat, 'S_IROTH'):
            if mode & stat.S_IRGRP or mode & stat.S_IROTH:
                print_warning(".env file is readable by group/others")
                print_info("Consider running: chmod 600 .env")
            else:
                print_success(".env file has restricted permissions")
    
    # Check for sensitive files in git
    gitignore = Path(".gitignore")
    if gitignore.exists():
        content = gitignore.read_text()
        if ".env" in content:
            print_success(".env is in .gitignore")
        else:
            print_warning(".env is NOT in .gitignore")
            print_info("Add '.env' to .gitignore to prevent credential leaks")
    else:
        print_warning("No .gitignore file found")
    
    return True


def main():
    """Run all validation checks."""
    print("MCP Schema Server - Setup Validation")
    print("=" * 60)
    
    all_passed = True
    
    # Check environment configuration
    if not check_environment():
        print("\n" + "=" * 60)
        print("VALIDATION FAILED: Configuration error")
        sys.exit(1)
    
    # Check database connection
    if not check_database_connection():
        print("\n" + "=" * 60)
        print("VALIDATION FAILED: Database connection error")
        sys.exit(2)
    
    # Get list of tables for subsequent tests
    tables = []
    try:
        tables = list_tables().get("tables", [])
    except Exception:
        pass
    
    # Test all tools
    tool_tests = [
        ("list_tables", check_tool_list_tables),
        ("get_table_schema", lambda: check_tool_get_table_schema(tables)),
        ("get_relationships", lambda: check_tool_get_relationships(tables)),
        ("search_tables", check_tool_search_tables),
        ("get_column_stats", lambda: check_tool_get_column_stats(tables)),
    ]
    
    for name, test_func in tool_tests:
        if not test_func():
            all_passed = False
    
    # Security checks
    check_security()
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("VALIDATION PASSED ✓")
        print("\nYour MCP Schema Server is ready to use!")
        print("\nNext steps:")
        print("  1. Configure your MCP client (see examples/mcp_config.json)")
        print("  2. Start the server:")
        print("     - With uvx (no install): uvx mcp-schema-server")
        print("     - With python module: python -m mcp_schema_server.server")
        print("  3. Run usage examples: python examples/usage_example.py")
        sys.exit(0)
    else:
        print("VALIDATION FAILED ✗")
        print("\nSome tests failed. Please review the errors above.")
        sys.exit(3)


if __name__ == "__main__":
    main()
