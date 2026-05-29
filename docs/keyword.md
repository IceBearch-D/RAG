# RAG 体系专业名词全表（按工作流程排列）

---

## 阶段一：离线索引构建（Indexing Pipeline）

### 1. 数据接入层

| 序号 | 名词 | 简要介绍 |
|---|---|---|
| 1 | **Data Connector（数据连接器）** | 用于对接各类数据源（数据库、API、文件系统、网页等）的统一抽象接口，负责数据的采集与增量同步 |
| 2 | **ETL（Extract-Transform-Load）** | 数据的抽取-转换-加载流程，在 RAG 中指从原始数据源抽取文档、转换为统一格式、加载到处理管道中的过程 |
| 3 | **Data Ingestion（数据摄取）** | 将外部数据源中的文档导入 RAG 系统的过程，包含格式识别、编码转换、去重等预处理 |

### 2. 文档解析层

| 序号 | 名词 | 简要介绍 |
|---|---|---|
| 4 | **Document Parser（文档解析器）** | 将 PDF、Word、PPT、HTML 等各种格式的文档转换为结构化纯文本的工具或模块 |
| 5 | **OCR（Optical Character Recognition，光学字符识别）** | 将图片、扫描件中的文字识别为可编辑文本的技术，用于处理扫描版 PDF、图片中的文字 |
| 6 | **Layout Analysis（版面分析）** | 识别文档中不同区域的功能（标题、正文、表格、图片、页眉页脚等），保留文档的结构层次信息 |
| 7 | **Table Extraction（表格抽取）** | 从文档中识别并提取表格，将其转化为结构化格式（如 Markdown、HTML table、JSON），保留行列关系 |

### 3. 文档分块层

| 序号 | 名词 | 简要介绍 |
|---|---|---|
| 8 | **Chunking / Splitting（分块）** | 将长文档切分为较短片段的过程，使每个片段适合 Embedding 模型处理且语义完整 |
| 9 | **Chunk Size（块大小）** | 每个分块的最大长度（通常以 token 计），常见范围 256~1024 tokens，是影响检索精度的核心参数 |
| 10 | **Chunk Overlap（块重叠）** | 相邻两个分块之间的重叠长度，防止关键信息恰好被切在边界处而丢失上下文，通常为 chunk size 的 10%~20% |
| 11 | **Recursive Splitting（递归分块）** | 按层级分隔符（`\n\n` → `\n` → `.` → 空格）递归切分文档的策略，优先在自然段落边界处切分，是工业级最常用的分块方法 |
| 12 | **Semantic Chunking（语义分块）** | 通过计算相邻句子之间的语义相似度，在相似度骤降的位置进行切分，使每个块内部语义连贯 |
| 13 | **Sliding Window（滑动窗口）** | 以固定窗口大小和固定步长滑动切分文本，窗口之间有重叠，保证上下文的连续性 |
| 14 | **Sentence Window（句子窗口）** | 以单个句子为检索单元，但返回时扩展到包含该句子前后若干句的窗口，兼顾检索精度和上下文完整性 |

### 4. 向量化层

| 序号 | 名词 | 简要介绍 |
|---|---|---|
| 15 | **Embedding（向量嵌入）** | 将文本映射为固定维度的稠密向量（如 768 维），使语义相近的文本在向量空间中距离接近，是向量检索的基础 |
| 16 | **Embedding Model（嵌入模型）** | 执行 Embedding 的模型，如 BGE、GTE、text-embedding-3、Jina 等，通过对比学习训练得到语义表示能力 |
| 17 | **Dense Vector（稠密向量）** | Embedding 模型输出的向量，每个维度都有非零值，包含压缩后的语义信息，与稀疏向量（如 BM25 的 TF-IDF 向量）相对 |
| 18 | **Dimension（向量维度）** | Embedding 向量的维度数，如 768、1024、1536 等，维度越高信息容量越大，但存储和计算成本也越高 |
| 19 | **Cosine Similarity（余弦相似度）** | 衡量两个向量方向接近程度的指标，值域 [-1,1]，L2 归一化后与内积等价，是 RAG 中最常用的相关性度量方式 |
| 20 | **L2 Normalization（L2 归一化）** | 将向量缩放为单位长度（模长为 1）的操作，归一化后余弦相似度等于内积，可加速计算 |
| 21 | **Contrastive Learning（对比学习）** | Embedding 模型的训练范式，通过拉近正样本对、推远负样本对来学习语义表示，核心损失函数为 InfoNCE Loss |
| 22 | **InfoNCE Loss** | 对比学习中的损失函数，通过 softmax 形式最大化正样本对的相似度同时最小化负样本对的相似度，是训练 Embedding 模型的数学基础 |

