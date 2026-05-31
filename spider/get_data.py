import os
import re
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

def scrape_all_sections():
    # 四个模块的入口网页及对应模块名
    sections = [
        {"name": "Agent", "url": "https://xiaolinnote.com/ai/agent/agent_info.html"},
        {"name": "RAG", "url": "https://xiaolinnote.com/ai/rag/rag_info.html"},
        {"name": "LLM工具", "url": "https://xiaolinnote.com/ai/tools/tools_info.html"},
        {"name": "大模型工程", "url": "https://xiaolinnote.com/ai/llm/llm_info.html"}
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    output_file = "all_xiaolinnote_chapters.txt"
    
    # 清空或创建结果文件
    with open(output_file, "w", encoding='utf-8') as f:
        f.write("")
        
    total_pages_scraped = 0
    
    for section in sections:
        section_name = section["name"]
        base_url = section["url"]
        
        try:
            print(f"正在获取【{section_name}】基础网页以解析左侧导航栏: {base_url}")
            response = requests.get(base_url, headers=headers)
            response.raise_for_status()
            response.encoding = 'utf-8' 
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 寻找侧边栏容器
            sidebar = soup.find('aside', class_='vp-sidebar')
            if not sidebar:
                print(f"❌ 无法找到【{section_name}】的侧边栏容器，跳过。")
                continue

            # 提取所有的子链接
            link_tags = sidebar.find_all('a')
            
            # 去重存放页面URL
            page_urls = []
            for tag in link_tags:
                href = tag.get('href')
                if href and not href.startswith('#'):
                    full_url = urljoin(base_url, href)
                    full_url = full_url.split('#')[0]
                    if full_url not in page_urls:
                        page_urls.append(full_url)
                        
            print(f"✅ 在【{section_name}】侧边栏中共找到了 {len(page_urls)} 个文章页面。\n")
            
            # 遍历每个URL进行爬取
            for i, url in enumerate(page_urls, 1):
                print(f"[{section_name} - {i}/{len(page_urls)}] 正在爬取: {url}")
                try:
                    res = requests.get(url, headers=headers)
                    res.raise_for_status()
                    res.encoding = 'utf-8'
                    page_soup = BeautifulSoup(res.text, 'html.parser')
                    
                    # 取出正文
                    main_tag = page_soup.find('main')
                    if main_tag:
                        text_content = main_tag.get_text(separator='\n', strip=True)
                    else:
                        text_content = page_soup.body.get_text(separator='\n', strip=True) if page_soup.body else page_soup.get_text(separator='\n', strip=True)
                    
                    # 命名标题
                    title_tag = page_soup.find('title')
                    raw_title = title_tag.text if title_tag else f"Chapter {i}"
                    
                    # 组合成：对应html名 + 文章页面编号 + 文章题目
                    block_title = f"{section_name} {i:02d} {raw_title}"
                    
                    # 写入总 txt 文件
                    with open(output_file, "a", encoding='utf-8') as f:
                        f.write(f"\n{'='*60}\n")
                        f.write(f"{block_title}\n")
                        f.write(f"{'='*60}\n\n")
                        f.write(text_content)
                        f.write("\n\n")
                        
                    total_pages_scraped += 1
                        
                except Exception as e:
                    print(f"  ❌ 爬取 {url} 时出错: {e}")
            
        except Exception as e:
            print(f"❌ 解析【{section_name}】章节出错: {e}")
            
    print(f"\n🎉 恭喜！所有模块共计 {total_pages_scraped} 篇文章网页已经全部爬取并整合完成！")
    print(f"结果储存在文件: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    scrape_all_sections()
