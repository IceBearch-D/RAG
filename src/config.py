import os

# --- 项目根目录 ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- 运行模式配置 ---
USE_ONLINE_LLM = False       # True使用在线GLM模型，False使用本地Ollama模型
USE_ONLINE_EMBEDDING = False # True使用在线GLM向量模型，False使用本地Ollama向量模型

# --- 在线GLM API配置 ---
GLM_API_KEY = "c0731891114141b5aedf468eac502b20.MtiZzh4m30arkHeE" # error api
GLM_LLM_MODEL = "glm-4.7-flash"
GLM_EMBEDDING_MODEL = "embedding-3"

# --- 大模型与向量模型配置(本地Ollama) ---
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "deepseek-r1:8b"
EMBEDDING_MODEL = "nomic-embed-text"

# --- 向量数据库与存储配置 ---
CHROMA_PERSIST_DIR = os.path.join(BASE_DIR, "chroma_db")
STORE_DIR = os.path.join(BASE_DIR, "store_db")  # 父文档本地存储库路径
COLLECTION_NAME = "advanced_rag_collection"

# --- 切分与检索配置 ---
PARENT_CHUNK_SIZE = 1000
PARENT_CHUNK_OVERLAP = 100
CHILD_CHUNK_SIZE = 200
CHILD_CHUNK_OVERLAP = 50

# --- 重排配置 ---
RERANKER_MODEL = "BAAI/bge-reranker-base"
TOP_K_RETRIEVAL = 10  # 多查询扩展后单路召回数量
TOP_K_RERANK = 3      # 重排后返回给模型的最终数量

# --- 日志配置 ---
LOG = True                                    # True: 记录日志; False: 关闭日志输出
LOG_DIR = os.path.join(BASE_DIR, "logs")     # 日志文件存储目录
LOG_LEVEL = "INFO"                           # 日志级别: DEBUG, INFO, WARNING, ERROR