### 5. 向量存储层

| 序号 | 名词 | 简要介绍 |
|---|---|---|
| 23 | **Vector Database（向量数据库）** | 专门用于存储和检索高维向量的数据库，支持高效的近似最近邻搜索（ANN），如 Milvus、Qdrant、Weaviate、ChromaDB 等 |
| 24 | **ANN（Approximate Nearest Neighbor，近似最近邻）** | 在海量向量中快速找到与查询向量最相似的 Top-K 个向量的算法，牺牲少量精度换取极大速度提升 |
| 25 | **HNSW（Hierarchical Navigable Small World）** | 最主流的 ANN 索引算法，构建多层图结构，从顶层入口点逐层贪心搜索到底层，时间复杂度 O(log N) |
| 26 | **IVF（Inverted File Index，倒排文件索引）** | 先用聚类将向量空间划分为若干区域（Voronoi cell），检索时只在最近的几个区域中搜索，减少搜索范围 |
| 27 | **PQ（Product Quantization，乘积量化）** | 将高维向量压缩为紧凑编码的技术，大幅减少内存占用，适合资源受限场景下的大规模向量检索 |
| 28 | **Metadata Filtering（元数据过滤）** | 在向量检索时附加结构化条件过滤（如按时间、来源、权限标签等），先过滤再搜索或先搜索再过滤 |
| 29 | **Payload（负载数据）** | 向量数据库中与向量一起存储的附加信息（原始文本、来源、时间戳等），用于结果展示和过滤 |

---

## 阶段二：在线检索（Retrieval Pipeline）

### 6. Query 理解与预处理层

| 序号 | 名词 | 简要介绍 |
|---|---|---|
| 30 | **Query Rewriting（查询改写）** | 将用户口语化、省略、模糊的 Query 改写为更明确、更适合检索的形式，如"那个东西怎么退" → "如何申请商品退货退款" |
| 31 | **Query Expansion（查询扩展）** | 在原始 Query 的基础上添加同义词、相关词，扩大检索召回范围，如"退款" 扩展为 "退款 OR 退货 OR 退换" |
| 32 | **Query Decomposition（查询分解）** | 将复杂的复合 Query 拆解为多个简单的子问题分别检索，提高每个子问题的检索精度 |
| 33 | **HyDE（Hypothetical Document Embeddings）** | 让 LLM 先生成一个"假设性回答"，用这个回答的 Embedding 去检索而非用原始 Query，因为假设性回答的表述风格更接近文档内容 |
| 34 | **Intent Recognition（意图识别）** | 判断用户 Query 的意图类型（知识问答、闲聊、操作指令等），将不同意图路由到不同的处理管道 |
| 35 | **Step-Back Prompting** | 将具体问题抽象为更高层级的问题，同时用原始 Query 和抽象 Query 检索，提高信息覆盖面 |

### 7. 检索层

