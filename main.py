import os
import sys
import json
import google.generativeai as genai
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from typing import List, Dict

# OAuth 範圍
SCOPES = ['https://www.googleapis.com/auth/generative-language.retriever']
HISTORY_FILE = "history.json"

# 定義系統指令
SYSTEM_INSTRUCTION = """
你是一位專業的資深台灣軟體工程師，具備分析專案程式碼與記憶對話脈絡的能力。
你的行為準則：
1. 使用繁體中文回應，保持專業但輕鬆的口吻。
2. 根據「專案上下文」與「過去的對話紀錄」進行回答。
3. 保持回應精簡、直接。
"""

class ProjectAnalyzer:
    """負責掃描並讀取專案檔案內容"""
    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir
        self.ignore_dirs = {'.git', '.venv', '__pycache__', '.pytest_cache', '.gemini'}
        self.ignore_files = {'uv.lock', '.python-version', '.gitignore', 'token.json', 'client_secret.json', HISTORY_FILE}

    def get_project_context(self) -> str:
        """收集專案結構與檔案內容"""
        context = ["這是一個專案的原始碼上下文：\n"]
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            for file in files:
                if file in self.ignore_files:
                    continue
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        context.append(f"--- FILE: {os.path.relpath(file_path, self.root_dir)} ---\n{content}\n")
                except:
                    continue
        return "\n".join(context)

def authenticate():
    """處理 OAuth2 認證流程"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('client_secret.json'):
                print("錯誤：找不到 client_secret.json")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def load_history() -> List[Dict]:
    """從檔案載入對話歷史"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history: List):
    """將對話歷史儲存到檔案"""
    serializable_history = []
    for content in history:
        serializable_history.append({
            "role": content.role,
            "parts": [part.text for part in content.parts]
        })
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(serializable_history, f, ensure_ascii=False, indent=2)

def setup_gemini():
    """初始化 Gemini API"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
    else:
        genai.configure(credentials=authenticate())
    
    return genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=SYSTEM_INSTRUCTION
    )

def main():
    model = setup_gemini()
    analyzer = ProjectAnalyzer()
    
    print("正在掃描專案並載入歷史紀錄...")
    project_context = analyzer.get_project_context()
    history_data = load_history()
    
    # 啟動對話 Session
    chat = model.start_chat(history=history_data)
    
    # 如果是第一次對話，注入專案上下文
    is_new_session = len(history_data) == 0

    def send_message(prompt: str):
        nonlocal is_new_session
        # 只有在 Session 開始的第一個 prompt 注入專案上下文，避免 Token 浪費
        current_prompt = f"{project_context}\n\n{prompt}" if is_new_session else prompt
        
        try:
            response = chat.send_message(current_prompt, stream=True)
            print("\nGemini: ", end="", flush=True)
            for chunk in response:
                if chunk.text:
                    print(chunk.text, end="", flush=True)
            print("\n")
            save_history(chat.history)
            is_new_session = False
        except Exception as e:
            print(f"\n發生錯誤：{str(e)}")

    if len(sys.argv) > 1:
        send_message(" ".join(sys.argv[1:]))
    else:
        print("--- Gemini 專業助理 (具備對話記憶) ---")
        print("(輸入 'clear' 清除歷史紀錄，輸入 'quit' 退出)")
        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ['quit', 'exit']:
                    break
                if user_input.lower() == 'clear':
                    if os.path.exists(HISTORY_FILE):
                        os.remove(HISTORY_FILE)
                    chat = model.start_chat(history=[])
                    is_new_session = True
                    print("對話紀錄已清除。")
                    continue
                if not user_input.strip():
                    continue
                send_message(user_input)
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    main()
