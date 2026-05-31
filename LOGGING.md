# 日志系统说明文档

## 📋 概览

项目已升级为完整的日志管理系统，用于替代原有的 `print()` 输出。所有日志输出现在可以：
- 📁 自动保存到 `logs/` 目录中的日志文件
- 🎛️ 通过 `config.py` 的 `LOG` 变量灵活控制
- 📊 支持多个日志级别（DEBUG, INFO, WARNING, ERROR）

---

## 🔧 核心配置

### config.py 中的日志设置

```python
# --- 日志配置 ---
LOG = True                                    # True: 记录日志; False: 关闭日志输出
LOG_DIR = os.path.join(BASE_DIR, "logs")     # 日志文件存储目录
LOG_LEVEL = "INFO"                           # 日志级别: DEBUG, INFO, WARNING, ERROR
```

### 参数说明

| 参数 | 默认值 | 说明 |
|---|---|---|
| `LOG` | `True` | 是否启用日志系统。False 时完全关闭日志（无输出、无文件） |
| `LOG_DIR` | `logs/` | 日志文件存储目录（相对于项目根目录） |
| `LOG_LEVEL` | `"INFO"` | 日志级别：DEBUG（最详细）→ INFO → WARNING → ERROR（最严重） |

---

## 🚀 使用场景

### 场景 1️⃣：Web UI 运行（app.py）

**所有日志自动保存到文件**

```bash
# 启动 Streamlit 应用
cd src
streamlit run app.py
```

- ✅ 自动在 `logs/` 目录下生成日志文件
- ✅ 文件名格式：`rag_YYYYMMDD_HHMMSS.log`
- ✅ 包含所有 INFO 及以上级别的日志

**日志文件内容示例**：
```
2026-05-29 14:30:45 - RAG_System - INFO - ✅ 日志系统已初始化，文件位置: E:\document\PycharmProjects\RAG\logs\rag_20260529_143045.log
2026-05-29 14:30:46 - RAG_System - INFO - 正在加载文档: docs/小林面试指南.txt (小林面试指南.txt)
2026-05-29 14:30:47 - RAG_System - INFO - 开始切分并生成向量（这可能需要一些时间）...
```

---

### 场景 2️⃣：测试脚本运行（evaluate.py）

#### 选项 A：保留日志

```bash
cd src
python evaluate.py
```

- ✅ 评测运行，日志保存到 `logs/` 目录

#### 选项 B：运行结束后清除日志

```bash
cd src
python evaluate.py --clean-logs
```

- ✅ 评测运行，日志记录到文件
- ✅ **运行结束时自动删除整个** `logs/` 目录
- 便于测试场景下不留下日志痕迹

---

### 场景 3️⃣：完全关闭日志

修改 `src/config.py`：

```python
LOG = False  # 关闭日志
```

**效果**：
- ❌ 不会在控制台输出日志
- ❌ 不会创建日志文件
- ❌ 完全静默运行

---

## 📊 日志级别

项目中使用的日志级别对应关系：

| 级别 | 函数 | 用途 | 示例 |
|---|---|---|---|
| **DEBUG** | `logger.debug()` | 详细的调试信息 | 向量数据库的详细检索过程、入库数据 |
| **INFO** | `logger.info()` | 一般信息 | 文档加载、索引完成、关键步骤 |
| **WARNING** | `logger.warning()` | 警告信息 | API 降级、切换本地模型 |
| **ERROR** | `logger.error()` | 错误信息 | 读取文件失败、API 异常 |

---

## 📁 日志文件结构

### 日志目录

```
RAG/
├── logs/
│   ├── rag_20260529_143045.log    # 2026-05-29 14:30:45 的会话日志
│   ├── rag_20260529_150230.log    # 2026-05-29 15:02:30 的会话日志
│   └── rag_20260529_163015.log    # ...
```

### 日志文件内容格式

**文件中** (DEBUG 及以上的详细信息)：
```
2026-05-29 14:30:45 - RAG_System - INFO - ✅ 日志系统已初始化
2026-05-29 14:30:46 - RAG_System - DEBUG - >> [输入] 即将去向量数据库匹配的扩展查询词 (Queries):
2026-05-29 14:30:47 - RAG_System - WARNING - ⚠️ 在线 LLM API 调用失败，切换为本地 Ollama
```

