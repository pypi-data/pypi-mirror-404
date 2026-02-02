# 简易版 PostgreSQL MCP Server

这是一个精简的 PostgreSQL Model Context Protocol (MCP) 服务器，旨在提供基础的数据库交互和查询分析功能。

## 工具说明

-   **query_sql**
    -   **功能**: 执行通用的 SQL 查询。
    -   **参数**: `sql` (string) - 要执行的 SQL 语句。
    -   **返回**: JSON 格式的查询结果或执行状态消息。

-   **list_tables**
    -   **功能**: 列出数据库中的表。
    -   **参数**: `schema` (string, 默认 "public") - 要查询的模式名称。
    -   **返回**: 包含表名和表类型的 JSON 列表。

-   **describe_table**
    -   **功能**: 获取表的详细结构信息。
    -   **参数**: 
        -   `table_name` (string) - 表名。
        -   `schema` (string, 默认 "public") - 模式名称。
    -   **返回**: 包含列名、数据类型、可空性、默认值等信息的 JSON 列表。

-   **explain_query**
    -   **功能**: 分析 SQL 查询计划，支持虚拟索引。
    -   **参数**:
        -   `sql` (string) - 要分析的 SQL 语句。
        -   `analyze` (boolean, 默认 false) - 是否实际执行查询 (EXPLAIN ANALYZE)。
        -   `hypothetical_indexes` (list[string], 可选) - 虚拟索引定义列表 (需要 hypopg 扩展)。
    -   **返回**: JSON 格式的查询计划。


## 快速开始

本项目支持多种运行方式，您可以根据场景选择。

### 方式 1: 使用 uvx (推荐，无需安装)

如果您的代码已发布到 PyPI 或通过 Git 使用：

```bash
# 确保设置了环境变量
set DATABASE_URL=postgresql://postgres:password@localhost:5432/mydb

# 自动下载并运行
uvx postgresql-server-mcp
```

### 方式 2: 本地开发运行

```bash
# 进入目录
cd postgresql-mcp

# 运行 (uv 会自动安装依赖)
uv run postgresql-server-mcp
```

## 配置

### 环境变量

您可以使用以下任意一种方式配置数据库连接：

1.  **方式 A (推荐): 使用 `DATABASE_URL`**
    ```bash
    set DATABASE_URL=postgresql://user:password@localhost:5432/dbname
    ```

2.  **方式 B: 使用标准 PG 环境变量**
    如果未设置 `DATABASE_URL`，服务器将自动读取以下变量：
    - `PGUSER`: 用户名
    - `PGPASSWORD`: 密码
    - `PGHOST`: 主机地址 (默认 localhost)
    - `PGPORT`: 端口 (默认 5432)
    - `PGDATABASE`: 数据库名

### MCP 客户端配置示例

#### Claude Desktop / Trae 配置

请将以下配置添加到您的 MCP 配置文件中：

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

## 发布指南

如果您想将其发布为标准的 MCP 包，以便他人通过 `uvx` 使用：

1.  **构建**:
    ```bash
    uv build
    ```

2.  **发布到 PyPI**:
    ```bash
    uv publish
    ```

发布后，任何人都可以通过 `uvx postgresql-server-mcp` 直接运行它。

## 虚拟索引分析示例

要使用虚拟索引分析，您的 PostgreSQL 数据库必须安装 `hypopg` 扩展：

```sql
-- 在数据库中执行
CREATE EXTENSION hypopg;
```

然后在 MCP 客户端中调用 `explain_query` 工具：

- **sql**: `SELECT * FROM my_table WHERE col_a = 123`
- **hypothetical_indexes**: `["CREATE INDEX ON my_table (col_a)"]`
- **analyze**: `false` (虚拟索引不支持 analyze)

服务器将模拟创建索引并返回查询计划，您可以对比 Cost 值来评估索引效果。
