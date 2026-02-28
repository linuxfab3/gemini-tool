import os
import sys
import google.generativeai as genai
from typing import Optional

def setup_gemini():
    """初始化 Gemini API 配置"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("錯誤：請先設置環境變數 GOOGLE_API_KEY")
        print("例如：$env:GOOGLE_API_KEY='your_api_key_here' (PowerShell)")
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

def chat_with_llm(model: genai.GenerativeModel, prompt: str):
    """與 LLM 進行串流對話"""
    try:
        response = model.generate_content(prompt, stream=True)
        print("\nGemini: ", end="", flush=True)
        for chunk in response:
            if chunk.text:
                print(chunk.text, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"\n發生錯誤：{str(e)}")

def main():
    """進入點：支援命令列參數或互動模式"""
    model = setup_gemini()
    
    # 檢查是否有命令列輸入
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        chat_with_llm(model, user_input)
    else:
        print("--- Gemini 互動模式 (輸入 'quit' 退出) ---")
        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ['quit', 'exit', 'exit()']:
                    break
                if not user_input.strip():
                    continue
                chat_with_llm(model, user_input)
            except KeyboardInterrupt:
                print("\n已退出。")
                break

if __name__ == "__main__":
    main()
