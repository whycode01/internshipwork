#!/usr/bin/env python3
"""
MySQL MCP Server - Model Context Protocol implementation for MySQL
Provides secure read-only access to MySQL databases for AI assistants
"""

import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

import mysql.connector
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS, TextContent, Tool
from mysql.connector import Error

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mysql-mcp-server")


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling Decimal and datetime objects"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


class MySQLMCPServer:
    """MySQL MCP Server implementation"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'company_db')
        }
        self.connection = None
        self.server = Server("mysql-mcp-server")
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP request handlers"""
        
        @self.server.list_tools()
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
                    description="Get the schema/structure of a specific table",
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
                    name="query",
                    description="Execute a read-only SQL SELECT query",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "SQL SELECT query to execute"
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum number of rows to return (default: 100)",
                                "default": 100
                            }
                        },
                        "required": ["sql"]
                    }
                ),
                Tool(
                    name="get_schema",
                    description="Get complete database schema with all tables and their structures",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Handle tool calls"""
            try:
                if name == "list_tables":
                    result = await self.list_tables()
                elif name == "describe_table":
                    table_name = arguments.get("table_name")
                    if not table_name:
                        raise ValueError("table_name is required")
                    result = await self.describe_table(table_name)
                elif name == "query":
                    sql = arguments.get("sql")
                    limit = arguments.get("limit", 100)
                    if not sql:
                        raise ValueError("sql is required")
                    result = await self.execute_query(sql, limit)
                elif name == "get_schema":
                    result = await self.get_complete_schema()
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [TextContent(type="text", text=json.dumps(result, indent=2, cls=DecimalEncoder))]
            
            except ValueError as e:
                logger.error(f"Invalid parameters: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    def get_connection(self):
        """Get or create database connection"""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**self.db_config)
                logger.info(f"Connected to MySQL database: {self.db_config['database']}")
            return self.connection
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            raise
    
    async def list_tables(self) -> dict:
        """List all tables in the database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            cursor.close()
            
            return {
                "status": "success",
                "database": self.db_config['database'],
                "tables": tables,
                "count": len(tables)
            }
        except Error as e:
            logger.error(f"Error listing tables: {e}")
            return {"status": "error", "message": str(e)}
    
    async def describe_table(self, table_name: str) -> dict:
        """Get table structure"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get column information
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            row_count = cursor.fetchone()['count']
            
            cursor.close()
            
            return {
                "status": "success",
                "table_name": table_name,
                "columns": columns,
                "row_count": row_count
            }
        except Error as e:
            logger.error(f"Error describing table {table_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def execute_query(self, sql: str, limit: int = 100) -> dict:
        """Execute read-only SQL query"""
        try:
            # Basic security check - only allow SELECT statements
            sql_upper = sql.strip().upper()
            if not sql_upper.startswith('SELECT'):
                raise ValueError("Only SELECT queries are allowed")
            
            # Add LIMIT if not present
            if 'LIMIT' not in sql_upper:
                sql = f"{sql.rstrip(';')} LIMIT {limit}"
            
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql)
            results = cursor.fetchall()
            cursor.close()
            
            return {
                "status": "success",
                "query": sql,
                "rows_returned": len(results),
                "data": results
            }
        except Error as e:
            logger.error(f"Error executing query: {e}")
            return {"status": "error", "message": str(e), "query": sql}
    
    async def get_complete_schema(self) -> dict:
        """Get complete database schema"""
        try:
            tables_result = await self.list_tables()
            if tables_result["status"] != "success":
                return tables_result
            
            schema = {
                "database": self.db_config['database'],
                "tables": {}
            }
            
            for table_name in tables_result["tables"]:
                table_info = await self.describe_table(table_name)
                if table_info["status"] == "success":
                    schema["tables"][table_name] = table_info
            
            return {"status": "success", "schema": schema}
        except Exception as e:
            logger.error(f"Error getting complete schema: {e}")
            return {"status": "error", "message": str(e)}
    
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            logger.info("MySQL MCP Server starting...")
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )
    
    def cleanup(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")


async def main():
    """Main entry point"""
    server = MySQLMCPServer()
    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        server.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