| 序号 | 名词 | 简要介绍 |
|---|---|---|
| 36 | **Dense Retrieval（稠密检索）** | 使用 Embedding 模型将 Query 和 Document 编码为稠密向量，通过向量相似度进行匹配的检索方式 |
| 37 | **Sparse Retrieval（稀疏检索）** | 基于词频统计的传统检索方式（如 BM25），使用稀疏向量表示文本，擅长精确关键词匹配 |
| 38 | **BM25（Best Matching 25）** | 经典的稀疏检索算法，综合考虑词频（TF）、逆文档频率（IDF）和文档长度归一化来计算相关性分数 |
| 39 | **TF-IDF（Term Frequency-Inverse Document Frequency）** | BM25 的前身，通过词频和逆文档频率的乘积衡量词对文档的重要程度，是最基础的文本相关性计算方法 |
| 40 | **Hybrid Search（混合检索）** | 同时使用向量检索和关键词检索（BM25），通过融合算法合并结果，取两种方式各自的优势 |
| 41 | **Multi-Route Retrieval（多路召回）** | 使用多种不同的检索策略（向量、BM25、知识图谱等）分别召回候选文档，最大化召回率 |
| 42 | **Reciprocal Rank Fusion（RRF，倒数排名融合）** | 多路检索结果的融合算法，将文档在各路中的排名取倒数求和，不依赖各路的原始分数，简单有效 |

### 8. 重排序层

| 序号 | 名词 | 简要介绍 |
|---|---|---|
| 43 | **Reranking（重排序）** | 在粗排召回的候选集上，使用更精细的模型重新打分排序的过程，是提升检索精度的关键步骤 |
| 44 | **Bi-Encoder（双塔模型）** | 粗排阶段使用的模型架构，Query 和 Document 各自独立编码为向量，通过向量点积计算相关性，速度快但精度有限 |
| 45 | **Cross-Encoder（交叉编码器）** | 精排（Reranking）阶段使用的模型架构，将 Query 和 Document 拼接后联合输入 Transformer，通过多层 Self-Attention 实现 token 级全量交互，精度远高于双塔 |
| 46 | **Self-Attention（自注意力机制）** | Transformer 的核心机制，每个 token 可以计算与序列中所有其他 token 的注意力权重，实现全局信息交互，是 Cross-Encoder 高精度的底层原因 |
| 47 | **[CLS] Token** | BERT 等模型在输入序列开头添加的特殊 token，其最终隐藏状态被用作整个序列的聚合表示，Cross-Encoder 用它来计算相关性分数 |

### 9. 后处理层

| 序号 | 名词 | 简要介绍 |
|---|---|---|
| 48 | **Top-K** | 从排序结果中取分数最高的 K 个文档片段，K 的取值直接影响注入 LLM 的信息量和 Token 消耗 |
| 49 | **Relevance Threshold（相关性阈值）** | 设定一个分数门槛，低于该阈值的检索结果直接丢弃，避免低质量片段污染 LLM 的上下文 |
| 50 | **MMR（Maximal Marginal Relevance，最大边际相关性）** | 在选择文档时同时考虑与 Query 的相关性和与已选文档的多样性，避免返回内容高度重复的片段 |
| 51 | **Deduplication（去重）** | 移除内容高度相似或重复的检索结果，减少上下文中的信息冗余，节省 Token |
| 52 | **Context Compression（上下文压缩）** | 对检索到的片段进行摘要或裁剪，只保留与 Query 最相关的部分，减少注入 LLM 的无关信息 |

---

## 阶段三：生成（Generation Pipeline）

### 10. Prompt 组装层

| 序号 | 名词 | 简要介绍 |
|---|---|---|
| 53 | **Prompt Engineering（提示工程）** | 设计和优化输入给 LLM 的 Prompt 模板的技术，包括指令措辞、上下文组织、输出格式约束等 |
| 54 | **System Prompt（系统提示词）** | 定义 LLM 角色、行为规则和约束条件的指令，如"严格根据参考资料回答""不允许编造""需要标注来源" |
| 55 | **Context Window（上下文窗口）** | LLM 单次能处理的最大 Token 数量，RAG 中需要在 Context Window 内合理分配系统指令、参考资料和生成空间 |
| 56 | **Token** | LLM 处理文本的最小单位，中文约 1~2 个字为一个 token，英文约 0.75 个单词为一个 token，是计算成本和窗口管理的基本计量单位 |
| 57 | **Citation / Attribution（引用标注）** | 在生成的回答中标注每条信息来源于哪个检索片段（如"根据[文档A]第3页"），增强回答的可溯源性 |

