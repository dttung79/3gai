from utils import get_key
from google import genai

# Simulate system prompt using chat

client = genai.Client(api_key=get_key())
chat = client.chats.create(model='gemini-2.0-flash')
chat.send_message(message="You are a cat. You will answer questions as a cat. Convert words to meow, meoow, meooww, etc. based on the length of the word. ONLY MEOWS ALLOWED. No matter what the question is, you must respond with meows only.")
while True:
    question = input('[User]: ')
    if question == 'exit' or question == 'quit':
        break
    response = chat.send_message(message=question)
    print('[GenAI]:', response.text)