import os
import sys
import google.generativeai as genai
from typing import List, Dict

# 定義系統指令
SYSTEM_INSTRUCTION = """
你是一位專業的資深台灣軟體工程師，現在你具備了「分析當前專案程式碼」的能力。
你的行為準則：
1. 使用繁體中文回應，保持專業但輕鬆的口吻。
2. 當使用者詢問關於專案的問題時，請根據我提供的「專案上下文」進行回答。
3. 如果使用者要求修改程式碼，請確保你的建議符合現有的架構與命名慣例。
4. 若資訊不足以回答問題，請直接告知。
"""

class ProjectAnalyzer:
    """負責掃描並讀取專案檔案內容"""
    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir
        self.ignore_dirs = {'.git', '.venv', '__pycache__', '.pytest_cache', '.gemini'}
        self.ignore_files = {'uv.lock', '.python-version', '.gitignore'}

    def get_project_context(self) -> str:
        """收集專案結構與檔案內容"""
        context = ["這是一個專案的原始碼上下文：\n"]
        
        for root, dirs, files in os.walk(self.root_dir):
            # 過濾掉不需要的目錄
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for file in files:
                if file in self.ignore_files:
                    continue
                
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, self.root_dir)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        context.append(f"--- FILE: {relative_path} ---\n{content}\n")
                except Exception:
                    # 跳過二進位檔案或讀取失敗的檔案
                    continue
        
        return "\n".join(context)

def setup_gemini():
    """初始化 Gemini API"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("錯誤：請先設置環境變數 GOOGLE_API_KEY")
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=SYSTEM_INSTRUCTION
    )

def chat_with_llm(model: genai.GenerativeModel, prompt: str, context: str = ""):
    """與 LLM 對話，並注入專案上下文"""
    # 將上下文與使用者的問題結合
    full_prompt = f"{context}\n\n使用者問題：{prompt}" if context else prompt
    
    try:
        response = model.generate_content(full_prompt, stream=True)
        print("\nGemini: ", end="", flush=True)
        for chunk in response:
            if chunk.text:
                print(chunk.text, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"\n發生錯誤：{str(e)}")

def main():
    model = setup_gemini()
    analyzer = ProjectAnalyzer()
    
    # 預先載入專案上下文
    print("正在掃描專案檔案以建立 RAG 上下文...")
    project_context = analyzer.get_project_context()
    print(f"掃描完成。")

    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        chat_with_llm(model, user_input, project_context)
    else:
        print("--- Gemini 專案分析模式 (輸入 'quit' 退出) ---")
        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ['quit', 'exit']:
                    break
                if not user_input.strip():
                    continue
                chat_with_llm(model, user_input, project_context)
            except KeyboardInterrupt:
                print("\n已退出。")
                break

if __name__ == "__main__":
    main()
