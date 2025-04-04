from utils import get_key
from google import genai
from google.genai import types


def display_code_execution_result(response):
    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(part.text)
        if part.executable_code is not None:
            print("\nCode:")
            print(part.executable_code.code)
        if part.code_execution_result is not None:
            print("\nExecution Result:")
            print(part.code_execution_result.output)
        if part.inline_data is not None:
            print("[Image data cannot be displayed in console]")
        print("---")

def init_chat():
    client = genai.Client(api_key=get_key())
    system_prompt = "You are an AI assistant. You will use Code execution feature to answer questions that requires calculation if needed, for example counting number of characters in a word, number of words in a sentence, comparing numbers, etc. You will also use Code execution feature to answer questions that requires code execution, for example writing a simple python code to calculate the sum of two numbers, writing a simple python code to calculate the factorial of a number, etc."
    
    code_config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[types.Tool(
                code_execution=types.ToolCodeExecution
            )])
    chat = client.chats.create(model='gemini-2.0-flash', config=code_config)
    
    return chat

def main():
    chat = init_chat()
    while True:
        question = input('[User]: ')
        if question == 'exit' or question == 'quit':
            break
        response = chat.send_message(message=question)
        # Only show the text response without warnings
        if hasattr(response, 'candidates') and len(response.candidates) > 0:
            text_parts = [part.text for part in response.candidates[0].content.parts if hasattr(part, 'text') and part.text is not None]
            print('[GenAI]:', ' '.join(text_parts))
        else:
            print('[GenAI]:', response.text)
        #display_code_execution_result(response)

if __name__ == "__main__":
    main()