# Simplified PostgreSQL MCP Server

[中文文档](README_zh.md)

A lightweight PostgreSQL Model Context Protocol (MCP) server, designed to provide basic database interaction and query analysis capabilities.

## Tools

-   **query_sql**
    -   **Description**: Execute read-only SQL queries (SELECT).
    -   **Arguments**: `sql` (string) - The SELECT query to execute.
    -   **Returns**: Query results in JSON format.

-   **execute_sql**
    -   **Description**: Execute modification SQL statements (DML) such as INSERT, UPDATE, DELETE.
    -   **Arguments**: `sql` (string) - The DML statement to execute.
    -   **Returns**: Execution status message (e.g., number of rows affected).

-   **run_ddl**
    -   **Description**: Execute database structure definition statements (DDL) such as CREATE, DROP, ALTER, TRUNCATE.
    -   **Arguments**: `sql` (string) - The DDL statement to execute.
    -   **Returns**: Execution status message.

-   **list_tables**
    -   **Description**: List tables in the database.
    -   **Arguments**: `schema` (string, default "public") - The schema name to query.
    -   **Returns**: JSON list containing table names and types.

-   **describe_table**
    -   **Description**: Get detailed structure information of a table.
    -   **Arguments**:
        -   `table_name` (string) - The name of the table.
        -   `schema` (string, default "public") - The schema name.
    -   **Returns**: JSON list containing column names, data types, nullability, default values, etc.

-   **explain_query**
    -   **Description**: Analyze SQL query plans, with support for hypothetical indexes.
    -   **Arguments**:
        -   `sql` (string) - The SQL statement to analyze.
        -   `analyze` (boolean, default false) - Whether to actually execute the query (EXPLAIN ANALYZE).
        -   `hypothetical_indexes` (list[string], optional) - List of hypothetical index definitions (requires `hypopg` extension).
    -   **Returns**: Query plan in JSON format.

## Quick Start

This project supports multiple running methods. Choose the one that fits your scenario.

### Method 1: Using uvx (Recommended, No Installation Required)

If the code is published to PyPI or used via Git:

```bash
# Ensure environment variables are set
set DATABASE_URL=postgresql://postgres:password@localhost:5432/mydb

# Download and run automatically
uvx postgresql-server-mcp
```

### Method 2: Local Development

```bash
# Enter directory
cd postgresql-mcp

# Run (uv automatically installs dependencies)
uv run postgresql-server-mcp
```

## Configuration

### Environment Variables

You can configure the database connection in one of the following ways:

1.  **Method A (Recommended): Using `DATABASE_URL`**
    ```bash
    set DATABASE_URL=postgresql://user:password@localhost:5432/dbname
    ```

2.  **Method B: Using Standard PG Environment Variables**
    If `DATABASE_URL` is not set, the server will automatically read the following variables:
    -   `PGUSER`: Username
    -   `PGPASSWORD`: Password
    -   `PGHOST`: Host address (default localhost)
    -   `PGPORT`: Port (default 5432)
    -   `PGDATABASE`: Database name

### MCP Client Configuration Example

#### Claude Desktop / Trae Configuration

Add the following configuration to your MCP config file:

```json
{
  "mcpServers": {
    "postgresql": {
      "command": "uvx",
      "args": [
        "postgresql-server-mcp"
      ],
      "env": {
        "PGUSER": "your_username",
        "PGPASSWORD": "your_password",
        "PGHOST": "localhost",
        "PGPORT": "5432",
        "PGDATABASE": "your_dbname"
      }
    }
  }
}
```

## Publishing Guide

If you want to publish this as a standard MCP package for others to use via `uvx`:

1.  **Build**:
    ```bash
    uv build
    ```

2.  **Publish to PyPI**:
    ```bash
    uv publish
    ```

After publishing, anyone can run it directly via `uvx postgresql-server-mcp`.

## Hypothetical Index Analysis Example

To use hypothetical index analysis, your PostgreSQL database must have the `hypopg` extension installed:

```sql
-- Execute in database
CREATE EXTENSION hypopg;
```

Then call the `explain_query` tool in your MCP client:

-   **sql**: `SELECT * FROM my_table WHERE col_a = 123`
-   **hypothetical_indexes**: `["CREATE INDEX ON my_table (col_a)"]`
-   **analyze**: `false` (Hypothetical indexes do not support analyze)

The server will simulate index creation and return the query plan, allowing you to compare Cost values to evaluate the index's effect.
