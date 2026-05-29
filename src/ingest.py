import os
import uuid
import hashlib
import json
import chromadb
import ollama
from pypdf import PdfReader
from config import *

def compute_md5(text: str) -> str:
    """计算文本的 MD5 摘要作为唯一 ID"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

import re

def split_text(text: str, chunk_size: int, chunk_overlap: int):
    """
    高级文本切分器（方案1加强版）
    - 按标点符号/换行符保证语义完整
    - 强制绑定特殊格式的一级标题（如 ==== 标题 ====）与其下文，绝不分离
    """
    # 1. 正则匹配标题块
    # 匹配模式：连续的 = 号（至少5个），换行，标题内容，换行，连续的 = 号
    # 使用 () 捕获组，使得 re.split 会把匹配到的标题原样保留在分割列表中
    header_pattern = r'([=]{5,}\s*\n.*?\n[=]{5,}\s*\n?)'
    
    # 按照标题将文章初步拆开
    raw_parts = re.split(header_pattern, text)
    
    # 2. 将全文本转化为结构化的 Token 列表
    tokens = []
    for part in raw_parts:
        if not part.strip():
            continue
            
        # 判断当前块是不是我们要保护的“标题块”
        if re.match(r'^[=]{5,}', part.strip()):
            tokens.append({"type": "header", "text": part})
        else:
            # 普通文本，按正常语义(句号/问号/叹号/换行)切分成句子
            sentences = re.split(r'(?<=[。！？\n])', part)
            for s in sentences:
                if s.strip():
                    tokens.append({"type": "sentence", "text": s})

    # 3. 滑动窗口打包 (贪心装箱)
    chunks = []
    current_chunk_tokens = []
    current_length = 0
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        token_text = token["text"]
        token_len = len(token_text)
        
        # 【核心魔法】：如果遇到标题，强制和它的正文绑定！
        if token["type"] == "header":
            current_chunk_tokens.append(token)
            current_length += token_len
            
            # 向下预读，强制把紧跟在标题后面的正文塞进来
            i += 1
            while i < len(tokens):
                next_token = tokens[i]
                current_chunk_tokens.append(next_token)
                current_length += len(next_token["text"])
                
                # 只要吃到了一句真正的正文内容，说明标题已经“有伴儿”了，停止预读
                if next_token["type"] == "sentence" and next_token["text"].strip():
                    break
                i += 1
            i += 1
            continue

        # 【常规逻辑】：普通句子的打包与 Overlap
        if current_length + token_len > chunk_size and current_length > 0:
            # 容量满了，把当前箱子里的所有 Token 拼成字符串，封箱入库
            chunk_str = "".join([t["text"] for t in current_chunk_tokens])
            chunks.append(chunk_str.strip())
            
            # 计算 Overlap（重叠区），把箱底的一小部分内容留给下一个箱子
            overlap_length = 0
            overlap_tokens = []
            
            # 从后往前拿（这个倒序遍历极其巧妙，后面会解释为什么它天然保护标题）
            for t in reversed(current_chunk_tokens):
                if overlap_length + len(t["text"]) <= chunk_overlap:
                    overlap_tokens.insert(0, t)
                    overlap_length += len(t["text"])
                else:
                    break
                    
            # 开启新箱子：带有上一轮 overlap 的尾巴 + 当前新进来的句子
            current_chunk_tokens = overlap_tokens + [token]
            current_length = overlap_length + token_len
        else:
            # 容量还没满，继续往箱子里装句子
            current_chunk_tokens.append(token)
            current_length += token_len
            
        i += 1

    # 4. 把最后剩下的小尾巴收尾
    if current_chunk_tokens:
        chunk_str = "".join([t["text"] for t in current_chunk_tokens])
        if chunk_str.strip():
            chunks.append(chunk_str.strip())
            
    return chunks

def get_all_files():
    """获取目前在知识库（docstore）中已存储的所有文件名列表"""
    docstore_path = os.path.join(STORE_DIR, "docstore.json")
    if not os.path.exists(docstore_path):
        return []
    try:
        # 因为在更新流程中，docstore 存的是 doc_id -> parent_chunk
        # 但我们之前更新了 metadata 存 filename，但在 docstore 并没有显式记录 filename
        # 我们可以通过 chromadb collection 去获取所有不同的 filename
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        data = collection.get(include=["metadatas"])
        if not data or not data.get("metadatas"):
            return []
        
        filenames = set()
        for meta in data["metadatas"]:
            if meta and "filename" in meta:
                filenames.add(meta["filename"])
        return list(filenames)
    except Exception as e:
        print(f"获取知识库文件列表失败: {e}")
        return []

def delete_file(filename: str):
    """从 chroma DB 中删除属于某个文件的所有向量"""
    try:
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        # 根据 metadata 过滤并删除
        collection.delete(where={"filename": filename})
        # 注意：这里我们为了简便，暂不清理 docstore.json 里残留的 parent_chunks，
        # 因为向量数据库里已经没有它们，也就搜不出来了。如果想严格清理需要从 collection.get 里提取 doc_id 并从 docstore.json 里弹出。
        print(f"✅ 文件 {filename} 的向量已从数据库中删除！")
        return True
    except Exception as e:
        print(f"删除失败: {e}")
        return False

def setup_ingestion_pipeline(file_path: str, filename: str = "unknown"):
    """
    文档处理流：读取 -> 父子切分 -> 向量化导入 (纯原生 Ollama + Chroma 实现)
    """
    print(f"正在加载文档: {file_path} ({filename})")
    text_content = ""
    ext = filename.lower().split('.')[-1]
    
    if ext == "pdf":
        reader = PdfReader(file_path)
        for page in reader.pages:
            text_content += page.extract_text() + "\n"
    elif ext in ["doc", "docx"]:
        try:
            import docx
            doc = docx.Document(file_path)
            text_content = "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            print(f"读取 docx/doc 失败: {e}")
    elif ext in ["xls", "xlsx"]:
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            text_content = df.to_string(index=False)
        except Exception as e:
            print(f"读取 Excel 失败: {e}")
    else:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text_content = f.read()

    # 初始化向量数据库(用作子节点检索)
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    
    # 获取或创建集合
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    # 存储父文档的基础存储 (用最简单的 JSON 本地文件做 KV 存储)
    os.makedirs(STORE_DIR, exist_ok=True)
    docstore_path = os.path.join(STORE_DIR, "docstore.json")
    
    docstore = {}
    if os.path.exists(docstore_path):
        with open(docstore_path, 'r', encoding='utf-8') as f:
            docstore = json.load(f)

    # 这里会对 docs 先按照父文档切分，再在其内部做子块切分并入库
    print("开始切分并生成向量（这可能需要一些时间）...")
    
    parent_chunks = split_text(text_content, PARENT_CHUNK_SIZE, PARENT_CHUNK_OVERLAP)
    
    child_ids = []
    child_embeddings = []
    child_documents = []
    child_metadatas = []

    for parent_chunk in parent_chunks:
        # 使用基于内容的 MD5 哈希作为稳定的 ID
        doc_id = compute_md5(parent_chunk)
        
        # 存父文档进 dict
        docstore[doc_id] = parent_chunk
        
        # 切分子文档
        child_chunks = split_text(parent_chunk, CHILD_CHUNK_SIZE, CHILD_CHUNK_OVERLAP)
        
        valid_chunks = [ch for ch in child_chunks if ch.strip()]
        if not valid_chunks:
            continue
            
        fallback_to_local_emb = False
        if USE_ONLINE_EMBEDDING:
            try:
                from zai import ZhipuAiClient
                client = ZhipuAiClient(api_key=GLM_API_KEY)
                # 使用批处理：一次性把所有切分的子块发送给在线 API 获得 Embedding
                # 极大程度避免被在线平台的 QPS(频率限制) 直接拒绝或限流阻断
                resp = client.embeddings.create(
                    model=GLM_EMBEDDING_MODEL,
                    input=valid_chunks
                )
                for i, chunk in enumerate(valid_chunks):
                    c_id = f"{doc_id}_child_{i}"
                    child_ids.append(c_id)
                    child_embeddings.append(resp.data[i].embedding)
                    child_documents.append(chunk)
                    child_metadatas.append({"doc_id": doc_id, "filename": filename})  # 在 metadata 里指向父文档
            except Exception as e:
                print(f"⚠️ 在线 Embedding API (ingest) 调用失败: {e}，正在切换为本地 Ollama...")
                fallback_to_local_emb = True
                
        if not USE_ONLINE_EMBEDDING or fallback_to_local_emb:
            for i, chunk in enumerate(valid_chunks):
                # 调用 Ollama 原生接口获取 Embedding
                response = ollama.embeddings(
                    model=EMBEDDING_MODEL,
                    prompt=chunk
                )
                
                c_id = f"{doc_id}_child_{i}"
                child_ids.append(c_id)
                child_embeddings.append(response["embedding"])
                child_documents.append(chunk)
                child_metadatas.append({"doc_id": doc_id, "filename": filename})  # 在 metadata 里指向父文档

    # 保存父文档
    with open(docstore_path, 'w', encoding='utf-8') as f:
        json.dump(docstore, f, ensure_ascii=False)

    # 存子文档（并生成向量到 Chroma）
    if child_ids:
        # --- 新增：打印写入向量数据库的内容（限制前几个避免严重刷屏） ---
        print("\n" + "📥"*20)
        print(f">> [输入] 即将写入向量数据库的子块，共计 {len(child_documents)} 个片段:")
        for idx, doc in enumerate(child_documents): 
            print(f"\n++++++++++【入库片段录入 {idx+1}/{len(child_documents)}】++++++++++\n{doc}\n----------------------------------")
        print("📥"*20 + "\n")
        
        # Chroma 的 add 方法如果遇到相同的 ID 会报错，使用 upsert 可实现存在即覆盖（幂等）
        batch_size = 100
        for i in range(0, len(child_ids), batch_size):
            collection.upsert(
                ids=child_ids[i:i+batch_size],
                embeddings=child_embeddings[i:i+batch_size],
                documents=child_documents[i:i+batch_size],
                metadatas=child_metadatas[i:i+batch_size]
            )
    print("入库完成！")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(BASE_DIR, "data.txt")
    if os.path.exists(data_path):
        setup_ingestion_pipeline(data_path)
    else:
        print(f"未找到 {data_path}")

