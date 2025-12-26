import logging

from strands import Agent
from strands.models.ollama import OllamaModel
from strands_tools import current_time

from app.schemas import BookAnalysis
from app.tools import letter_counter, simple_calculator

# Optional debug logs
logging.getLogger("strands").setLevel(logging.INFO)
logging.basicConfig(format="%(levelname)s | %(name)s | %(message)s")

# Configure the local Ollama model
# Ensure `ollama serve` is running and model is pulled: `ollama pull llama3.2:3b`
ollama_model = OllamaModel(
    host="http://localhost:11434",
    model_id="llama3.2:3b",
    temperature=0.3,
    keep_alive="10m",
)

# Assemble the agent with tools (Windows-safe: no python_repl)
agent = Agent(
    model=ollama_model,
    tools=[simple_calculator, current_time, letter_counter],
)

def demo_basic():
    # First, let's test our letter_counter tool directly
    print("\n--- Direct Tool Test ---")
    direct_result = letter_counter("strawberry", "r")
    print(f"Direct letter_counter('strawberry', 'r') = {direct_result}")
    
    # Test the simple calculator directly
    calc_result = simple_calculator("3111696 / 74088")
    print(f"Direct simple_calculator('3111696 / 74088') = {calc_result}")
    
    prompt = (
        "Please help me with these 3 tasks:\n"
        "1) Tell me what time it is in paris\n"
        "2) Calculate the result of 3111696 divided by 74088\n"
        "3) Count exactly how many times the letter 'r' appears in the word 'strawberry'\n\n"
        "Use the available tools for each task and provide clear results."
    )
    result = agent(prompt)
    
    # Print detailed tool results
    print("\n--- Tool Execution Details ---")
    summary = result.metrics.get_summary()
    for trace in summary.get('traces', []):
        for child in trace.get('children', []):
            if child.get('name', '').startswith('Tool:'):
                tool_name = child['name']
                message = child.get('message', {})
                if message and 'content' in message:
                    tool_result = message['content'][0]
                    if tool_result.get('toolResult', {}).get('status') == 'success':
                        content = tool_result['toolResult']['content'][0]['text']
                        print(f"{tool_name}: SUCCESS - {content}")
                    else:
                        error_content = tool_result.get('toolResult', {}).get('content', [{}])[0].get('text', 'Unknown error')
                        print(f"{tool_name}: ERROR - {error_content}")
    
    # Print model output (stdout side-effect) and a short metrics summary
    print("\n--- Metrics summary ---")
    print(summary)

def demo_structured_output():
    text = (
        'Analyze this book: "The Hitchhiker\'s Guide to the Galaxy" by Douglas Adams. '
        "It is a humorous sci-fi classic. Provide a rating."
    )
    result = agent.structured_output(BookAnalysis, text)

    print("\n--- Structured Output (JSON) ---")
    # ✅ Pretty-print JSON instead of raw object
    print(result.model_dump_json(indent=4))

if __name__ == "__main__":
    demo_basic()
    demo_structured_output()
