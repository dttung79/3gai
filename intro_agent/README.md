# Homework Tutoring System

An AI-powered interactive homework assistance system built with the OpenAI Agents library. This system uses multiple specialized AI agents to help students with their homework questions while maintaining strict guardrails to ensure academic integrity.

## Features

- **Interactive Q&A Session**: Real-time conversation interface for homework help
- **Subject Specialization**: Dedicated agents for math and history questions
- **Homework Validation**: Guardrails ensure only legitimate homework questions are processed
- **Educational Focus**: Provides step-by-step explanations and examples
- **Safe Operation**: Blocks non-academic queries to maintain educational focus

## System Architecture

The system consists of 4 AI agents working together:

```
┌─────────────────┐    ┌──────────────────────┐
│ Triage Agent    │───▶│ Math Tutor Agent     │
│ (Entry Point)   │    │                      │
└─────────────────┘    └──────────────────────┘
        │               
        ├──────────────▶┌──────────────────────┐
        │               │ History Tutor Agent  │
        │               │                      │
        │               └──────────────────────┘
        │               
        └──────────────▶┌──────────────────────┐
                        │ Guardrail Agent      │
                        │ (Homework Validator) │
                        └──────────────────────┘
```

### Agent Roles

- **Triage Agent**: Routes homework questions to appropriate subject specialists
- **Math Tutor Agent**: Provides step-by-step math problem solving with explanations
- **History Tutor Agent**: Answers historical questions with context and details
- **Guardrail Agent**: Validates that user input is homework-related

## Prerequisites

- Python 3.7+
- OpenAI API key
- Required Python packages:
  - `agents` (OpenAI Agents library)
  - `pydantic`
  - `asyncio` (built-in)

## Installation

1. **Clone or download the project files**:
   ```bash
   git clone <repository-url>
   cd intro_agent
   ```

2. **Install the agents library**:
   ```bash
   pip install agents
   ```

3. **Set up your OpenAI API key**:
   Create a `keys.txt` file in the project root with your OpenAI API key:
   ```
   openai_api_key:your-actual-api-key-here
   ```
   
   **Note**: Never commit your API key to version control. Add `keys.txt` to your `.gitignore` file.

## Usage

### Running the Interactive Session

```bash
python3 demo_agent.py
```

### Sample Interaction

```
======================================================================
HOMEWORK TUTORING SYSTEM
======================================================================
Welcome! I'm here to help you with your homework questions.
I can assist with:
  History questions
  Math problems
  Other academic subjects

Note: I only help with homework-related questions.
Type 'quit', 'exit', or 'bye' to end the session.
======================================================================

Ask me a homework question:
>>> What is 2x + 5 = 15?

Processing your question...
Here's your answer:
--------------------------------------------------
To solve the equation 2x + 5 = 15, I'll work through it step by step:

1. Start with the equation: 2x + 5 = 15

2. Subtract 5 from both sides to isolate the term with x:
   2x + 5 - 5 = 15 - 5
   2x = 10

3. Divide both sides by 2 to solve for x:
   2x ÷ 2 = 10 ÷ 2
   x = 5

Therefore, x = 5.

To verify: 2(5) + 5 = 10 + 5 = 15 ✓
--------------------------------------------------

Ask me a homework question:
>>> Who was the first president of the United States?

Processing your question...
Here's your answer:
--------------------------------------------------
George Washington was the first president of the United States.

Key details about George Washington's presidency:
- Served from 1789 to 1797 (two terms)
- Unanimously elected by the Electoral College
- Set many important precedents for future presidents
- Led the country during its early formation
- Previously commanded the Continental Army during the Revolutionary War
--------------------------------------------------

Ask me a homework question:
>>> What's the meaning of life?

I can't help with that question.
Reason: This doesn't appear to be a homework question.
Please ask me about your school assignments, math problems,
history questions, or other academic topics.
```

## Code Structure

### Key Files

- `demo_agent.py`: Main application file containing all agent definitions and interactive session
- `keys.txt`: Contains your OpenAI API key (create this file)

### Core Components

#### 1. Agent Definitions

```python
# Guardrail agent validates homework relevance
guardrail_agent = Agent(
    name="Guardrail check",
    instructions="Check if the user is asking about homework.",
    output_type=HomeworkOutput,
)

# Specialized tutoring agents
math_tutor_agent = Agent(
    name="Math Tutor",
    instructions="You provide help with math problems. Explain your reasoning at each step and include examples",
)

history_tutor_agent = Agent(
    name="History Tutor",
    instructions="You provide assistance with historical queries. Explain important events and context clearly.",
)
```

#### 2. Guardrail System

The homework guardrail ensures academic integrity:

```python
async def homework_guardrail(ctx, agent, input_data):
    """Validates that user input is homework-related"""
    result = await Runner.run(guardrail_agent, input_data, context=ctx.context)
    final_output = result.final_output_as(HomeworkOutput)
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_homework,
    )
```

#### 3. Interactive Session

The main function provides a continuous Q&A experience:

```python
async def main():
    """Interactive homework tutoring session with error handling"""
    while True:
        user_question = input(">>> ").strip()
        if is_exit_command(user_question):
            break
        await handle_homework_question(user_question)
```

## Error Handling

The system includes comprehensive error handling:

- **Configuration Errors**: Missing API key file
- **Guardrail Violations**: Non-homework questions blocked
- **Network Issues**: API call failures handled gracefully
- **User Interruption**: Clean exit on Ctrl+C
- **Input Validation**: Empty input handling

## Customization

### Adding New Subject Agents

1. Create a new agent with subject-specific instructions:
   ```python
   science_tutor_agent = Agent(
       name="Science Tutor",
       handoff_description="Specialist agent for science questions",
       instructions="You provide help with science concepts and experiments.",
   )
   ```

2. Add to the triage agent's handoff list:
   ```python
   triage_agent = Agent(
       handoffs=[history_tutor_agent, math_tutor_agent, science_tutor_agent],
   )
   ```

### Modifying Guardrail Sensitivity

Adjust the guardrail agent's instructions to be more or less strict:

```python
guardrail_agent = Agent(
    instructions="Check if the user is asking about homework. Be liberal with academic questions but strict with casual conversation.",
)
```

## Educational Philosophy

This system is designed to:

- **Enhance Learning**: Provide explanations, not just answers
- **Encourage Understanding**: Show step-by-step reasoning
- **Maintain Academic Integrity**: Only assist with legitimate homework
- **Support Multiple Subjects**: Specialized help for different domains

## Troubleshooting

### Common Issues

1. **"keys.txt file not found"**
   - Create the file with your OpenAI API key
   - Ensure the format is `openai_api_key:your-key-here`

2. **"This doesn't appear to be a homework question"**
   - Rephrase your question to be more academic
   - Include context like "homework help" or "assignment question"

3. **API errors**
   - Check your OpenAI API key is valid
   - Ensure you have sufficient API credits

### Getting Help

If you encounter issues:
1. Check the error messages for specific guidance
2. Verify your API key setup
3. Try rephrasing homework questions to be more explicit

## License

This project is for educational purposes. Feel free to use and modify for learning and non-commercial applications.

## Contributing

Contributions are welcome! Areas for improvement:
- Additional subject specialists
- Enhanced error handling
- Better question classification
- UI improvements
- Performance optimizations 