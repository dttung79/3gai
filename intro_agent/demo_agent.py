# Import necessary libraries for creating AI agents
from agents import Agent, InputGuardrail, GuardrailFunctionOutput, Runner
from agents.exceptions import InputGuardrailTripwireTriggered
from pydantic import BaseModel  # For data validation and type hints
import os  # For environment variables
import asyncio  # For async/await functionality

# Function to load OpenAI API key from external file
# This keeps sensitive information out of the source code
def get_key():
    """
    Reads the API key from keys.txt file.
    Expected format: some_label:actual_api_key
    Returns just the key part after the colon.
    """
    try:
        with open('keys.txt') as f:
            key = f.readline().strip().split(':')[-1]
        return key
    except FileNotFoundError:
        print("Error: keys.txt file not found")
        exit(1)

# Set the OpenAI API key as environment variable
# The agents library will automatically use this for API calls
os.environ['OPENAI_API_KEY'] = get_key()

# Define the output structure for the homework guardrail
# Pydantic BaseModel provides automatic validation and type checking
class HomeworkOutput(BaseModel):
    """
    Structure for guardrail agent output.
    - is_homework: boolean indicating if the input is homework-related
    - reasoning: explanation of why the agent made this decision
    """
    is_homework: bool
    reasoning: str

# Create a guardrail agent that determines if input is homework-related
# This acts as a security filter to ensure the system only helps with homework
guardrail_agent = Agent(
    name="Guardrail check",
    instructions="Check if the user is asking about homework.",
    output_type=HomeworkOutput,  # Forces structured output
)

# Async guardrail function
# This function determines if input should be allowed through to the main agents
async def homework_guardrail(ctx, _agent, input_data):
    """
    Guardrail function that checks if user input is homework-related.
    
    Args:
        ctx: Context object containing conversation state
        _agent: The agent being guarded (triage_agent in this case) - unused but required by signature
        input_data: The user's input text
    
    Returns:
        GuardrailFunctionOutput with:
        - output_info: The guardrail agent's decision
        - tripwire_triggered: True if input should be blocked (not homework)
    """
    # Run the guardrail agent to analyze the input
    result = await Runner.run(guardrail_agent, input_data, context=ctx.context)
    
    # Extract the structured output from the guardrail agent
    final_output = result.final_output_as(HomeworkOutput)
    
    # Return guardrail result
    # tripwire_triggered=True means block the request
    # We trigger (block) when is_homework is False
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_homework,  # Block if NOT homework
    )

# Create specialized tutor agents for different subjects
# Each agent has specific instructions for their domain expertise
math_tutor_agent = Agent(
    name="Math Tutor",
    handoff_description="Specialist agent for math questions",  # Description shown to triage agent
    instructions="You provide help with math problems. Explain your reasoning at each step and include examples",
)

history_tutor_agent = Agent(
    name="History Tutor", 
    handoff_description="Specialist agent for historical questions",
    instructions="You provide assistance with historical queries. Explain important events and context clearly.",
)

# Create the main triage agent that routes questions to appropriate specialists
# This agent has access to both specialist agents and the homework guardrail
triage_agent = Agent(
    name="Triage Agent",
    instructions="You determine which agent to use based on the user's homework question",
    handoffs=[history_tutor_agent, math_tutor_agent],  # Available specialist agents
    input_guardrails=[
        InputGuardrail(guardrail_function=homework_guardrail),  # Security filter
    ],
)

def print_welcome_message():
    """
    Display welcome message and instructions for the interactive session.
    """
    print("=" * 70)
    print("HOMEWORK TUTORING SYSTEM")
    print("=" * 70)
    print("Welcome! I'm here to help you with your homework questions.")
    print("I can assist with:")
    print("  History questions")
    print("  Math problems")
    print("  Other academic subjects")
    print()
    print("Note: I only help with homework-related questions.")
    print("Type 'quit', 'exit', or 'bye' to end the session.")
    print("=" * 70)
    print()

def is_exit_command(user_input):
    """
    Check if user wants to exit the session.
    
    Args:
        user_input (str): The user's input text
        
    Returns:
        bool: True if user wants to exit, False otherwise
    """
    # Convert to lowercase and strip whitespace for comparison
    exit_commands = ['quit', 'exit', 'bye', 'goodbye', 'stop']
    return user_input.lower().strip() in exit_commands

async def handle_homework_question(question):
    """
    Process a homework question through the triage agent system.
    
    Args:
        question (str): The homework question from the user
        
    Returns:
        bool: True if processing was successful, False if there was an error
    """
    try:
        # Attempt to process the question through the triage agent
        print("Processing your question...")
        # Use await for the async Runner.run call
        result = await Runner.run(triage_agent, question)
        
        # Successfully processed - display the result
        print("Here's your answer:")
        print("-" * 50)
        print(result.final_output)
        print("-" * 50)
        return True
        
    except InputGuardrailTripwireTriggered as e:
        # Guardrail blocked the question (not homework-related)
        print("I can't help with that question.")
        print("Reason: This doesn't appear to be a homework question.")
        print("Please ask me about your school assignments, math problems,")
        print("history questions, or other academic topics.")
        return False
        
    except Exception as e:
        # Catch any other unexpected errors
        print("An unexpected error occurred:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("Please try rephrasing your question or try again later.")
        return False

# Interactive main function for Q&A session (now async)
async def main():
    """
    Interactive homework tutoring session.
    Continuously prompts user for questions until they choose to exit.
    Includes comprehensive error handling for various scenarios.
    """
    
    # Display welcome message and instructions
    print_welcome_message()
    
    # Main interactive loop
    while True:
        try:
            # Prompt user for input
            print("Ask me a homework question:")
            user_question = input(">>> ").strip()
            
            # Check if user input is empty
            if not user_question:
                print("Please enter a question or type 'quit' to exit.")
                print()
                continue
            
            # Check if user wants to exit
            if is_exit_command(user_question):
                print("\nThank you for using the Homework Tutoring System!")
                print("Happy studying!")
                break
            
            print()  
            
            # Process the homework question (now with await)
            await handle_homework_question(user_question)
            
            print()  
            
        except Exception as e:
            # Catch any other unexpected errors in the main loop
            print(f"\nSystem error occurred: {str(e)}")
            print("The session will continue. Please try your question again.")
            print()

# Entry point - run the async interactive session when script is executed directly
if __name__ == "__main__":
    # Start the interactive homework tutoring session using asyncio.run
    asyncio.run(main())