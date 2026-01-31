#!/usr/bin/env python3
"""
Example: Programmatic usage of MCP Schema Server tools.

This example demonstrates how to use the schema tools directly
from Python code without going through the MCP protocol.

Useful for:
- Building custom database documentation tools
- Automated schema validation
- Integration with existing Python applications
- Testing and debugging
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_schema_server.tools.schema_tools import (
    list_tables,
    get_table_schema,
    get_relationships,
    search_tables,
    get_column_stats,
    SchemaToolError,
)


def print_json(data: dict, title: str = None) -> None:
    """Pretty print JSON data with optional title."""
    if title:
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}")
    print(json.dumps(data, indent=2))
    print()


def example_list_tables() -> None:
    """Example: List all tables in the database."""
    print("Example 1: List all tables")
    print("-" * 60)
    
    try:
        result = list_tables()
        print_json(result, "All Tables")
        
        # Show how to iterate over tables
        tables = result.get("tables", [])
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")
            
    except SchemaToolError as e:
        print(f"Error: {e}")


def example_get_table_schema(table_name: str) -> None:
    """Example: Get detailed schema for a specific table."""
    print(f"\nExample 2: Get schema for '{table_name}'")
    print("-" * 60)
    
    try:
        result = get_table_schema(table_name)
        print_json(result, f"Schema: {table_name}")
        
        # Analyze the schema
        columns = result.get("columns", [])
        primary_key = result.get("primary_key", [])
        indexes = result.get("indexes", [])
        
        print(f"Summary:")
        print(f"  - Columns: {len(columns)}")
        print(f"  - Primary Key: {', '.join(primary_key) if primary_key else 'None'}")
        print(f"  - Indexes: {len(indexes)}")
        
        # Show column details
        print(f"\nColumn Details:")
        for col in columns:
            nullable = "NULL" if col["nullable"] else "NOT NULL"
            pk_marker = " (PK)" if col["name"] in primary_key else ""
            print(f"  - {col['name']}: {col['type']}{pk_marker} {nullable}")
            
    except SchemaToolError as e:
        print(f"Error: {e}")


def example_get_relationships(table_name: str) -> None:
    """Example: Get foreign key relationships for a table."""
    print(f"\nExample 3: Get relationships for '{table_name}'")
    print("-" * 60)
    
    try:
        result = get_relationships(table_name)
        print_json(result, f"Relationships: {table_name}")
        
        # Analyze relationships
        foreign_keys = result.get("foreign_keys", [])
        referenced_by = result.get("referenced_by", [])
        
        if foreign_keys:
            print(f"\nOutgoing Foreign Keys ({len(foreign_keys)}):")
            for fk in foreign_keys:
                print(f"  - {fk['column']} → {fk['referenced_table']}.{fk['referenced_column']}")
        else:
            print("\nNo outgoing foreign keys")
            
        if referenced_by:
            print(f"\nReferenced By ({len(referenced_by)}):")
            for ref in referenced_by:
                print(f"  - {ref['table']}.{ref['column']} → {table_name}.{ref['referenced_column']}")
        else:
            print("\nNo tables reference this table")
            
    except SchemaToolError as e:
        print(f"Error: {e}")


def example_search_tables(query: str) -> None:
    """Example: Search for tables by keyword."""
    print(f"\nExample 4: Search for '{query}'")
    print("-" * 60)
    
    try:
        result = search_tables(query)
        print_json(result, f"Search Results: '{query}'")
        
        # Show relevance scores
        results = result.get("results", [])
        if results:
            print(f"\nFound {len(results)} matching tables:")
            for item in results:
                table = item["table"]
                relevance = item["relevance"]
                matches = item["matches"]
                print(f"  - {table} (relevance: {relevance:.1f})")
                print(f"    Matched on: {', '.join(matches)}")
        else:
            print("\nNo matching tables found")
            
    except SchemaToolError as e:
        print(f"Error: {e}")


def example_get_column_stats(table_name: str, column_name: str) -> None:
    """Example: Get statistics for a specific column."""
    print(f"\nExample 5: Get column stats for '{table_name}.{column_name}'")
    print("-" * 60)
    
    try:
        result = get_column_stats(table_name, column_name)
        print_json(result, f"Column Stats: {table_name}.{column_name}")
        
        # Analyze column constraints
        print(f"\nConstraint Analysis:")
        print(f"  - Type: {result['type']}")
        print(f"  - Nullable: {'Yes' if result['nullable'] else 'No'}")
        print(f"  - Has Index: {'Yes' if result['has_index'] else 'No'}")
        print(f"  - Is Primary Key: {'Yes' if result['is_primary_key'] else 'No'}")
        print(f"  - Is Foreign Key: {'Yes' if result['is_foreign_key'] else 'No'}")
        
        if "max_length" in result:
            print(f"  - Max Length: {result['max_length']}")
        if "default_value" in result:
            print(f"  - Default: {result['default_value']}")
        if "comment" in result:
            print(f"  - Comment: {result['comment']}")
            
    except SchemaToolError as e:
        print(f"Error: {e}")


def example_generate_documentation() -> None:
    """Example: Generate simple documentation for all tables."""
    print("\nExample 6: Generate Database Documentation")
    print("=" * 60)
    
    try:
        # Get all tables
        tables_result = list_tables()
        tables = tables_result.get("tables", [])
        
        doc = {
            "database_documentation": {
                "total_tables": len(tables),
                "tables": []
            }
        }
        
        for table_name in tables:
            # Get schema for each table
            schema = get_table_schema(table_name)
            
            # Get relationships
            relationships = get_relationships(table_name)
            
            table_doc = {
                "name": table_name,
                "columns": [
                    {
                        "name": col["name"],
                        "type": col["type"],
                        "nullable": col["nullable"],
                        "is_primary_key": col["name"] in schema.get("primary_key", [])
                    }
                    for col in schema.get("columns", [])
                ],
                "primary_key": schema.get("primary_key", []),
                "foreign_keys": [
                    {
                        "column": fk["column"],
                        "references": f"{fk['referenced_table']}.{fk['referenced_column']}"
                    }
                    for fk in relationships.get("foreign_keys", [])
                ],
                "referenced_by": [
                    {
                        "table": ref["table"],
                        "column": ref["column"]
                    }
                    for ref in relationships.get("referenced_by", [])
                ]
            }
            
            doc["database_documentation"]["tables"].append(table_doc)
        
        print_json(doc, "Generated Documentation")
        
        # Save to file
        output_file = Path("database_documentation.json")
        with open(output_file, "w") as f:
            json.dump(doc, f, indent=2)
        print(f"Documentation saved to: {output_file}")
        
    except SchemaToolError as e:
        print(f"Error: {e}")


def main():
    """Run all examples."""
    print("MCP Schema Server - Usage Examples")
    print("=" * 60)
    print("\nThese examples demonstrate how to use the schema tools")
    print("programmatically from Python code.\n")
    
    # Example 1: List all tables
    example_list_tables()
    
    # Example 2: Get schema for a table (uses first table found)
    try:
        tables = list_tables().get("tables", [])
        if tables:
            example_get_table_schema(tables[0])
        else:
            print("\nSkipping schema example - no tables found")
    except Exception as e:
        print(f"\nSkipping schema example - {e}")
    
    # Example 3: Get relationships (uses first table found)
    try:
        tables = list_tables().get("tables", [])
        if tables:
            example_get_relationships(tables[0])
        else:
            print("\nSkipping relationships example - no tables found")
    except Exception as e:
        print(f"\nSkipping relationships example - {e}")
    
    # Example 4: Search for tables
    example_search_tables("user")
    
    # Example 5: Get column stats (uses first table and column found)
    try:
        tables = list_tables().get("tables", [])
        if tables:
            schema = get_table_schema(tables[0])
            columns = schema.get("columns", [])
            if columns:
                example_get_column_stats(tables[0], columns[0]["name"])
            else:
                print("\nSkipping column stats example - no columns found")
        else:
            print("\nSkipping column stats example - no tables found")
    except Exception as e:
        print(f"\nSkipping column stats example - {e}")
    
    # Example 6: Generate documentation
    print("\n" + "=" * 60)
    response = input("\nGenerate full database documentation? (y/N): ")
    if response.lower() == "y":
        example_generate_documentation()
    else:
        print("Skipping documentation generation")
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("\nFor more information, see:")
    print("  - README.md for full documentation")
    print("  - examples/mcp_config.json for MCP client configuration")


if __name__ == "__main__":
    main()