### 11. LLM 生成层

| 序号 | 名词 | 简要介绍 |
|---|---|---|
| 58 | **LLM（Large Language Model，大语言模型）** | RAG 中负责理解问题并生成回答的核心模块，如 GPT-4、Qwen、DeepSeek、GLM 等 |
| 59 | **Hallucination（幻觉）** | LLM 生成看似合理但实际上不正确或无依据的内容的现象，RAG 的核心目标之一就是通过外部知识锚定来缓解幻觉 |
| 60 | **Grounding（接地/锚定）** | 让 LLM 的生成内容基于外部检索到的事实依据而非内部参数中的记忆，RAG 本质上就是一种 Grounding 技术 |
| 61 | **Temperature（温度）** | 控制 LLM 生成随机性的参数，值越高输出越多样/随机，值越低输出越确定/保守，RAG 场景通常设为较低值（0~0.3） |
| 62 | **Streaming（流式输出）** | LLM 逐 token 生成并实时返回给用户的技术（通过 SSE 或 WebSocket），减少用户感知的等待时间 |
| 63 | **Token Budget（Token 预算）** | 在 Context Window 限制下，为系统指令、检索上下文、用户问题和生成回答各分配的 Token 数量上限 |

### 12. 后处理层

| 序号 | 名词 | 简要介绍 |
|---|---|---|
| 64 | **Faithfulness Check（忠实度校验）** | 验证 LLM 生成的回答是否忠于检索到的参考资料，检测是否存在与原文矛盾或无中生有的内容 |
| 65 | **Hallucination Detection（幻觉检测）** | 自动识别生成回答中可能存在的幻觉内容的技术，通常通过将回答与检索片段做逐句交叉比对实现 |
| 66 | **Post-processing（后处理）** | LLM 输出后的格式化、引用验证、敏感信息过滤、重复内容去除等操作的总称 |

---

## 横向贯穿：进阶架构与评估

### 13. 高级 RAG 架构

| 序号 | 名词 | 简要介绍 |
|---|---|---|
| 67 | **Naive RAG（朴素 RAG）** | 最基础的 RAG 模式：检索 → 拼接 → 生成，无查询优化、无重排序、无迭代，即"检索 + 生成"的直接串联 |
| 68 | **Advanced RAG（进阶 RAG）** | 在 Naive RAG 基础上加入查询改写、混合检索、Reranking、上下文压缩等优化技术的增强方案 |
| 69 | **Modular RAG（模块化 RAG）** | 将 RAG 拆解为可插拔的模块（检索器、重排器、生成器等），各模块可独立替换和优化，提高系统灵活性 |
| 70 | **Self-RAG（自反思 RAG）** | LLM 在生成过程中自主判断是否需要检索、检索结果是否相关、回答是否被证据支持，通过输出特殊反思 token 实现自适应决策 |
| 71 | **Agentic RAG（智能体 RAG）** | 用 Agent（智能体）控制 RAG 流程，支持多轮迭代检索、动态规划、工具调用等复杂决策逻辑 |
| 72 | **Corrective RAG（纠正式 RAG）** | 在生成前对检索结果进行质量评估，若检测到不相关或矛盾的内容则触发重新检索或修正 |
| 73 | **Graph RAG（图 RAG）** | 将文档中的实体和关系构建成知识图谱，在检索时结合图遍历进行多跳推理，适合需要关系推理的问答场景 |
| 74 | **Knowledge Graph（知识图谱）** | 以三元组（实体-关系-实体）形式存储结构化知识的图结构数据库，如 Neo4j，可支持复杂的多跳关系推理 |
| 75 | **Multimodal RAG（多模态 RAG）** | 能处理和检索文本、图片、表格、音频等多种模态信息的 RAG 系统，需要多模态 Embedding 或视觉语言模型的支持 |

### 14. 评估体系