**控制台输出** (仅 INFO 及以上)：
```
14:30:45 - INFO - ✅ 日志系统已初始化
14:30:47 - WARNING - ⚠️ 在线 LLM API 调用失败，切换为本地 Ollama
14:31:00 - INFO - 入库完成！
```

---

## 🔄 已修改的文件列表

| 文件 | print 数量 | 状态 | 说明 |
|---|---|---|---|
| `src/chain.py` | 4 | ✅ 已替换 | RAG 链条核心逻辑 |
| `src/ingest.py` | 11 | ✅ 已替换 | 文档摄入与索引构建 |
| `src/retriever.py` | 14 | ✅ 已替换 | 多路检索与重排 |
| `src/evaluate.py` | 7 | ✅ 已替换 | 评估脚本 |
| `src/app.py` | 0 | ✅ 无需修改 | Streamlit 前端 |

**总计**：36 个 `print()` 语句已全部替换为 `logger` 调用

---

## 💻 快速参考

### 在代码中使用日志

```python
# 导入
from logger import logger

# 常见用法
logger.debug("调试信息")
logger.info("信息提示")
logger.warning("警告信息")
logger.error("错误信息")

# 格式化输出
logger.info(f"处理文件: {filename}")
logger.warning(f"API 调用失败: {exception}")
```

### 修改日志行为

```python
# src/config.py

# 启用详细日志（包括 DEBUG）
LOG = True
LOG_LEVEL = "DEBUG"

# 关闭日志
LOG = False

# 改变日志存储位置
LOG_DIR = os.path.join(BASE_DIR, "my_logs")
```

---

## 🎯 设计亮点

### ✨ 单例模式
`LoggerManager` 采用单例模式，确保全局只有一个 logger 实例，避免重复创建。

### 🎛️ 灵活的日志级别
- 通过修改 `LOG_LEVEL` 快速调整输出详细程度
- 文件总是保存 DEBUG 级别的详细信息
- 控制台仅显示 INFO 及以上的关键信息

### 🚫 完全的关闭选项
当 `LOG = False` 时：
- 使用 `NullHandler` 完全忽略所有日志
- 不创建日志文件
- 零性能开销

### ⏰ 时间戳命名
日志文件使用 `YYYYMMDD_HHMMSS` 格式命名，易于追踪多个会话。

---

## 🧪 测试日志系统

### 快速测试

```bash
cd src

# 测试 1: Web UI（保留日志）
streamlit run app.py
# 查看 logs/ 目录中是否有生成的日志文件

# 测试 2: 评估脚本（保留日志）
python evaluate.py

# 测试 3: 评估脚本（清除日志）
python evaluate.py --clean-logs
# 运行结束后，logs/ 目录应该被删除

# 测试 4: 关闭日志
# 修改 config.py: LOG = False
python evaluate.py
# 应该没有日志输出和日志文件生成
```

---

## ❓ 常见问题

### Q1: 日志文件在哪里？

A: 在项目根目录的 `logs/` 文件夹中，文件名格式为 `rag_YYYYMMDD_HHMMSS.log`。

### Q2: 如何只看 WARNING 和 ERROR？

A: 修改 `config.py`：
```python
LOG_LEVEL = "WARNING"
```

### Q3: 能否改变日志存储位置？

A: 可以，修改 `config.py`：
```python
LOG_DIR = "/path/to/custom/logs"
```

### Q4: 日志文件会越来越大吗？

A: 每次运行创建新文件（带时间戳），可以定期手动清理旧日志。也可以在 evaluate.py 中使用 `--clean-logs` 参数自动清理。

### Q5: print() 和 logger 能混用吗？

A: 可以，但建议统一使用 logger。如果有 print()，它会直接输出到控制台，不会被记录到日志文件。

---

## 📞 总结

✅ **完整的日志系统已实现**：
- 36 个 print 全部替换为 logger
- Web UI (app.py) 自动记录日志
- 评估脚本 (evaluate.py) 支持可选清除日志
- 通过 config.py 灵活控制日志行为
- 无额外代码入侵，使用简洁

**推荐设置**：
- Web UI 使用：`LOG = True`（默认）
- 测试使用：`python evaluate.py --clean-logs`
- 调试使用：`LOG_LEVEL = "DEBUG"`
