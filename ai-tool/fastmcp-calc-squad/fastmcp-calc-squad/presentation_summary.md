# 🎯 FastMCP + AWS Agent Squad Calculator - Presentation Summary

## 📊 Project Overview
- **Dynamic AI-powered calculator** using natural language processing
- **Two-level intelligent orchestration** system
- **Seamless integration** between MCP protocol and AWS Bedrock agents
- **Extensible architecture** for adding new capabilities

---

## 🏗️ Core Architecture Components

### 1. MCP (Model Context Protocol) Server
- Hosts **11 calculator tools** (add, subtract, multiply, divide, sqrt, gcd, lcm, factorial, mean, median, power)
- **FastMCP framework** for easy tool creation and discovery
- Tools are **automatically discoverable** via MCP protocol
- **Language-agnostic** - can be called by any MCP client

### 2. MCP Bridge (Tool Connector)
- **MCPBridge class** acts as client to MCP server
- **Dynamic tool discovery** - lists available tools at runtime
- **Tool execution** with parameter passing and result handling
- **Type conversion** for AWS Bedrock compatibility

### 3. Tool Registry (Format Converter)
- **Critical translation layer** between MCP and AWS formats
- Converts MCP tool schemas to AWS Bedrock tool specifications
- **Key conversion**: `input_schema` → `toolSpec.inputSchema.json`
- Enables AWS agents to understand and use MCP tools

### 4. AWS Agent Squad (Orchestration Framework)
- **AgentSquad** manages multiple specialized agents
- **BedrockLLMAgent** with Claude 3.5 Sonnet as the "brain"
- **Intelligent routing** to appropriate agents
- **Built-in features**: logging, retries, fallback handling

---

## 🧠 Two-Level Intelligent Orchestration

### Level 1: Agent Selection (Agent Squad)
```
User Input → AgentSquad Orchestrator → Agent Classification → Route to Calc Agent
```
- **Natural language understanding** of user intent
- **Dynamic routing** to specialized agents (currently: Calc Agent)
- **Scalable**: Easy to add Weather Agent, Time Agent, etc.

### Level 2: Tool Selection (Within Agent)
```
Calc Agent → Bedrock LLM Analysis → Tool Selection → Parameter Extraction
```
- **Claude analyzes** math question and selects appropriate tool
- **Automatic parameter extraction** from natural language
- **Example**: "square root of 144" → selects `sqrt` tool with `{x: 144}`

---

## 🔄 Complete Request Flow

### Step-by-Step Process:
1. **User Input**: "What is square root of 144?"
2. **Agent Classification**: AgentSquad identifies as math question → routes to Calc Agent
3. **Tool Selection**: Calc Agent analyzes → selects `sqrt` tool
4. **Parameter Extraction**: Extracts `x = 144`
5. **MCP Bridge Call**: Calls MCP server with `sqrt(144)`
6. **Tool Execution**: MCP server calculates `144 ** 0.5 = 12.0`
7. **Response Generation**: Claude generates user-friendly response
8. **Output**: "The square root of 144 is 12"

---

## 🔧 Key Technical Integrations

### MCP Protocol Integration
- **Tool Discovery**: Dynamic listing of available calculator functions
- **Schema Translation**: MCP format → AWS Bedrock format
- **Execution Bridge**: AWS tool calls → MCP server calls
- **Result Handling**: Type conversion and error management

### AWS Bedrock Integration
- **boto3 client** for AWS API communication
- **Claude 3.5 Sonnet** for natural language understanding
- **Function calling** capability for tool selection
- **Authentication** via environment variables

### Agent Squad Framework
- **Multi-agent management** with intelligent routing
- **Tool configuration** with recursion limits
- **Custom system prompts** for agent behavior
- **Comprehensive logging** and performance tracking

---

## 💡 Key Advantages

### 🎯 Dynamic vs Hardcoded
- **100% Dynamic**: No hardcoded rules for tool selection
- **AI-powered decisions**: LLM analyzes and chooses appropriate tools
- **Natural language interface**: Users don't need to know specific tool names

### 🔧 Extensibility
- **Easy tool addition**: Add new functions to MCP server
- **Agent scalability**: Add Weather Agent, Time Agent, etc.
- **LLM flexibility**: Can switch from AWS Bedrock to Groq, OpenAI, etc.

### 🏗️ Modular Architecture
- **Separation of concerns**: MCP tools, agent logic, orchestration
- **Protocol independence**: MCP tools work with any LLM provider
- **Format abstraction**: Tool registry handles protocol differences

