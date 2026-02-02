# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mcp[cli]",
#     "psycopg[binary]>=3.2.0",
# ]
# ///

import os
import asyncio
import json
from typing import Any, List, Optional
from mcp.server.fastmcp import FastMCP
import psycopg
from psycopg.rows import dict_row

# 初始化 FastMCP 服务
mcp = FastMCP("PostgreSQL")

async def get_connection() -> psycopg.AsyncConnection:
    """
    获取数据库连接。
    
    连接策略：
    1. 优先使用 DATABASE_URL 环境变量（如果存在）。
    2. 如果不存在 DATABASE_URL，则依赖 psycopg 的默认行为，
       它会自动读取 PGUSER, PGPASSWORD, PGHOST, PGPORT, PGDATABASE 等环境变量。
    """
    conn_info = os.environ.get("DATABASE_URL", "")
    
    try:
        # psycopg.AsyncConnection.connect 支持连接串或空参数（自动读取 libpq 环境变量）
        conn = await psycopg.AsyncConnection.connect(conn_info)
        return conn
    except Exception as e:
        # 收集一些调试信息（注意脱敏）
        user = os.environ.get("PGUSER", "Not Set")
        host = os.environ.get("PGHOST", "Not Set")
        db = os.environ.get("PGDATABASE", "Not Set")
        raise RuntimeError(f"无法连接到数据库 (User: {user}, Host: {host}, DB: {db}): {str(e)}")

@mcp.tool()
async def query_sql(sql: str) -> str:
    """
    执行通用的 SQL 查询。
    
    Args:
        sql: 要执行的 SQL 语句。
    """
    conn = await get_connection()
    try:
        async with conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(sql)
                
                # 如果是 SELECT 等返回结果的查询
                if cur.description:
                    rows = await cur.fetchall()
                    # 将结果转换为 JSON 格式字符串返回，处理日期等特殊类型
                    return json.dumps([dict(row) for row in rows], default=str, ensure_ascii=False)
                
                # 如果是 INSERT/UPDATE/DELETE 等
                return f"执行成功，影响行数: {cur.rowcount}"
    except Exception as e:
        return f"执行出错: {str(e)}"
    finally:
        await conn.close()

@mcp.tool()
async def list_tables(schema: str = "public") -> str:
    """
    列出指定模式下的所有表。
    
    Args:
        schema: 模式名称，默认为 'public'。
    """
    sql = """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = %s
        ORDER BY table_name;
    """
    conn = await get_connection()
    try:
        async with conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(sql, (schema,))
                rows = await cur.fetchall()
                return json.dumps([dict(row) for row in rows], default=str, ensure_ascii=False)
    except Exception as e:
        return f"获取表列表出错: {str(e)}"
    finally:
        await conn.close()

@mcp.tool()
async def describe_table(table_name: str, schema: str = "public") -> str:
    """
    获取表的结构信息（列名、类型等）。
    
    Args:
        table_name: 表名。
        schema: 模式名称，默认为 'public'。
    """
    sql = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position;
    """
    conn = await get_connection()
    try:
        async with conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(sql, (schema, table_name))
                rows = await cur.fetchall()
                if not rows:
                    return f"未找到表 {schema}.{table_name} 或表为空"
                return json.dumps([dict(row) for row in rows], default=str, ensure_ascii=False)
    except Exception as e:
        return f"获取表结构出错: {str(e)}"
    finally:
        await conn.close()

@mcp.tool()
async def explain_query(sql: str, analyze: bool = False, hypothetical_indexes: List[str] = []) -> str:
    """
    分析 SQL 查询计划，支持虚拟索引分析。
    
    Args:
        sql: 要分析的 SQL 语句。
        analyze: 是否实际执行查询 (EXPLAIN ANALYZE)。注意：如果使用了 hypothetical_indexes，analyze 必须为 False，因为虚拟索引不支持实际执行。
        hypothetical_indexes: 虚拟索引定义列表。每个元素应为一个完整的 CREATE INDEX 语句字符串。
                              例如: ["CREATE INDEX ON my_table (my_col)"]
                              需要数据库安装 hypopg 扩展。
    """
    if analyze and hypothetical_indexes:
        return "错误: 不能同时使用 analyze=True 和 hypothetical_indexes。虚拟索引无法用于实际执行计划 (EXPLAIN ANALYZE)。"

    conn = await get_connection()
    try:
        async with conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                # 1. 如果有虚拟索引，先尝试加载 hypopg
                if hypothetical_indexes:
                    try:
                        # 检查 hypopg 是否安装
                        await cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'hypopg'")
                        if not await cur.fetchone():
                            return "错误: 未检测到 'hypopg' 扩展。请先在数据库中安装: CREATE EXTENSION hypopg;"
                        
                        # 重置之前的虚拟索引
                        await cur.execute("SELECT hypopg_reset()")
                        
                        # 创建虚拟索引
                        for idx_def in hypothetical_indexes:
                            # hypopg_create_index 接受 CREATE INDEX 语句
                            await cur.execute("SELECT hypopg_create_index(%s)", (idx_def,))
                            
                    except Exception as e:
                        return f"创建虚拟索引失败: {str(e)}"

                # 2. 构建 EXPLAIN 语句
                explain_cmd = "EXPLAIN (FORMAT JSON"
                if analyze:
                    explain_cmd += ", ANALYZE"
                explain_cmd += ") " + sql
                
                # 3. 执行 EXPLAIN
                await cur.execute(explain_cmd)
                result = await cur.fetchone()
                
                if result and 'QUERY PLAN' in result:
                    return json.dumps(result['QUERY PLAN'], indent=2, ensure_ascii=False)
                return "未获取到查询计划"
                
    except Exception as e:
        return f"分析查询出错: {str(e)}"
    finally:
        await conn.close()

def main():
    # Windows 下 psycopg 需要使用 SelectorEventLoop
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    mcp.run()

if __name__ == "__main__":
    main()
