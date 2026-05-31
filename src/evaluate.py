import json
import os
import sys
import shutil
import ollama
from tqdm import tqdm

from config import *
from retriever import AdvancedRetriever
from logger import logger

EVAL_RECALL_PROMPT = """你是一个专业的评委。请根据提供的[标准答案]和检索到的[上下文]，评估[上下文]中是否包含了能够推导出[标准答案]的全部或部分关键信息。
请只输出 0 或 1。1代表包含所需信息（召回成功），0代表不包含（召回失败）。
[标准答案]：{ground_truth}
[上下文]：{context}
评分："""

EVAL_RELEVANCE_PROMPT = """你是一个专业的评委。请根据[问题]和[回答]，评估[回答]是否直接且准确地回答了[问题]。
请只输出 0 或 1。1代表相关且正确，0代表不相关或错误。
[问题]：{question}
[回答]：{answer}
评分："""

EVAL_FAITHFULNESS_PROMPT = """你是一个专业的评委。请根据[上文]和[回答]，评估[回答]中的信息是否完全来源于[上文]，没有编造幻觉。
请只输出 0 或 1。1代表无幻觉（完全忠实），0代表存在幻觉或外部编造知识。
[上文]：{context}
[回答]：{answer}
评分："""

def llm_judge(prompt):
    messages = [{"role": "user", "content": prompt}]
    res = ollama.chat(model=LLM_MODEL, messages=messages, options={"temperature": 0.0})
    text = res['message']['content'].strip()
    return 1 if "1" in text else 0

def generate_answer(question, context):
    sys_prompt = f"""你是一个助手。请使用检索到的上下文来回答给定的问题。如果你不知道答案，就说不知道。请用中文回答。\n\n【上下文信息】:\n{context}"""
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": question}
    ]
    res = ollama.chat(model=LLM_MODEL, messages=messages, options={"temperature": 0.0})
    text = res['message']['content'].strip()
    # 如果输出包含<think>标签，尝试过滤掉
    import re
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    return text

def run_evaluation():
    dataset_path = os.path.join(BASE_DIR, "docs", "eval_dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    logger.info("初始化检索器...")
    retriever = AdvancedRetriever()
    
    pipelines = {
        "1_Baseline": [],
        "2_+MultiQuery": [],
        "3_+ParentChild": [],
        "4_+Reranker": []
    }
    
    logger.info("开始评测...")
    for idx, data in enumerate(tqdm(dataset, desc="Evaluating")):
        q = data["question"]
        gt = data["ground_truth"]
        
        # 1. Baseline
        q_emb = ollama.embeddings(model=EMBEDDING_MODEL, prompt=q)["embedding"]
        res1 = retriever.collection.query(query_embeddings=[q_emb], n_results=TOP_K_RETRIEVAL)
        ctx1_list = res1["documents"][0] if res1 and res1.get("documents") else []
        ctx1 = "\n".join(ctx1_list)
        
        # 2. +MultiQuery
        queries = retriever._generate_multi_queries(q)
        ctx2_list = []
        for mq in queries:
            mq_emb = ollama.embeddings(model=EMBEDDING_MODEL, prompt=mq)["embedding"]
            res2 = retriever.collection.query(query_embeddings=[mq_emb], n_results=TOP_K_RETRIEVAL)
            if res2 and res2.get("documents"):
                for d in res2["documents"][0]:
                    if d not in ctx2_list:
                        ctx2_list.append(d)
        ctx2 = "\n".join(ctx2_list)
        
        # 3. +ParentChild
        ctx3_list = retriever._parent_child_retrieve(queries)
        ctx3 = "\n".join(ctx3_list)
        
        # 4. +Reranker
        ctx4_list = retriever._rerank(q, ctx3_list)
        ctx4 = "\n".join(ctx4_list)
        
        contexts = {
            "1_Baseline": ctx1,
            "2_+MultiQuery": ctx2,
            "3_+ParentChild": ctx3,
            "4_+Reranker": ctx4
        }
        
        for p_name, ctx in contexts.items():
            # Answer generation
            ans = generate_answer(q, ctx)
            
            # 评估
            recall_score = llm_judge(EVAL_RECALL_PROMPT.format(ground_truth=gt, context=ctx))
            rel_score = llm_judge(EVAL_RELEVANCE_PROMPT.format(question=q, answer=ans))
            faith_score = llm_judge(EVAL_FAITHFULNESS_PROMPT.format(context=ctx, answer=ans))
            
            pipelines[p_name].append({
                "recall": recall_score,
                "relevance": rel_score,
                "faithfulness": faith_score
            })
            
    # 输出结果
    logger.info("\n" + "="*60)
    logger.info("评测结果统计 (LLM-as-a-Judge)：")
    logger.info("="*60)
    for p_name, metrics in pipelines.items():
        avg_recall = sum(m["recall"] for m in metrics) / len(metrics)
        avg_rel = sum(m["relevance"] for m in metrics) / len(metrics)
        avg_faith = sum(m["faithfulness"] for m in metrics) / len(metrics)
        logger.info(f"{p_name:<16} | Recall@K: {avg_recall:.2f} | Answer Relevance: {avg_rel:.2f} | Faithfulness: {avg_faith:.2f}")
    logger.info("="*60)

if __name__ == "__main__":
    # 支持桥接:
    # python evaluate.py              # 保留日志
    # python evaluate.py --clean-logs # 删除故事日志
    
    run_evaluation()
    
    # 检查是否需要清理日志
    if "--clean-logs" in sys.argv and LOG:
        logger.info("\n举报: 删除测试日志...")
        try:
            shutil.rmtree(LOG_DIR)
            logger.info(f"✅ 日志目录 {LOG_DIR} 已删除")
        except Exception as e:
            logger.error(f"因死日志目录失败: {e}")
