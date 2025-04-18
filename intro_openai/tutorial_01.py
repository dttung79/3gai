from openai import OpenAI
from utils import get_key

# This is a simple example of how to use the OpenAI API to chat with a model.
# It uses the OpenAI Python client library to send a message to the model and receive a response.
# In this example, model cannot remember the previous conversation.

client = OpenAI(api_key=get_key())

while True:
    try:
        question = input('[User]: ')
        if question == 'exit' or question == 'quit':
            break
        # generate a response
        response = client.chat.completions.create(
            model='gpt-4.1',
            messages=[{'role': 'user', 'content': question}]
        )
        print('[AI]:', response.choices[0].message.content)
    except Exception as e:
        print(e)
        break