---

## 🛠️ Technical Requirements

### Dependencies
- **FastMCP**: Tool server framework
- **boto3**: AWS SDK for Python
- **agent-squad**: Multi-agent orchestration
- **python-dotenv**: Environment configuration

### AWS Setup
- **Bedrock access** with Claude 3.5 Sonnet model
- **Proper IAM permissions** for Bedrock runtime
- **Environment variables**: AWS credentials and region

### Environment Configuration
- **AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY**: Authentication
- **AWS_REGION**: Service region (us-east-1)
- **BEDROCK_MODEL_ID**: Claude model specification

---

## 🚀 Scalability & Future Extensions

### Adding New Agents (Example)
```python
# Weather Agent with separate MCP server
weather_agent = BedrockLLMAgent(BedrockLLMAgentOptions(
    name="Weather Expert",
    tools=weather_mcp_tools,  # get_weather, get_forecast
))

# Time Agent with time-related tools  
time_agent = BedrockLLMAgent(BedrockLLMAgentOptions(
    name="Time Keeper", 
    tools=time_mcp_tools,     # get_time, get_date
))
```

### LLM Provider Flexibility
- **Current**: AWS Bedrock (Claude)
- **Alternatives**: Groq, OpenAI, Anthropic Direct, Local LLMs
- **Same MCP integration** works with any provider

---

## 📊 Business Value

### User Experience
- **Natural language interface**: "What's 5 plus 3?" instead of `add(5,3)`
- **Intelligent tool selection**: Users don't need to know specific functions
- **Conversational interaction**: AI explains reasoning and results

### Developer Benefits
- **Rapid tool development**: Add new capabilities via MCP protocol
- **Multi-agent architecture**: Specialized agents for different domains
- **Cloud-native**: Leverages AWS managed AI services

### Enterprise Ready
- **Comprehensive logging**: Full audit trail of agent decisions
- **Error handling**: Retry mechanisms and fallback strategies
- **Scalable architecture**: Add unlimited agents and tools

---

## 🎯 Key Takeaway
**This project demonstrates a sophisticated AI orchestration system that combines multiple cutting-edge technologies (MCP, AWS Bedrock, Agent Squad) to create an intelligent, extensible, and user-friendly calculator that understands natural language and automatically selects appropriate tools.**

---

## 📋 Format Conversion Differences

### MCP Format vs AWS Agent Squad Format

#### MCP Format:
```json
{
    "name": "sqrt",
    "description": "Calculate square root", 
    "input_schema": {
        "type": "object",
        "properties": {
            "x": {"type": "number"}
        }
    }
}
```

#### AWS Agent Squad Format:
```json
{
    "toolSpec": {
        "name": "sqrt",
        "description": "Calculate square root",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "x": {"type": "number"}
                }
            }
        }
    }
}
```

#### Key Differences:
- **Structure**: MCP uses flat structure, AWS uses nested `toolSpec` wrapper
- **Schema Wrapping**: MCP has direct `input_schema`, AWS wraps in `inputSchema.json`
- **Naming Convention**: MCP uses snake_case, AWS uses camelCase
- **Protocol Requirements**: Different standards for tool specification

---

## 🔗 Project File Structure
```
fastmcp-calc-squad/
├── app/
│   ├── run.py              # Main application entry point
│   ├── squad.py            # Orchestration and agent setup
│   ├── mcp_client.py       # MCP Bridge (tool connector)
│   ├── tool_registry.py    # Format converter (MCP → AWS)
│   └── prompts/
│       └── calc_system_prompt.txt  # Agent behavior instructions
├── mcp_server/
│   └── server.py           # FastMCP calculator tools server
├── requirements.txt        # Python dependencies
└── .env                    # Environment configuration
```

---

## 🚦 Setup Commands Summary
```bash
# Navigate to project directory
cd /d "c:\Users\Gaurav\Downloads\fastmcp-calc-squad\fastmcp-calc-squad"

# Activate virtual environment
venv\Scripts\activate

# Run the application
python -m app.run
```

---

## 🌟 Demo Examples

### User Interactions:
- **Input**: "What is square root of 144?"
- **Output**: "The square root of 144 is 12"

- **Input**: "Add 5 and 3"
- **Output**: "5 + 3 = 8"

- **Input**: "Find GCD of 84 and 30"
- **Output**: "The greatest common divisor of 84 and 30 is 6"

- **Input**: "Calculate factorial of 5"
- **Output**: "The factorial of 5 is 120"
