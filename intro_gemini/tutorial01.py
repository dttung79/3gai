from utils import get_key
# Simple example of using the GenAI client
# AI has no memory, so it will not remember the context of the conversation
from google import genai
# create a client
client = genai.Client(api_key=get_key())
while True:
    question = input('[User]: ')
    if question == 'exit' or 'quit':
        break
    # generate a response
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=[question]
    )
    print('[GenAI]:', response.text)