| 序号 | 名词 | 简要介绍 |
|---|---|---|
| 76 | **RAGAS** | 业界最常用的 RAG 自动化评估框架，包含四个核心指标，用 LLM 自动评估检索和生成质量 |
| 77 | **Faithfulness（忠实度）** | RAGAS 指标之一，衡量生成回答中的每条陈述是否能从检索到的上下文中找到支撑依据 |
| 78 | **Answer Relevancy（回答相关性）** | RAGAS 指标之一，衡量生成的回答与用户原始问题的相关程度，回答是否切题 |
| 79 | **Context Precision（上下文精确率）** | RAGAS 指标之一，衡量检索到的上下文中真正与问题相关的片段占比（检索的精确程度） |
| 80 | **Context Recall（上下文召回率）** | RAGAS 指标之一，衡量参考标准答案中的信息被检索到的上下文覆盖了多少（检索的召回程度） |
| 81 | **Recall@K** | 在 Top-K 个检索结果中包含至少一个相关文档的比例，衡量检索系统的召回能力 |
| 82 | **MRR（Mean Reciprocal Rank，平均倒数排名）** | 第一个相关结果排名的倒数的均值，排名越靠前 MRR 越高，衡量相关文档是否排在前面 |
| 83 | **nDCG（Normalized Discounted Cumulative Gain）** | 考虑排名位置权重的评估指标，排在前面的相关文档贡献更大，衡量排序质量 |
| 84 | **LLM-as-Judge** | 用强大的 LLM（如 GPT-4）作为评判者自动给 RAG 回答打分的评估方法，可部分替代人工评估 |
| 85 | **A/B Testing（A/B 测试）** | 在线上将用户随机分为两组，分别使用不同版本的 RAG 系统，通过统计用户满意度指标来比较方案优劣 |

### 15. 工程框架

| 序号 | 名词 | 简要介绍 |
|---|---|---|
| 86 | **LangChain** | 最流行的 LLM 应用开发框架，提供文档加载、分块、Embedding、向量存储、检索、链式调用等 RAG 全流程组件 |
| 87 | **LlamaIndex** | 专注于数据索引和检索的 LLM 框架，提供丰富的索引结构（向量索引、树索引、知识图谱索引等）和查询引擎 |
| 88 | **LangGraph** | LangChain 生态中的状态图（StateGraph）框架，用于构建 Agentic RAG 等需要多步决策和循环的工作流 |
| 89 | **Embedding API** | 调用远程 Embedding 模型服务的接口，如 OpenAI Embeddings API、Cohere Embed API 等 |
| 90 | **Pipeline（管道）** | 将多个处理步骤串联为一条自动化流水线的设计模式，RAG 的离线索引和在线检索各构成一条 Pipeline |

---

## 速查：按流程节点的一句话串联

```
Data Connector → Document Parser（OCR / Layout Analysis / Table Extraction）
    → Chunking（Recursive Splitting / Chunk Size / Chunk Overlap / Semantic Chunking）
    → Embedding Model（Contrastive Learning / InfoNCE Loss / Dense Vector / Cosine Similarity）
    → Vector Database（ANN / HNSW / IVF / PQ / Metadata Filtering）

用户 Query → Query Rewriting（HyDE / Query Decomposition / Step-Back）
    → Multi-Route Retrieval（Dense Retrieval + Sparse Retrieval(BM25/TF-IDF)）
    → RRF 融合
    → Reranking（Bi-Encoder 粗排 → Cross-Encoder 精排 / Self-Attention / [CLS] Token）
    → Top-K / Relevance Threshold / MMR 去重 / Context Compression

Prompt Assembly（System Prompt / Context Window / Token Budget / Citation）
    → LLM Generation（Hallucination / Grounding / Temperature / Streaming）
    → Post-processing（Faithfulness Check / Hallucination Detection）

评估：RAGAS（Faithfulness / Answer Relevancy / Context Precision / Context Recall）
     + Recall@K / MRR / nDCG / LLM-as-Judge / A/B Testing
```

以上 90 个名词覆盖了 RAG 从数据处理到最终生成的完整链路，在面试中能系统地、有层次地提及这些概念，可以体现对 RAG 落地方案的全面理解。