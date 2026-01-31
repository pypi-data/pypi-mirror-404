# MCP Schema Server for MySQL

A secure [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that provides AI assistants with safe, read-only access to MySQL database schemas. This server enables AI tools to understand your database structure without exposing any sensitive data.

> ⚠️ **Important Security Note**: While this server does not provide direct access to data in user tables, it does expose metadata including table names, column names, data types, constraints, indexes, and foreign key relationships. This metadata could potentially be used to infer sensitive information about your database structure, business logic, or data organization. Please review the following before using this server:
> - **Table and column names** may reveal business domains, data categories, or application functionality
> - **Foreign key relationships** can expose data model relationships and dependencies
> - **Constraint patterns** (unique constraints, check constraints) may indicate business rules or validation logic
> - **Index structures** can reveal query patterns and access priorities
> - **Column data types and lengths** may suggest the nature or sensitivity of stored data
>
> Ensure this level of schema exposure is acceptable for your use case before connecting to production databases.

## 🔒 Security First

```
✅ Schema-Only Access: Only queries INFORMATION_SCHEMA metadata
✅ No Data Exposure: User tables are never accessed
✅ Read-Only: No modifications to your database
✅ Input Validation: SQL injection protection on all inputs
✅ Error Sanitization: Credentials never leak in error messages
```

## 📋 Overview

The MCP Schema Server exposes 5 powerful tools for database introspection:

| Tool | Purpose |
|------|---------|
| `list_tables` | Discover all tables in the database |
| `get_table_schema` | Get detailed column and index information |
| `get_relationships` | View foreign key relationships |
| `search_tables` | Find tables by keyword matching |
| `get_column_stats` | Get column metadata and constraints |

Perfect for:
- AI-powered SQL query generation
- Database documentation
- Schema exploration
- Query optimization assistance

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- MySQL database
- MCP client (Claude Desktop, Kilocode, etc.)

### Installation

#### Option 1: Using uvx (Recommended - No Installation Required)

With [uv](https://docs.astral.sh/uv/) installed, you can run the server directly without installing it:

```bash
uvx mcp-schema-server
```

Or with environment variables:

```bash
uvx --env-file .env mcp-schema-server
```

#### Option 2: Traditional Installation

```bash
# Clone the repository
git clone <repository-url>
cd mcp-schema-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

### Configuration

Create a `.env` file in the project root:

```bash
# Copy the example configuration
cp .env.example .env

# Edit with your database credentials
nano .env
```

Required environment variables:

```env
# MySQL Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password

# Optional: Use connection string instead
# DATABASE_URL=mysql+pymysql://user:password@localhost:3306/database_name

# MCP Server Configuration
MCP_SERVER_NAME=mcp-schema-server
MCP_LOG_LEVEL=INFO
```

### Running the Server

```bash
# Run with uvx (no installation required)
uvx mcp-schema-server

# Run directly (if installed)
python -m mcp_schema_server.server

# Or use the installed command
mcp-schema-server
```

## 🔧 MCP Client Configuration

### Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%/Claude/claude_desktop_config.json` on Windows):

#### Using uvx (Recommended - No Installation Required)

```json
{
  "mcpServers": {
    "mysql-schema": {
      "command": "uvx",
      "args": ["mcp-schema-server"],
      "env": {
        "DB_HOST": "localhost",
        "DB_PORT": "3306",
        "DB_NAME": "your_database",
        "DB_USER": "your_username",
        "DB_PASSWORD": "your_password"
      }
    }
  }
}
```

#### Using Python Module (If Installed)

```json
{
  "mcpServers": {
    "mysql-schema": {
      "command": "python",
      "args": ["-m", "mcp_schema_server.server"],
      "env": {
        "DB_HOST": "localhost",
        "DB_PORT": "3306",
        "DB_NAME": "your_database",
        "DB_USER": "your_username",
        "DB_PASSWORD": "your_password"
      }
    }
  }
}
```

### Kilocode

Add to your Kilocode MCP configuration (`.kilocode/mcp.json`):

#### Using uvx (Recommended - No Installation Required)

```json
{
  "mcpServers": {
    "mysql-schema": {
      "command": "uvx",
      "args": ["mcp-schema-server"],
      "env": {
        "DB_HOST": "localhost",
        "DB_PORT": "3306",
        "DB_NAME": "your_database",
        "DB_USER": "your_username",
        "DB_PASSWORD": "your_password"
      }
    }
  }
}
```

#### Using Python Module (If Installed)

```json
{
  "mcpServers": {
    "mysql-schema": {
      "command": "python",
      "args": ["-m", "mcp_schema_server.server"],
      "env": {
        "DB_HOST": "localhost",
        "DB_PORT": "3306",
        "DB_NAME": "your_database",
        "DB_USER": "your_username",
        "DB_PASSWORD": "your_password"
      }
    }
  }
}
```

See [`examples/mcp_config.json`](examples/mcp_config.json) for more configuration examples.

## 🛠️ Available Tools

### 1. list_tables

Returns all table names in the current database.

**Usage:**
```json
{
  "name": "list_tables",
  "arguments": {}
}
```

**Example Response:**
```json
{
  "tables": ["customers", "orders", "order_items", "products", "users"]
}
```

### 2. get_table_schema

Returns detailed schema information for a specific table.

**Usage:**
```json
{
  "name": "get_table_schema",
  "arguments": {
    "table_name": "users"
  }
}
```

**Example Response:**
```json
{
  "table_name": "users",
  "columns": [
    {
      "name": "id",
      "type": "int",
      "nullable": false,
      "default": null,
      "extra": "auto_increment"
    },
    {
      "name": "email",
      "type": "varchar",
      "nullable": false,
      "default": null,
      "extra": "",
      "max_length": 255
    }
  ],
  "primary_key": ["id"],
  "indexes": [
    {
      "name": "PRIMARY",
      "columns": ["id"],
      "unique": true
    },
    {
      "name": "idx_email",
      "columns": ["email"],
      "unique": true
    }
  ]
}
```

### 3. get_relationships

Returns foreign key relationships for a specific table.

**Usage:**
```json
{
  "name": "get_relationships",
  "arguments": {
    "table_name": "orders"
  }
}
```

**Example Response:**
```json
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
```

### 4. search_tables

Search for tables based on keywords in table or column names.

**Usage:**
```json
{
  "name": "search_tables",
  "arguments": {
    "query": "user"
  }
}
```

**Example Response:**
```json
{
  "query": "user",
  "results": [
    {
      "table": "users",
      "relevance": 1.0,
      "matches": ["table_name"]
    },
    {
      "table": "user_profiles",
      "relevance": 0.8,
      "matches": ["table_name"]
    },
    {
      "table": "orders",
      "relevance": 0.5,
      "matches": ["column:user_id"]
    }
  ]
}
```

### 5. get_column_stats

Returns statistical metadata for a specific column.

**Usage:**
```json
{
  "name": "get_column_stats",
  "arguments": {
    "table_name": "users",
    "column_name": "email"
  }
}
```

**Example Response:**
```json
{
  "table_name": "users",
  "column_name": "email",
  "type": "varchar",
  "nullable": false,
  "max_length": 255,
  "has_index": true,
  "is_primary_key": false,
  "is_foreign_key": false,
  "indexes": [
    {
      "name": "idx_email",
      "unique": true,
      "position": 1
    }
  ]
}
```

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   MCP Client    │────▶│  MCP Schema      │────▶│  INFORMATION_   │
│  (Claude/etc)   │◀────│  Server          │◀────│  SCHEMA         │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │   MySQL DB       │
                        │  (metadata only) │
                        └──────────────────┘
```

The server follows a layered architecture:

1. **Server Layer** (`server.py`): MCP protocol handling, tool routing, error handling
2. **Tools Layer** (`tools/schema_tools.py`): Business logic for schema queries
3. **Database Layer** (`db/connection.py`): Connection management, configuration

All database access is strictly limited to `INFORMATION_SCHEMA` - the MySQL metadata catalog.

## 🔐 Privacy & Security

### What the Server CAN Access:
- ✅ Table names
- ✅ Column names and data types
- ✅ Index definitions
- ✅ Foreign key constraints
- ✅ Column constraints (nullable, defaults, etc.)

### What the Server CANNOT Access:
- ❌ User data in tables
- ❌ Row counts or statistics from user tables
- ❌ Actual values in any column
- ❌ Database credentials (only uses them to connect)

### Security Measures:

1. **Input Validation**: All table and column names are validated against SQL injection patterns
2. **Parameterized Queries**: All database queries use parameterized statements
3. **Error Sanitization**: Error messages are scrubbed to prevent credential leakage
4. **Read-Only Access**: Only `SELECT` queries on `INFORMATION_SCHEMA` are used
5. **Schema Isolation**: Queries are restricted to the configured database only

## 🧪 Testing & Validation

Run the validation script to test your setup:

```bash
# Test database connection and tool functionality
python scripts/validate_setup.py
```

This will verify:
- Database connectivity
- INFORMATION_SCHEMA access
- All tool functions

## 📚 Examples

See the [`examples/`](examples/) directory for:
- [`mcp_config.json`](examples/mcp_config.json) - MCP client configuration examples
- [`usage_example.py`](examples/usage_example.py) - Programmatic usage examples

## 🛠️ Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black mcp_schema_server/

# Lint code
ruff check mcp_schema_server/

# Type check
mypy mcp_schema_server/
```

## 📝 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_HOST` | No* | `localhost` | MySQL server hostname |
| `DB_PORT` | No* | `3306` | MySQL server port |
| `DB_NAME` | Yes* | - | Database name to connect to |
| `DB_USER` | Yes* | - | MySQL username |
| `DB_PASSWORD` | Yes* | - | MySQL password |
| `DATABASE_URL` | Alternative | - | Full connection string (overrides individual settings) |
| `MCP_SERVER_NAME` | No | `mcp-schema-server` | Server identifier |
| `MCP_LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

*Required unless using `DATABASE_URL`

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Troubleshooting

### Connection Issues

```bash
# Test database connectivity
python -c "from mcp_schema_server.db.connection import test_connection; print(test_connection())"
```

### Permission Errors

Ensure your MySQL user has `SELECT` privilege on `INFORMATION_SCHEMA`:

```sql
GRANT SELECT ON INFORMATION_SCHEMA.* TO 'your_user'@'localhost';
```

### MCP Client Not Finding Tools

1. Verify the server starts without errors: `python -m mcp_schema_server.server`
2. Check MCP client configuration JSON syntax
3. Ensure environment variables are properly set in the MCP config

---

**Note**: This server is designed for schema introspection only. It will never access your actual data, making it safe to use with production databases containing sensitive information.
