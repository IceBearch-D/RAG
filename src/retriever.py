import os
import json
import chromadb
import ollama
from sentence_transformers import CrossEncoder

from config import *
from logger import logger

class AdvancedRetriever:
    def __init__(self):
        # 1. 向量数据库连接
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        self.collection = self.chroma_client.get_or_create_collection(name=COLLECTION_NAME)
        
        # 2. 父文档存储连接
        self.docstore_path = os.path.join(STORE_DIR, "docstore.json")
        self.docstore = {}
        if os.path.exists(self.docstore_path):
            with open(self.docstore_path, 'r', encoding='utf-8') as f:
                self.docstore = json.load(f)
                
        # 3. 本地重排器加载 (Cross-Encoder)
        self.cross_encoder = CrossEncoder(RERANKER_MODEL, max_length=512)

    def _generate_multi_queries(self, question: str) -> list[str]:
        """
        【面试防身注释 - 多查询扩展 (Multi-Query)】
        为什么要多查询扩展？
        - 痛点：用户提问往往极其发散，单纯的相似度（Dense Retrieval）查不到。
        - 原理：调用大模型推理重写Question，变成3个表达不同的Query，多次召回并去重。
        """
        prompt = (
            "你是一个AI语言模型助手。你的任务是根据用户问题，生成3个不同版本的相同查询，用于从向量数据库中检索相关文档。\n"
            "请提供3个不同的查询，每个查询占一行，**不要输出任何思考过程，不要包含<think>标签等额外内容，直接给出列表即可**。\n"
            f"原始问题: {question}"
        )
        
        fallback_to_local = False
        content = ""
        
        if USE_ONLINE_LLM:
            try:
                from zai import ZhipuAiClient
                client = ZhipuAiClient(api_key=GLM_API_KEY)
                response = client.chat.completions.create(
                    model=GLM_LLM_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.choices[0].message.content
            except Exception as e:
                logger.warning(f"⚠️ 在线 LLM API (_generate_multi_queries) 调用失败: {e}，正在切换为本地 Ollama...")
                fallback_to_local = True
                
        if not USE_ONLINE_LLM or fallback_to_local:
            response = ollama.chat(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            content = response['message']['content']
        
        # 简单清洗并提取每一行作为一个query
        queries = [q.strip() for q in content.split('\n') if q.strip()]
        # 把原始问题也加进去
        queries.append(question)
        return list(set(queries))  # 去重处理

    def _parent_child_retrieve(self, queries: list[str]) -> list[str]:
        """
        【面试防身注释 - 父子文档检索 (Parent/Child Retriever)】
        在此处实现：检索时匹配小块的向量，但凭借 metadata 中的 doc_id 映射提取对应的父大块文档。
        """
        retrieved_parent_ids = set()
        
        q_embs = []
        fallback_to_local_emb = False
        
        if USE_ONLINE_EMBEDDING:
            try:
                # 批量发送请求避免遭到在线API的高频限流导致无返回
                from zai import ZhipuAiClient
                client = ZhipuAiClient(api_key=GLM_API_KEY)
                resp = client.embeddings.create(
                    model=GLM_EMBEDDING_MODEL,
                    input=queries
                )
                q_embs = [data.embedding for data in resp.data]
            except Exception as e:
                logger.warning(f"⚠️ 在线 Embedding API (_parent_child_retrieve) 调用失败: {e}，正在切换为本地 Ollama...")
                fallback_to_local_emb = True
                
        if not USE_ONLINE_EMBEDDING or fallback_to_local_emb:
            for q in queries:
                emb_res = ollama.embeddings(model=EMBEDDING_MODEL, prompt=q)
                q_embs.append(emb_res["embedding"])
                
        # --- 记录向量数据库检索请求 ---
        logger.debug("\n" + "🔥"*30)
        logger.debug(">>【输入】即将去向量数据库匹配的扩展查询词 (Queries):")
        for idx, q in enumerate(queries, 1):
            logger.debug(f"  {idx}. {q}")
        logger.debug("🔥"*30 + "\n")
        
        for idx, q_emb in enumerate(q_embs):
            # 去 Chroma 查子文档
            results = self.collection.query(
                query_embeddings=[q_emb],
                n_results=TOP_K_RETRIEVAL
            )
            
            # --- 记录向量数据库返回的初次召回文本 ---
            logger.debug("\n" + "⭐"*30)
            logger.debug(f"<< [输出] 向量数据库根据查询词 [{queries[idx]}] 初次召回的相关子片段:")
            logger.debug("⭐"*30)
            
            if results and results.get("documents") and results["documents"][0]:
                for doc_idx, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0]), 1):
                    doc_id = meta.get("doc_id", "未知")
                    logger.debug(f"\n▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼【返回片段 {doc_idx} (父文档doc_id: {doc_id})】▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼")
                    logger.debug(doc)
                    logger.debug("▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲")
            else:
                logger.debug("⚠️ 未找到匹配的文档。")
            logger.debug("⭐"*30 + "\n")
            
            # 提取 metadata 里的父文档 ID
            if results and results["metadatas"] and results["metadatas"][0]:
                for meta in results["metadatas"][0]:
                    if "doc_id" in meta:
                        retrieved_parent_ids.add(meta["doc_id"])
                        
        # 每次检索前重新加载 docstore，保证前端动态上传的文件也能被读取
        if os.path.exists(self.docstore_path):
            with open(self.docstore_path, 'r', encoding='utf-8') as f:
                self.docstore = json.load(f)

        # 组装返回的父文档文本
        parent_docs = []
        for pid in retrieved_parent_ids:
            if pid in self.docstore:
                parent_docs.append(self.docstore[pid])
                
        return parent_docs

    def _rerank(self, question: str, docs: list[str]) -> list[str]:
        """
        【面试防身注释 - 重排 (Reranker)】
        多路召回可能返回大量文本导致幻觉，这里使用 Cross-Encoder 计算 (Question, Document) pair 真实关联度，并截断。
        """
        if not docs:
            return []
            
        # 构造给 Cross-Encoder 评分的 Pair
        pairs = [[question, doc] for doc in docs]
        
        # 计算打分
        scores = self.cross_encoder.predict(pairs)
        
        # 组合打分和文档并排序
        scored_docs = list(zip(scores, docs))
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # 取 Top K
        top_docs = [doc for score, doc in scored_docs[:TOP_K_RERANK]]
        return top_docs

    def retrieve_context(self, question: str) -> str:
        """
        暴露对外的接口：多查询 -> 父子召回 -> 重排
        """
        # 1. 扩展查询
        queries = self._generate_multi_queries(question)
        
        # 2. 召回父文档（去重组合）
        docs = self._parent_child_retrieve(queries)
        
        # 3. 精排精简
        final_docs = self._rerank(question, docs)
        
        return "\n\n".join(final_docs)
