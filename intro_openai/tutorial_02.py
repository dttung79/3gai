# The Assistants API allows you to build AI assistants within your own applications. An Assistant has instructions and can leverage models, tools, and files to respond to user queries.

# The Assistants API currently supports three types of tools: Code Interpreter, File Search, and Function calling.

from openai import OpenAI
from utils import get_key, print_message_content

client = OpenAI(api_key=get_key())

# create an assistant
assistant = client.beta.assistants.create(
    name='Progammer Expert',
    instructions='You are a helpful assistant that helps users with programming questions.',
    model='gpt-4.1')
# create a thread
thread = client.beta.threads.create()

# create messages in the thread
while True:
    try:
        question = input('[User]: ')
        if question == 'exit' or question == 'quit':
            break
        # create a message in the thread
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role='user',
            content=question)
        # create a run to answer the question
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id)
        # a run takes a few seconds to complete
        if run.status == 'completed':
            # get message from the run
            messages = client.beta.threads.messages.list(
                thread_id=thread.id,
                run_id=run.id)
            for message in messages.data:
                if message.role == 'assistant':
                    print_message_content(message.content)
        else:
            print('[AI]:', run.status)

    except Exception as e:
        print(e)
        break