import os
import sys
import google.generativeai as genai
from typing import Optional

# 定義系統指令：設定 AI 的性格與行為準則
SYSTEM_INSTRUCTION = """
你是一位專業、資深且幽默的台灣軟體工程師。
你的行為準則如下：
1. 使用繁體中文回應。
2. 語氣專業但輕鬆，偶爾可以使用台灣工程師常用的術語（如：噴掉、修好、部署、環境變數等）。
3. 回應要精簡、直接，不廢話。
4. 如果使用者問的是程式碼相關問題，請優先提供高品質、符合最佳實踐的解決方案。
5. 保持謙虛但展現專業。
"""

def setup_gemini():
    """初始化 Gemini API 配置並設定 System Instruction"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("錯誤：請先設置環境變數 GOOGLE_API_KEY")
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    
    # 在建立模型時傳入 system_instruction
    return genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=SYSTEM_INSTRUCTION
    )

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
    """進入點"""
    model = setup_gemini()
    
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        chat_with_llm(model, user_input)
    else:
        print("--- Gemini 專業工程師模式 (輸入 'quit' 退出) ---")
        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ['quit', 'exit']:
                    break
                if not user_input.strip():
                    continue
                chat_with_llm(model, user_input)
            except KeyboardInterrupt:
                print("\n已退出。")
                break

if __name__ == "__main__":
    main()
