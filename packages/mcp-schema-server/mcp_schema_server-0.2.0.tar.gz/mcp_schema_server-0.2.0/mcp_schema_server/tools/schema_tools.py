"""Schema query tools for MCP schema server.

This module provides tools for querying MySQL INFORMATION_SCHEMA metadata.
All tools only access schema information - never user data tables.

Privacy Note: These tools are designed to ONLY query INFORMATION_SCHEMA
for table structures, column definitions, and metadata. No user data
is ever accessed or returned.
"""

from typing import Dict, Any, List, Optional

from mcp_schema_server.db.connection import get_db_cursor, DatabaseConnectionError
from mcp_schema_server.config import should_ignore_table


class SchemaToolError(Exception):
    """Raised when a schema tool operation fails."""
    pass


def _get_current_database() -> str:
    """Get the name of the current database.
    
    Returns:
        Current database name
        
    Raises:
        SchemaToolError: If unable to get database name
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT DATABASE()")
            result = cursor.fetchone()
            if result and result.get("DATABASE()"):
                return result["DATABASE()"]
            raise SchemaToolError("Unable to determine current database")
    except DatabaseConnectionError as e:
        raise SchemaToolError(f"Database connection error: {e}") from e
    except Exception as e:
        raise SchemaToolError(f"Failed to get current database: {e}") from e


def _validate_table_name(table_name: str) -> None:
    """Validate table name to prevent SQL injection.
    
    Args:
        table_name: Table name to validate
        
    Raises:
        SchemaToolError: If table name is invalid
    """
    if not table_name:
        raise SchemaToolError("Table name cannot be empty")
    
    # Only allow alphanumeric characters, underscores, and backticks
    # Backticks are allowed for quoted identifiers but will be handled carefully
    import re
    if not re.match(r'^[a-zA-Z0-9_`]+$', table_name):
        raise SchemaToolError(f"Invalid table name: {table_name}")


def _validate_column_name(column_name: str) -> None:
    """Validate column name to prevent SQL injection.
    
    Args:
        column_name: Column name to validate
        
    Raises:
        SchemaToolError: If column name is invalid
    """
    if not column_name:
        raise SchemaToolError("Column name cannot be empty")
    
    import re
    if not re.match(r'^[a-zA-Z0-9_`]+$', column_name):
        raise SchemaToolError(f"Invalid column name: {column_name}")


def list_tables() -> Dict[str, Any]:
    """Returns all table names in the current database.
    
    Queries INFORMATION_SCHEMA.TABLES to get a list of all tables
    in the current database. Tables matching ignore patterns are excluded.
    
    Returns:
        Dictionary with 'tables' key containing list of table names
        Example: {"tables": ["users", "orders", "products"]}
        
    Raises:
        SchemaToolError: If database query fails
    """
    try:
        database_name = _get_current_database()
        
        with get_db_cursor() as cursor:
            query = """
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s
                AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """
            cursor.execute(query, (database_name,))
            results = cursor.fetchall()
            
            # Filter out ignored tables
            tables = [
                row["TABLE_NAME"]
                for row in results
                if not should_ignore_table(row["TABLE_NAME"])
            ]
            
            return {"tables": tables}
            
    except DatabaseConnectionError as e:
        raise SchemaToolError(f"Database connection error: {e}") from e
    except Exception as e:
        raise SchemaToolError(f"Failed to list tables: {e}") from e


def get_table_schema(table_name: str) -> Dict[str, Any]:
    """Returns detailed schema information for a specific table.
    
    Queries INFORMATION_SCHEMA.COLUMNS for column definitions and
    INFORMATION_SCHEMA.STATISTICS for index information.
    
    Args:
        table_name: Name of the table to get schema for
        
    Returns:
        Dictionary containing:
        - table_name: Name of the table
        - columns: List of column definitions with name, type, nullable, default, extra
        - primary_key: List of primary key column names
        - indexes: List of index definitions
        
        Example:
        {
            "table_name": "users",
            "columns": [
                {
                    "name": "id",
                    "type": "int",
                    "nullable": False,
                    "default": None,
                    "extra": "auto_increment"
                },
                ...
            ],
            "primary_key": ["id"],
            "indexes": [
                {
                    "name": "PRIMARY",
                    "columns": ["id"],
                    "unique": True
                },
                ...
            ]
        }
        
    Raises:
        SchemaToolError: If table doesn't exist, is ignored, or query fails
    """
    try:
        _validate_table_name(table_name)
        
        # Check if table is ignored
        if should_ignore_table(table_name):
            raise SchemaToolError(f"Table '{table_name}' is not accessible")
        
        database_name = _get_current_database()
        
        with get_db_cursor() as cursor:
            # Get column information
            columns_query = """
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT,
                    EXTRA,
                    COLUMN_COMMENT,
                    CHARACTER_MAXIMUM_LENGTH,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """
            cursor.execute(columns_query, (database_name, table_name))
            columns_results = cursor.fetchall()
            
            if not columns_results:
                raise SchemaToolError(f"Table '{table_name}' not found in database '{database_name}'")
            
            columns = []
            for row in columns_results:
                column_info = {
                    "name": row["COLUMN_NAME"],
                    "type": row["DATA_TYPE"],
                    "nullable": row["IS_NULLABLE"] == "YES",
                    "default": row["COLUMN_DEFAULT"],
                    "extra": row["EXTRA"] or "",
                }
                
                # Add type-specific details
                if row["CHARACTER_MAXIMUM_LENGTH"]:
                    column_info["max_length"] = row["CHARACTER_MAXIMUM_LENGTH"]
                if row["NUMERIC_PRECISION"] is not None:
                    column_info["numeric_precision"] = row["NUMERIC_PRECISION"]
                if row["NUMERIC_SCALE"] is not None:
                    column_info["numeric_scale"] = row["NUMERIC_SCALE"]
                if row["COLUMN_COMMENT"]:
                    column_info["comment"] = row["COLUMN_COMMENT"]
                    
                columns.append(column_info)
            
            # Get index information
            indexes_query = """
                SELECT 
                    INDEX_NAME,
                    COLUMN_NAME,
                    NON_UNIQUE,
                    SEQ_IN_INDEX
                FROM INFORMATION_SCHEMA.STATISTICS
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = %s
                ORDER BY INDEX_NAME, SEQ_IN_INDEX
            """
            cursor.execute(indexes_query, (database_name, table_name))
            indexes_results = cursor.fetchall()
            
            # Process indexes
            indexes_map: Dict[str, Dict[str, Any]] = {}
            primary_key = []
            
            for row in indexes_results:
                index_name = row["INDEX_NAME"]
                column_name = row["COLUMN_NAME"]
                is_unique = row["NON_UNIQUE"] == 0
                
                if index_name == "PRIMARY":
                    primary_key.append(column_name)
                
                if index_name not in indexes_map:
                    indexes_map[index_name] = {
                        "name": index_name,
                        "columns": [],
                        "unique": is_unique
                    }
                indexes_map[index_name]["columns"].append(column_name)
            
            indexes = list(indexes_map.values())
            
            return {
                "table_name": table_name,
                "columns": columns,
                "primary_key": primary_key,
                "indexes": indexes
            }
            
    except DatabaseConnectionError as e:
        raise SchemaToolError(f"Database connection error: {e}") from e
    except SchemaToolError:
        raise
    except Exception as e:
        raise SchemaToolError(f"Failed to get table schema: {e}") from e


def get_relationships(table_name: str) -> Dict[str, Any]:
    """Returns foreign key relationships for a specific table.
    
    Queries INFORMATION_SCHEMA.KEY_COLUMN_USAGE to find both outgoing
    foreign keys (from this table to others) and incoming references
    (other tables referencing this one). Relationships involving ignored
    tables are filtered out.
    
    Args:
        table_name: Name of the table to get relationships for
        
    Returns:
        Dictionary containing:
        - table_name: Name of the table
        - foreign_keys: List of outgoing foreign keys
        - referenced_by: List of incoming foreign key references
        
        Example:
        {
            "table_name": "orders",
            "foreign_keys": [
                {
                    "column": "user_id",
                    "referenced_table": "users",
                    "referenced_column": "id",
                    "constraint_name": "fk_orders_user"
                }
            ],
            "referenced_by": [
                {
                    "table": "order_items",
                    "column": "order_id",
                    "referenced_column": "id",
                    "constraint_name": "fk_order_items_order"
                }
            ]
        }
        
    Raises:
        SchemaToolError: If table doesn't exist, is ignored, or query fails
    """
    try:
        _validate_table_name(table_name)
        
        # Check if table is ignored
        if should_ignore_table(table_name):
            raise SchemaToolError(f"Table '{table_name}' is not accessible")
        
        database_name = _get_current_database()
        
        with get_db_cursor() as cursor:
            # Get outgoing foreign keys (this table references others)
            outgoing_query = """
                SELECT
                    COLUMN_NAME,
                    REFERENCED_TABLE_NAME,
                    REFERENCED_COLUMN_NAME,
                    CONSTRAINT_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = %s
                AND REFERENCED_TABLE_NAME IS NOT NULL
                ORDER BY CONSTRAINT_NAME, ORDINAL_POSITION
            """
            cursor.execute(outgoing_query, (database_name, table_name))
            outgoing_results = cursor.fetchall()
            
            foreign_keys = []
            for row in outgoing_results:
                # Skip if the referenced table is ignored
                if should_ignore_table(row["REFERENCED_TABLE_NAME"]):
                    continue
                foreign_keys.append({
                    "column": row["COLUMN_NAME"],
                    "referenced_table": row["REFERENCED_TABLE_NAME"],
                    "referenced_column": row["REFERENCED_COLUMN_NAME"],
                    "constraint_name": row["CONSTRAINT_NAME"]
                })
            
            # Get incoming references (other tables reference this one)
            incoming_query = """
                SELECT
                    TABLE_NAME,
                    COLUMN_NAME,
                    REFERENCED_COLUMN_NAME,
                    CONSTRAINT_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s
                AND REFERENCED_TABLE_NAME = %s
                ORDER BY TABLE_NAME, CONSTRAINT_NAME
            """
            cursor.execute(incoming_query, (database_name, table_name))
            incoming_results = cursor.fetchall()
            
            referenced_by = []
            for row in incoming_results:
                # Skip if the referencing table is ignored
                if should_ignore_table(row["TABLE_NAME"]):
                    continue
                referenced_by.append({
                    "table": row["TABLE_NAME"],
                    "column": row["COLUMN_NAME"],
                    "referenced_column": row["REFERENCED_COLUMN_NAME"],
                    "constraint_name": row["CONSTRAINT_NAME"]
                })
            
            return {
                "table_name": table_name,
                "foreign_keys": foreign_keys,
                "referenced_by": referenced_by
            }
            
    except DatabaseConnectionError as e:
        raise SchemaToolError(f"Database connection error: {e}") from e
    except Exception as e:
        raise SchemaToolError(f"Failed to get relationships: {e}") from e


def search_tables(query: str) -> Dict[str, Any]:
    """Search for tables based on keywords in table or column names.
    
    Performs substring matching on table names and column names to find
    relevant tables. Returns results with relevance scores. Ignored tables
    are excluded from search results.
    
    Args:
        query: Search keyword or phrase
        
    Returns:
        Dictionary containing:
        - query: The search query
        - results: List of matching tables with relevance scores
        
        Example:
        {
            "query": "user",
            "results": [
                {"table": "users", "relevance": 1.0, "matches": ["table_name"]},
                {"table": "user_profiles", "relevance": 0.8, "matches": ["table_name"]},
                {"table": "orders", "relevance": 0.5, "matches": ["column:user_id"]}
            ]
        }
        
    Raises:
        SchemaToolError: If query is empty or query fails
    """
    try:
        if not query or not query.strip():
            raise SchemaToolError("Search query cannot be empty")
        
        query = query.strip().lower()
        database_name = _get_current_database()
        
        with get_db_cursor() as cursor:
            # Search table names
            tables_query = """
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s
                AND TABLE_TYPE = 'BASE TABLE'
            """
            cursor.execute(tables_query, (database_name,))
            all_tables = cursor.fetchall()
            
            results = []
            table_scores: Dict[str, Dict[str, Any]] = {}
            
            # Score table name matches (skip ignored tables)
            for row in all_tables:
                table_name = row["TABLE_NAME"]
                
                # Skip ignored tables
                if should_ignore_table(table_name):
                    continue
                
                table_lower = table_name.lower()
                
                if query == table_lower:
                    # Exact match
                    table_scores[table_name] = {
                        "table": table_name,
                        "relevance": 1.0,
                        "matches": ["table_name"]
                    }
                elif query in table_lower:
                    # Substring match in table name
                    table_scores[table_name] = {
                        "table": table_name,
                        "relevance": 0.8,
                        "matches": ["table_name"]
                    }
            
            # Search column names
            columns_query = """
                SELECT TABLE_NAME, COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
            """
            cursor.execute(columns_query, (database_name,))
            all_columns = cursor.fetchall()
            
            # Score column name matches (skip ignored tables)
            for row in all_columns:
                table_name = row["TABLE_NAME"]
                column_name = row["COLUMN_NAME"]
                column_lower = column_name.lower()
                
                # Skip ignored tables
                if should_ignore_table(table_name):
                    continue
                
                if query in column_lower:
                    if table_name in table_scores:
                        # Already matched on table name, boost score slightly
                        if f"column:{column_name}" not in table_scores[table_name]["matches"]:
                            table_scores[table_name]["matches"].append(f"column:{column_name}")
                            table_scores[table_name]["relevance"] = min(
                                1.0, table_scores[table_name]["relevance"] + 0.1
                            )
                    else:
                        # New match on column name
                        relevance = 0.5 if query == column_lower else 0.3
                        table_scores[table_name] = {
                            "table": table_name,
                            "relevance": relevance,
                            "matches": [f"column:{column_name}"]
                        }
            
            # Convert to list and sort by relevance
            results = list(table_scores.values())
            results.sort(key=lambda x: x["relevance"], reverse=True)
            
            return {
                "query": query,
                "results": results
            }
            
    except DatabaseConnectionError as e:
        raise SchemaToolError(f"Database connection error: {e}") from e
    except SchemaToolError:
        raise
    except Exception as e:
        raise SchemaToolError(f"Failed to search tables: {e}") from e


def get_column_stats(table_name: str, column_name: str) -> Dict[str, Any]:
    """Returns statistical metadata for a specific column.
    
    Queries INFORMATION_SCHEMA.COLUMNS for type information and attempts
    to gather statistical metadata like distinct count and null presence.
    Note: This only queries INFORMATION_SCHEMA, not actual table data.
    
    Args:
        table_name: Name of the table containing the column
        column_name: Name of the column to get stats for
        
    Returns:
        Dictionary containing:
        - table_name: Name of the table
        - column_name: Name of the column
        - type: Data type of the column
        - nullable: Whether the column allows NULL values
        - max_length: Maximum character length (for string types)
        - numeric_precision: Precision (for numeric types)
        - numeric_scale: Scale (for numeric types)
        - has_index: Whether the column has any index
        - is_primary_key: Whether the column is part of primary key
        - is_foreign_key: Whether the column is a foreign key
        
        Example:
        {
            "table_name": "users",
            "column_name": "email",
            "type": "varchar",
            "nullable": True,
            "max_length": 255,
            "has_index": True,
            "is_primary_key": False,
            "is_foreign_key": False
        }
        
    Raises:
        SchemaToolError: If column doesn't exist, table is ignored, or query fails
    """
    try:
        _validate_table_name(table_name)
        _validate_column_name(column_name)
        
        # Check if table is ignored
        if should_ignore_table(table_name):
            raise SchemaToolError(f"Table '{table_name}' is not accessible")
        
        database_name = _get_current_database()
        
        with get_db_cursor() as cursor:
            # Get column information from INFORMATION_SCHEMA
            column_query = """
                SELECT 
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT,
                    CHARACTER_MAXIMUM_LENGTH,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE,
                    COLUMN_COMMENT,
                    EXTRA
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = %s
                AND COLUMN_NAME = %s
            """
            cursor.execute(column_query, (database_name, table_name, column_name))
            column_result = cursor.fetchone()
            
            if not column_result:
                raise SchemaToolError(
                    f"Column '{column_name}' not found in table '{table_name}'"
                )
            
            # Check for indexes on this column
            index_query = """
                SELECT 
                    INDEX_NAME,
                    NON_UNIQUE,
                    SEQ_IN_INDEX
                FROM INFORMATION_SCHEMA.STATISTICS
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = %s
                AND COLUMN_NAME = %s
            """
            cursor.execute(index_query, (database_name, table_name, column_name))
            index_results = cursor.fetchall()
            
            has_index = len(index_results) > 0
            is_primary_key = any(row["INDEX_NAME"] == "PRIMARY" for row in index_results)
            
            # Check if column is a foreign key
            fk_query = """
                SELECT CONSTRAINT_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = %s
                AND COLUMN_NAME = %s
                AND REFERENCED_TABLE_NAME IS NOT NULL
            """
            cursor.execute(fk_query, (database_name, table_name, column_name))
            fk_result = cursor.fetchone()
            is_foreign_key = fk_result is not None
            
            # Build result
            result = {
                "table_name": table_name,
                "column_name": column_name,
                "type": column_result["DATA_TYPE"],
                "nullable": column_result["IS_NULLABLE"] == "YES",
                "has_index": has_index,
                "is_primary_key": is_primary_key,
                "is_foreign_key": is_foreign_key,
            }
            
            # Add optional fields
            if column_result["COLUMN_DEFAULT"] is not None:
                result["default_value"] = column_result["COLUMN_DEFAULT"]
            
            if column_result["CHARACTER_MAXIMUM_LENGTH"]:
                result["max_length"] = column_result["CHARACTER_MAXIMUM_LENGTH"]
            
            if column_result["NUMERIC_PRECISION"] is not None:
                result["numeric_precision"] = column_result["NUMERIC_PRECISION"]
            
            if column_result["NUMERIC_SCALE"] is not None:
                result["numeric_scale"] = column_result["NUMERIC_SCALE"]
            
            if column_result["COLUMN_COMMENT"]:
                result["comment"] = column_result["COLUMN_COMMENT"]
            
            if column_result["EXTRA"]:
                result["extra"] = column_result["EXTRA"]
            
            # Add index details
            if index_results:
                indexes = []
                for idx in index_results:
                    indexes.append({
                        "name": idx["INDEX_NAME"],
                        "unique": idx["NON_UNIQUE"] == 0,
                        "position": idx["SEQ_IN_INDEX"]
                    })
                result["indexes"] = indexes
            
            return result
            
    except DatabaseConnectionError as e:
        raise SchemaToolError(f"Database connection error: {e}") from e
    except SchemaToolError:
        raise
    except Exception as e:
        raise SchemaToolError(f"Failed to get column stats: {e}") from e
