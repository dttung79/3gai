#!/usr/bin/env python3
"""
MySQL MCP Server
Allows Claude to query MySQL database named 'abc' on localhost
Supports: list tables, describe table, and select queries only
"""

import asyncio
import json
from typing import Any
import mysql.connector
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# Create server instance
server = Server("mysql-server")

# Database connection configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'abc',
    'user': 'root',  # Default user, change as needed
    'password': 'R00t!2025',  # Set password as needed
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        raise Exception(f"Database connection error: {err}")

def format_table_data(columns, rows):
    """Format query results into a readable table"""
    if not rows:
        return "No data found."
    
    # Calculate column widths
    col_widths = []
    for i, col in enumerate(columns):
        max_width = len(str(col))
        for row in rows:
            max_width = max(max_width, len(str(row[i])) if row[i] is not None else 4)
        col_widths.append(max_width + 2)
    
    # Create header
    header = "|"
    separator = "|"
    for i, col in enumerate(columns):
        header += f" {str(col):<{col_widths[i]-1}}|"
        separator += f"{'-'*col_widths[i]}|"
    
    # Create rows
    result = header + "\n" + separator + "\n"
    for row in rows:
        row_str = "|"
        for i, cell in enumerate(row):
            cell_str = str(cell) if cell is not None else "NULL"
            row_str += f" {cell_str:<{col_widths[i]-1}}|"
        result += row_str + "\n"
    
    return result

async def handle_test_connection() -> list[TextContent]:
    """Handle test_connection tool"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return [TextContent(
            type="text",
            text=f"Database connection successful!\nMySQL Version: {version}\nDatabase: {DB_CONFIG['database']}\nHost: {DB_CONFIG['host']}"
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Database connection failed: {str(e)}"
        )]

async def handle_list_tables() -> list[TextContent]:
    """Handle list_tables tool"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if not tables:
            return [TextContent(
                type="text",
                text="No tables found in the database."
            )]
        
        table_list = "\n".join([f"- {table[0]}" for table in tables])
        return [TextContent(
            type="text",
            text=f"Tables in database '{DB_CONFIG['database']}':\n\n{table_list}"
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error listing tables: {str(e)}"
        )]

async def handle_describe_table(table_name: str) -> list[TextContent]:
    """Handle describe_table tool"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE %s", (table_name,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return [TextContent(
                type="text",
                text=f"Table '{table_name}' does not exist."
            )]
        
        # Describe table structure
        cursor.execute(f"DESCRIBE `{table_name}`")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        table_structure = format_table_data(columns, rows)
        return [TextContent(
            type="text",
            text=f"Structure of table '{table_name}':\n\n{table_structure}"
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error describing table '{table_name}': {str(e)}"
        )]

async def handle_select_query(query: str) -> list[TextContent]:
    """Handle select_query tool"""
    query = query.strip()
    
    # Security check: only allow SELECT queries
    if not query.upper().startswith("SELECT"):
        return [TextContent(
            type="text",
            text="Error: Only SELECT queries are allowed."
        )]
    
    # Additional security: prevent certain dangerous keywords
    dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
    query_upper = query.upper()
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return [TextContent(
                type="text",
                text=f"Error: Query contains forbidden keyword '{keyword}'. Only SELECT queries are allowed."
            )]
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if not rows:
            return [TextContent(
                type="text",
                text=f"Query executed successfully but returned no results.\n\nQuery: {query}"
            )]
        
        result_table = format_table_data(columns, rows)
        return [TextContent(
            type="text",
            text=f"Query results:\n\nQuery: {query}\n\n{result_table}\nRows returned: {len(rows)}"
        )]
        
    except mysql.connector.Error as e:
        return [TextContent(
            type="text",
            text=f"MySQL Error: {str(e)}\n\nQuery: {query}"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error executing query: {str(e)}\n\nQuery: {query}"
        )]

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="list_tables",
            description="List all tables in the database",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="describe_table",
            description="Describe the structure of a specific table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to describe"
                    }
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="select_query",
            description="Execute a SELECT query on the database",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SELECT SQL query to execute (only SELECT statements allowed)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="test_connection",
            description="Test the database connection",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls by dispatching to appropriate handler functions"""
    
    if name == "test_connection":
        return await handle_test_connection()
    
    elif name == "list_tables":
        return await handle_list_tables()
    
    elif name == "describe_table":
        table_name = arguments["table_name"]
        return await handle_describe_table(table_name)
    
    elif name == "select_query":
        query = arguments["query"]
        return await handle_select_query(query)
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

async def main():
    """Main function to run the server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
