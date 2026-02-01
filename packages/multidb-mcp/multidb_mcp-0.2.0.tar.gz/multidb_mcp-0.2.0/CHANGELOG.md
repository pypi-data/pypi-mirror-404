# Changelog

## v0.2.0 - Stateless Design (2026-01-30)

### Breaking Changes

本版本采用**无状态设计**，对 API 进行了重大改变：

#### 移除的功能
- ❌ `switch_database(name)` 工具 - 不再需要切换数据库
- ❌ `current_db` 状态 - 服务器不再维护当前数据库状态

#### 修改的工具签名

**之前 (有状态设计)**:
```python
execute_query(query: str)  # 在当前数据库执行
list_tables()  # 列出当前数据库的表
describe_table(table_name: str)  # 描述当前数据库的表
```

**现在 (无状态设计)**:
```python
execute_query(database: str, query: str)  # 在指定数据库执行
list_tables(database: str)  # 列出指定数据库的表
describe_table(database: str, table_name: str)  # 描述指定数据库的表
```

### 新特性

- ✅ **无状态设计**: 每次调用明确指定数据库，无需维护状态
- ✅ **并发友好**: 多个客户端可以同时使用，互不干扰
- ✅ **更明确**: 每次调用都清楚知道在操作哪个数据库
- ✅ **分布式友好**: 适合云原生和无服务器环境

### 迁移指南

如果你正在从 v0.1.0 升级，需要修改代码：

**v0.1.0 用法**:
```python
# 1. 切换到数据库
switch_database("production")

# 2. 执行查询
result = execute_query("SELECT * FROM users")

# 3. 列出表
tables = list_tables()
```

**v0.2.0 用法**:
```python
# 直接在指定数据库上操作，无需切换
result = execute_query("production", "SELECT * FROM users")
tables = list_tables("production")

# 可以在同一个会话中访问不同数据库
dev_data = execute_query("dev", "SELECT * FROM users")
prod_data = execute_query("production", "SELECT * FROM users")
```

### 优势

1. **无状态**: 服务器不保存任何状态，更简单可靠
2. **并发安全**: 多个客户端不会互相影响
3. **清晰明确**: 每次调用都知道在操作哪个数据库
4. **易于理解**: 不需要记住"当前"在哪个数据库
5. **分布式友好**: 适合横向扩展和负载均衡

---

## v0.1.0 - 初始版本

- ✅ 支持多个数据库配置
- ✅ 有状态设计（需要 switch_database）
- ✅ 5 个 MCP 工具
- ✅ MySQL 和 PostgreSQL 支持
