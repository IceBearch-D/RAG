# RAG 检索工作流程 - 信息块分析

## 📊 整体流程图

```
用户输入 (user_input)
    ↓
[APP.PY] 
    ├─ 构造 chat_history = 历史消息 (除去当前输入)
    └─ 调用 rag_chain.stream_answer(user_input, chat_history)
         ↓
[CHAIN.PY - stream_answer()]
    ├─ 1️⃣ 独立化问题
    │   └─ standalone_question = _contextualize_question(question, chat_history)
    │       (输入 LLM：question + chat_history → 输出：独立化问题)
    │
    ├─ 2️⃣ 向量库检索
    │   └─ context = retriever.retrieve_context(standalone_question)
    │       [RETRIEVER.PY]
    │       ├─ 多查询：生成多个查询变体
    │       ├─ 向量检索：从 ChromaDB 查询相关文档
    │       ├─ 父子文档组装：从 docstore 拿完整父文档
    │       └─ CrossEncoder 重排：精确排序文档
    │
    ├─ 3️⃣ 构造最终 LLM 输入 (messages 列表)
    │   └─ messages = [
    │       {"role": "system", "content": qa_system_prompt},
    │       ...chat_history...,
    │       {"role": "user", "content": question}
    │   ]
    │
    └─ 4️⃣ 调用 LLM 并流式返回结果
```

---

## 🔢 最终交给 LLM 的信息块统计

### **消息结构 (messages 列表)**

| 序号 | 来源 | 块类型 | 数量 | 内容 | 代码位置 |
|------|------|--------|------|------|---------|
| **1** | system | system 消息 | 1 | 系统提示词 + 检索到的 `context` | chain.py L86-99 |
| **2** | history | user/assistant | N | 聊天历史消息 | chain.py L100-102 |
| **3** | current | user 消息 | 1 | 用户当前问题 | chain.py L103 |

### **总计**: 
- **消息块数**: `1 (系统) + N (历史) + 1 (当前) = N+2`
- **核心信息源**: 4 种

---

## 📝 详细信息块分解

### **块 1️⃣: 系统提示词 + 检索上下文 (SYSTEM ROLE)**

**来源**: chain.py L86-99

```python
qa_system_prompt = f"""你是一个企业级智能安全审计与知识问答助手。
请使用检索到的上下文来回答给定的问题。如果你不知道答案，就说你不知道，不要自己编造。
请保证回答的专业性与简洁性。

请按照以下格式输出：
<think>
[这里填写你的思考过程和分析逻辑，不要超过300字]
</think>
[基于思考，给出最终直接回答用户的答案]

【上下文信息】:
{context}"""  # ← context 就是从向量库检索到的相关文档
```

**包含内容**:
- ✅ 系统指示 (固定)
- ✅ 检索的上下文 `context` (动态，从 retriever.retrieve_context() 获得)

**context 的生成过程**:
1. 多查询：生成 3 个查询变体
2. 向量检索：ChromaDB 查询 
3. 父子文档：从 docstore.json 拿完整文档
4. CrossEncoder 重排：精确排序

---

### **块 2️⃣: 聊天历史 (USER/ASSISTANT ROLES)**

**来源**: app.py L80-85 + chain.py L100-102

```python
# app.py 构造 chat_history
chat_history = []
for msg in st.session_state.messages[:-1]:  # 排除当前输入
    role = "human" if msg["role"] == "user" else "ai"
    chat_history.append((role, msg["content"]))

# chain.py 添加到 messages
for role, msg in chat_history:
    ollama_role = "user" if role == "human" else "assistant"
    messages.append({"role": ollama_role, "content": msg})
```

**包含内容**:
- 所有历史对话（多轮会话）
- 交替的 user/assistant 角色
- **数量**: N (取决于对话轮数)

---

### **块 3️⃣: 当前用户问题 (USER ROLE)**

**来源**: app.py L60 + chain.py L103

```python
# app.py
user_input = st.chat_input("请输入您的问题...")

# chain.py 最后添加当前问题
messages.append({"role": "user", "content": question})
```

**包含内容**:
- 用户当前提出的问题
- **数量**: 1

---

## 🔍 关键信息提取点

### **_contextualize_question() 中的 chat_history 使用**

```python
def _contextualize_question(self, question: str, chat_history: list) -> str:
    """
    输入：question + chat_history
    输出：独立化的 standalone_question
    
    用途：将当前问题与历史结合，防止提问时的代词歧义
    例如：用户说 "它是什么？" → 变成 "Data Connector 是什么?"
    """
```

**这里的 chat_history** 会被发送给 LLM 一次（在 _contextualize_question 中），然后：
- 该 `standalone_question` 作为查询送入 `retriever.retrieve_context()`
- 同时原始的 `chat_history` 也会在 `stream_answer()` 中再次作为消息块发送给最终的 LLM

---

## 📌 最终统计总结

```
最终 messages 列表结构：
├─ messages[0]: {"role": "system", "content": "系统指示 + 检索的 context"}
├─ messages[1-N]: {"role": "user/assistant", "content": "历史对话"}  
│                  (交替的 user 和 assistant)
└─ messages[N+1]: {"role": "user", "content": "当前问题"}

总消息数 = 2 + len(chat_history)
```

### **核心信息源 (4 种独立来源)**

| 来源 | 说明 | 调用次数 |
|------|------|---------|
| **系统指示** | 固定的系统提示词 | 1次 (在 stream_answer 中) |
| **检索上下文** (context) | 从向量库动态检索 | 1次 (retriever.retrieve_context) |
| **聊天历史** | 多轮历史对话 | 2次 ⚠️ (一次在 _contextualize_question，一次在 stream_answer) |
| **当前问题** | 用户输入 | 2次 ⚠️ (一次在 _contextualize_question，一次在 stream_answer) |

---

## ⚠️ 重要发现

**聊天历史和当前问题被使用了 2 次**:
1. 第一次：在 `_contextualize_question()` 中用于生成独立化问题
2. 第二次：在 `stream_answer()` 中直接添加到最终 messages 列表中

这是正确的行为，因为：
- 第一次是为了生成更好的检索查询
- 第二次是为了让 LLM 有完整的对话上下文
