from agents import Agent, Runner
from agents import Agent, Runner
import os

# Load API key from keys.txt file (following project pattern)
def get_key():
    with open('keys.txt') as f:
        key = f.readline().strip().split(':')[-1]
    return key

# Set environment variable for agents library
os.environ['OPENAI_API_KEY'] = get_key()

# create a new agent
agent = Agent(name="Nhà thơ", 
              instructions="Luôn luôn trả lời câu hỏi của người dùng bằng một bài thơ lục bát")

# run the agent syncronously
question = '1 + 1 = ?'
result = Runner.run_sync(agent, question)
print(result.final_output)