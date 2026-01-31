"""Main MCP server implementation for schema tools.

This module provides an MCP server that exposes 5 schema introspection tools
for MySQL databases. All tools only access INFORMATION_SCHEMA metadata -
never user data tables.

Environment Variables:
    MCP_SERVER_NAME: Server name (default: "schema-only-mcp")
    MCP_LOG_LEVEL: Logging level (default: INFO)
    DATABASE_URL or DB_*: Database connection parameters

Usage:
    python -m mcp_schema_server.server
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    ErrorData,
    TextContent,
    Tool,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)

from mcp_schema_server.tools.schema_tools import (
    list_tables,
    get_table_schema,
    get_relationships,
    search_tables,
    get_column_stats,
    SchemaToolError,
)
from mcp_schema_server.db.connection import (
    DatabaseConnectionError,
    DatabaseConfigError,
)

# Server configuration
SERVER_NAME = os.environ.get("MCP_SERVER_NAME", "schema-only-mcp")
LOG_LEVEL = os.environ.get("MCP_LOG_LEVEL", "INFO").upper()

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_schema_server")

# Tool definitions with JSON Schema for parameters
TOOL_DEFINITIONS: list[Tool] = [
    Tool(
        name="list_tables",
        description=(
            "Returns all table names in the current database. "
            "Use this tool to discover what tables are available before querying their schema. "
            "Returns a list of table names sorted alphabetically."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="get_table_schema",
        description=(
            "Returns detailed schema information for a specific table including columns, "
            "data types, nullability, defaults, primary keys, and indexes. "
            "Use this to understand the structure of a table before working with it."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table to get schema for",
                },
            },
            "required": ["table_name"],
        },
    ),
    Tool(
        name="get_relationships",
        description=(
            "Returns foreign key relationships for a specific table. Shows both outgoing "
            "foreign keys (this table references others) and incoming references "
            "(other tables reference this one). Use this to understand table relationships."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table to get relationships for",
                },
            },
            "required": ["table_name"],
        },
    ),
    Tool(
        name="search_tables",
        description=(
            "Search for tables based on keywords in table or column names. "
            "Returns matching tables with relevance scores. Use this when you need to "
            "find tables related to a specific concept but don't know the exact table name."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keyword or phrase to match against table and column names",
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="get_column_stats",
        description=(
            "Returns statistical metadata for a specific column including data type, "
            "nullability, indexes, primary key status, and foreign key status. "
            "Use this to understand column constraints and indexing."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table containing the column",
                },
                "column_name": {
                    "type": "string",
                    "description": "Name of the column to get statistics for",
                },
            },
            "required": ["table_name", "column_name"],
        },
    ),
]


def _format_error(error_code: int, message: str) -> Dict[str, Any]:
    """Format an error response for MCP.
    
    Args:
        error_code: MCP error code
        message: Error message (sanitized to not expose credentials)
        
    Returns:
        Error response dictionary
    """
    # Sanitize message to remove potential credential leaks
    sanitized = str(message)
    sensitive_patterns = [
        "password", "passwd", "pwd", "secret", "token",
        "credential", "auth", "key",
    ]
    for pattern in sensitive_patterns:
        # Replace any potential credential info with [REDACTED]
        if pattern.lower() in sanitized.lower():
            sanitized = f"[Error sanitized - contains sensitive information]"
            break
    
    return {
        "error": {
            "code": error_code,
            "message": sanitized,
        }
    }


async def handle_list_tables(arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle list_tables tool call."""
    logger.info("Executing list_tables")
    result = list_tables()
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_get_table_schema(arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle get_table_schema tool call."""
    table_name = arguments.get("table_name")
    if not table_name:
        raise ValueError("table_name is required")
    
    logger.info(f"Executing get_table_schema for table: {table_name}")
    result = get_table_schema(table_name)
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_get_relationships(arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle get_relationships tool call."""
    table_name = arguments.get("table_name")
    if not table_name:
        raise ValueError("table_name is required")
    
    logger.info(f"Executing get_relationships for table: {table_name}")
    result = get_relationships(table_name)
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_search_tables(arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle search_tables tool call."""
    query = arguments.get("query")
    if not query:
        raise ValueError("query is required")
    
    logger.info(f"Executing search_tables with query: {query}")
    result = search_tables(query)
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_get_column_stats(arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle get_column_stats tool call."""
    table_name = arguments.get("table_name")
    column_name = arguments.get("column_name")
    if not table_name or not column_name:
        raise ValueError("table_name and column_name are required")
    
    logger.info(f"Executing get_column_stats for {table_name}.{column_name}")
    result = get_column_stats(table_name, column_name)
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


# Tool handler mapping
TOOL_HANDLERS = {
    "list_tables": handle_list_tables,
    "get_table_schema": handle_get_table_schema,
    "get_relationships": handle_get_relationships,
    "search_tables": handle_search_tables,
    "get_column_stats": handle_get_column_stats,
}


async def main_async() -> None:
    """Main async entry point for the MCP server."""
    logger.info(f"Starting {SERVER_NAME} MCP server")
    
    # Create the MCP server
    server = Server(SERVER_NAME)
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """Return the list of available tools."""
        return TOOL_DEFINITIONS
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Handle a tool call."""
        logger.info(f"Tool call: {name}")
        
        handler = TOOL_HANDLERS.get(name)
        if not handler:
            logger.error(f"Unknown tool: {name}")
            raise RuntimeError(f"Unknown tool: {name}")
        
        try:
            return await handler(arguments)
        except ValueError as e:
            # Invalid parameters
            logger.warning(f"Invalid parameters for {name}: {e}")
            raise RuntimeError(f"Invalid parameters: {e}")
        except SchemaToolError as e:
            # Schema tool error (user-facing)
            logger.warning(f"Schema tool error in {name}: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
        except (DatabaseConnectionError, DatabaseConfigError) as e:
            # Database errors - don't expose internal details
            logger.error(f"Database error in {name}: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Database connection error. Please check database configuration."
                }, indent=2)
            )]
        except Exception as e:
            # Unexpected errors
            logger.exception(f"Unexpected error in {name}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "An unexpected error occurred. Please try again."
                }, indent=2)
            )]
    
    # Run the server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Server ready - waiting for connections")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    """Main entry point for the MCP server (synchronous wrapper)."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.exception("Fatal error running server")
        sys.exit(1)


# Entry point for uvx compatibility - uvx calls the function directly
def run() -> None:
    """Entry point for uvx tool execution."""
    # uvx calls this function directly when used as a tool
    # We need to handle --help here since uvx doesn't invoke the script normally
    import sys
    if len(sys.argv) > 1 and sys.argv[1] in ('--help', '-h'):
        print("MCP Schema Server for MySQL")
        print("A secure MCP server providing read-only access to MySQL database schemas.")
        print("\nThis server runs via stdio transport for MCP communication.")
        print("\nEnvironment variables:")
        print("  DB_HOST       MySQL host (default: localhost)")
        print("  DB_PORT       MySQL port (default: 3306)")
        print("  DB_NAME       MySQL database name (required)")
        print("  DB_USER       MySQL username (required)")
        print("  DB_PASSWORD   MySQL password (required)")
        print("  DATABASE_URL  Alternative: full connection URL")
        sys.exit(0)
    # Call main() which properly runs the async event loop
    main()


if __name__ == "__main__":
    main()
