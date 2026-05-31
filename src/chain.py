import ollama
from retriever import AdvancedRetriever
from config import *
from logger import logger

class NativeRAGChain:
    def __init__(self):
        self.retriever = AdvancedRetriever()
        
    def _contextualize_question(self, question: str, chat_history: list) -> str:
        """
        【面试防身注释 - 对话状态管理与查询改写 (Contextual Query Rewrite)】
        痛点：传统的RAG检索是拿“当前提问”去查向量库。但如果用户说“它出了什么错？”这里的“它”指代上一轮的系统。向量空间毫无头绪。
        方案：把"Chat History + 最新提问"融合，重写成一个【完全独立的、没有歧义的自然语言问句】再去查RAG检索。
        """
        if not chat_history:
            return question
            
        sys_prompt = (
            "根据聊天历史和最新的用户问题（它可能引用了聊天历史中的上下文），"
            "制定一个独立的、能被完全理解而无需参考历史记录的问题。\n"
            "不要回答问题，只是在需要时重构它，否则就原样返回它。\n"
            "无论何时，严禁输出任何<think>标签与内部思考过程，只输出重组后的独立问题语句。"
        )
        
        # 组装 messages 以调用 Ollama
        messages = [{"role": "system", "content": sys_prompt}]
        for role, msg in chat_history:
            # chat_history 结构: [("human", "问题"), ("ai", "回答")]
            ollama_role = "user" if role == "human" else "assistant"
            messages.append({"role": ollama_role, "content": msg})
            
        messages.append({"role": "user", "content": question})
        
        fallback_to_local = False
        
        if USE_ONLINE_LLM:
            try:
                from zai import ZhipuAiClient
                client = ZhipuAiClient(api_key=GLM_API_KEY)
                response = client.chat.completions.create(
                    model=GLM_LLM_MODEL,
                    messages=messages,
                    temperature=0.01  # Zhipu GLM API 通常不允许完全为0.0
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"⚠️ 在线 LLM API (_contextualize_question) 调用失败: {e}，正在切换为本地 Ollama...")
                fallback_to_local = True
                
        if not USE_ONLINE_LLM or fallback_to_local:
            # 禁用流式，直接获取一次改写结果
            response = ollama.chat(
                model=LLM_MODEL,
                messages=messages,
                options={"temperature": 0.0}
            )
            return response['message']['content'].strip()
        
    def stream_answer(self, question: str, chat_history: list):
        """
        供前端调用的核心方法：执行 RAG 流水线并 yield 返回流
        """
        # 1. 独立化查询（如果存在历史）
        standalone_question = self._contextualize_question(question, chat_history)

        # 2. 从向量库检索相关上下文
        context = self.retriever.retrieve_context(standalone_question)
        
        # 记录查找到的上下文
        logger.info("\n" + "="*50)
        logger.info(f"👀 【RAG 最终召回送入 LLM 的 Context】:\n{context}")
        logger.info(f"上下文行数: {len(context.splitlines())}")
        logger.info("="*50 + "\n")
        
        # 3. 构造给大模型的最终 Prompt
        qa_system_prompt = f"""你是一个企业级智能安全审计与知识问答助手。
请使用检索到的上下文来回答给定的问题。如果你不知道答案，就说你不知道，不要自己编造。
请保证回答的专业性与简洁性。

请按照以下格式输出：
<think>
[这里填写你的思考过程和分析逻辑，不要超过300字]
</think>
[基于思考，给出最终直接回答用户的答案]

【上下文信息】:
{context}"""
        
        # 构造最终流式请求的 messages
        messages = [{"role": "system", "content": qa_system_prompt}]
        for role, msg in chat_history:
            ollama_role = "user" if role == "human" else "assistant"
            messages.append({"role": ollama_role, "content": msg})
        messages.append({"role": "user", "content": question})  # 注意最终回答依然是对着用户原问题回答
        
        # 4. 执行生成并向外 `yield`
        fallback_to_local = False
        
        if USE_ONLINE_LLM:
            try:
                from zai import ZhipuAiClient
                client = ZhipuAiClient(api_key=GLM_API_KEY)
                stream_response = client.chat.completions.create(
                    model=GLM_LLM_MODEL,
                    messages=messages,
                    stream=True,
                    temperature=0.3
                )
                
                # 尝试获取并生成在线 API 的流式数据
                iterator = iter(stream_response)
                for chunk in iterator:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return  # 如果正常结束，则直接退出
            except Exception as e:
                logger.warning(f"⚠️ 在线 LLM API (stream_answer) 调用失败: {e}，正在尝试切换为本地 Ollama...")
                fallback_to_local = True
                
        if not USE_ONLINE_LLM or fallback_to_local:
            stream_response = ollama.chat(
                model=LLM_MODEL,
                messages=messages,
                stream=True,
                options={"temperature": 0.3}
            )
            
            for chunk in stream_response:
                yield chunk['message']['content']

