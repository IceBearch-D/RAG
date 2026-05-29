import os

app_content = """import os
os.environ['TRANSFORMERS_VERBOSITY']='error'
os.environ['TOKENIZERS_PARALLELISM']='false'
import streamlit as st
import tempfile
import warnings
from chain import NativeRAGChain
from ingest import setup_ingestion_pipeline, get_all_files, delete_file

# 忽略 transformers 的部分烦人警告
warnings.filterwarnings("ignore", message=".*Accessing `__path__` from.*")

st.set_page_config(page_title="大模型实习生学习系统", layout="wide")

# ================= 左侧导航栏 =================
with st.sidebar:
    st.title("👨‍🚀 导航栏")
    page = st.radio("选择模块", ["1. 💬 聊天模块", "2. 📄 文件管理"])

# 初始化后端 Chain
@st.cache_resource
def get_chain():
    return NativeRAGChain()

rag_chain = get_chain()

if page == "1. 💬 聊天模块":
    # ================= 主界面：对话窗口 =================
    st.title("👨‍🎓 大模型实习生学习系统")
    st.markdown("**(DeepSeek-R1 + Multi-Query + Parent-Child Retriever + Cross-Encoder Reranker)**")
    st.markdown("*注：系统采用原生的ollama-python库开发，零绑定LangChain，逻辑清晰度极高。*")

    # 初始化聊天历史
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 显示界面上的历史消息
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and "<think>" in msg["content"]:
                # 在历史记录中分离并折叠思考过程
                parts = msg["content"].split("</think>")
                think_part = parts[0].replace("<think>", "").strip()
                answer_part = parts[1].strip() if len(parts) > 1 else ""
                with st.expander("🤔 历史思考过程"):
                    st.markdown(think_part)
                st.markdown(answer_part)
            else:
                st.markdown(msg["content"])

    user_input = st.chat_input("请输入您的问题...")

    if user_input:
        # 立即展示用户输入
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # 构造历史列表
        chat_history = []
        for msg in st.session_state.messages[:-1]:
            role = "human" if msg["role"] == "user" else "ai"
            chat_history.append((role, msg["content"]))
        
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            # 为了处理 DeepSeek-R1 的 <think> 标签所展现的思考状态
            st_think_container = st.expander("🤔 DeepSeek-R1 正在思考（多查询+文档重排已介入）...", expanded=True)
            think_text_placeholder = st_think_container.empty()
            final_answer_placeholder = st.empty()

            # 开始流式调用大模型
            full_response = ""
            
            # Generator 形式提取流式回答内容
            import re
            import time
            for chunk in rag_chain.stream_answer(user_input, chat_history):
                full_response += chunk
                
                think_match_closed = re.search(r'<think>(.*?)</think>', full_response, re.DOTALL | re.IGNORECASE)
                if think_match_closed:
                    think_content = think_match_closed.group(1).strip()
                    answer_content = re.split(r'</think>', full_response, flags=re.IGNORECASE)[-1].strip()
                    think_text_placeholder.markdown(think_content)
                    final_answer_placeholder.markdown(answer_content + '▌')
                else:
                    think_match_open = re.search(r'<think>(.*)', full_response, re.DOTALL | re.IGNORECASE)
                    if think_match_open:
                        think_content = think_match_open.group(1).strip()
                        think_text_placeholder.markdown(think_content + '▌')
                    else:
                        answer_content = full_response
                        final_answer_placeholder.markdown(answer_content + '▌')
                time.sleep(0.01)

            answer_content_final = ""
            if "<think>" in full_response:
                ans_split = re.split(r'</think>', full_response, flags=re.IGNORECASE)
                if len(ans_split) > 1:
                    answer_content_final = ans_split[-1].strip()
            else:
                answer_content_final = full_response
                 
            final_answer_placeholder.markdown(answer_content_final)
            
        st.session_state.messages.append({"role": "assistant", "content": full_response})

elif page == "2. 📄 文件管理":
    st.title("📄 知识库文件管理")
    st.markdown("在此模块中，您可以上传支持的格式文件（**txt, md, docx, pdf, xlsx**）到向量数据库，也可以删除不再需要的文件。")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 文件上传入库")
        uploaded_file = st.file_uploader("选择文档", type=["txt", "md", "pdf", "docx", "doc", "xlsx", "xls"])
        
        if st.button("处理并入库", type="primary"):
            if uploaded_file is not None:
                with st.spinner("正在切分文档并生成向量（这可能需要一些时间）..."):
                    # 将上传的文件保存到临时路径
                    ext = uploaded_file.name.split('.')[-1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    try:
                        # 调用 ingest.py 中的处理函数
                        setup_ingestion_pipeline(tmp_file_path, uploaded_file.name)
                        st.success(f"✅ 文件 {uploaded_file.name} 已成功入库！")
                    except Exception as e:
                        st.error(f"入库失败: {str(e)}")
                    finally:
                        # 清理临时文件
                        if os.path.exists(tmp_file_path):
                            os.remove(tmp_file_path)
            else:
                st.warning("⚠️ 请先选择一个文件！")
                
    with col2:
        st.subheader("🗑️ 文件删除")
        files_in_db = get_all_files()
        
        if not files_in_db:
            st.info("当前向量数据库中没有文件。")
        else:
            selected_file = st.selectbox("选择要删除的文件：", files_in_db)
            if st.button("删除文件", type="primary", key="btn_del"):
                with st.spinner(f"正在从知识库中删除 {selected_file}..."):
                    success = delete_file(selected_file)
                    if success:
                        st.success(f"✅ 文件 {selected_file} 已成功从数据库中删除！")
                        st.rerun()
                    else:
                        st.error("删除失败！")
"""

with open("e:/document/PycharmProjects/RAG/src/app.py", "w", encoding="utf-8") as f:
    f.write(app_content)
