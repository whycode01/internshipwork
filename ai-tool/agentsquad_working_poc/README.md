# AgentSquad Working POC

A demonstration of the AgentSquad framework showcasing multi-agent orchestration with specialized agents for weather, time, and news services.

## Project Overview

This project demonstrates how to build and orchestrate multiple AI agents using the AgentSquad framework. It includes:

- **WeatherAgent**: Provides weather information for any city
- **TimeAgent**: Returns current time for various cities worldwide
- **NewsAgent**: Fetches top news headlines
- **MetaAgent**: Orchestrates and routes requests to appropriate agents using LLM-based entity extraction

## Prerequisites

- Python 3.8 or higher
- pip package manager
- API keys for external services (see Environment Setup)

## Environment Setup

### 1. Clone or Download the Repository

```bash
# If using git
git clone <repository-url>
cd agentsquad_working_poc

# Or download and extract the files to your local directory
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv myenv

# Activate virtual environment
# On Windows:
myenv\Scripts\activate

# On macOS/Linux:
source myenv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` file in the project root directory with the following API keys:

```env
# Required API Keys
GROQ_API_KEY=your_groq_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here
NEWS_API_KEY=your_newsapi_key_here
```

#### How to Get API Keys:

1. **GROQ API Key**:
   - Visit [Groq Console](https://console.groq.com/)
   - Sign up/login and create an API key
   - Free tier available

2. **OpenWeather API Key**:
   - Visit [OpenWeatherMap](https://openweathermap.org/api)
   - Sign up for a free account
   - Generate an API key (free tier: 1000 calls/day)

3. **News API Key**:
   - Visit [NewsAPI](https://newsapi.org/)
   - Register for a free account
   - Get your API key (free tier: 100 requests/day)

## Project Structure

### Core Files Used in the Application:

```
agentsquad_working_poc/
├── main.py                    # Main application entry point
├── custom_agents.py           # Weather, Time, and News agents
├── meta_agent.py             # Meta agent for orchestration
├── entity_extractor.py       # LLM-based entity extraction
├── simple_classifier.py      # Agent classification logic
├── orchestrator_config.py    # AgentSquad configuration
├── timezones.json            # Timezone mappings for cities
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
└── README.md                 # This file
```

### Test and Example Files:

```
├── test_project.py           # Unit tests for agents
├── questions.txt             # Sample queries for testing
```

### Unused Files:

```
├── llama_agent.py           # Alternative LLM agent implementation (not used)
├── myenv/                   # Virtual environment directory
├── __pycache__/            # Python cache files
```

## How to Run the Application

### 1. Ensure Virtual Environment is Active

```bash
# Windows
myenv\Scripts\activate

# macOS/Linux
source myenv/bin/activate
```

### 2. Run the Application

```bash
python main.py
```

### 3. Interact with the System

The application will start an interactive loop where you can ask questions like:

- `"What's the weather in Paris, the time in Tokyo, and the latest news?"`
- `"Give me the current temperature in New York"`
- `"What time is it in London?"`
- `"Show me the latest news"`
- `"Tell me the weather in Berlin and time in Dubai"`

Type `exit` or `quit` to terminate the application.

## Sample Interactions

```
🧠 Type your question below (type 'exit' to quit):

💬 You: What's the weather in Paris, the time in Tokyo, and the latest news?

🤖 Assistant:
 🌤 WeatherAgent:
The current temperature in Paris is 18°C with clear sky.

⏰ TimeAgent:
The current time in Tokyo is 15:30:25.

📰 Top News Headlines:
1. Breaking: Major tech announcement today (BBC News)
2. Global climate summit begins (The Verge)
3. Economic markets show growth (BBC News)
```

## Running Tests

To run the test suite:

```bash
# Install pytest if not already installed
pip install pytest

# Run tests
pytest test_project.py -v
```

## File Details

### Used Files:

1. **main.py**: Entry point that sets up the agent squad and interactive loop
2. **custom_agents.py**: Contains WeatherAgent, TimeAgent, and NewsAgent implementations
3. **meta_agent.py**: MetaAgent that orchestrates requests to specialized agents
4. **entity_extractor.py**: Uses Groq LLM to extract entities from user queries
5. **simple_classifier.py**: Classifier that routes all requests to MetaAgent
6. **orchestrator_config.py**: Configuration for AgentSquad behavior
7. **timezones.json**: Maps city names to timezone identifiers
8. **requirements.txt**: Lists all Python dependencies
9. **.env**: Environment variables (you need to create this)

### Test/Example Files:

1. **test_project.py**: Unit tests for all agents
2. **questions.txt**: Example queries for manual testing

### Unused Files:

1. **llama_agent.py**: Alternative LLM agent implementation (not imported or used)
2. **myenv/**: Virtual environment directory (development artifact)
3. **__pycache__/**: Python bytecode cache (automatically generated)

## Architecture Overview

```
User Input → AgentSquad → MetaClassifier → MetaAgent → Entity Extractor (Groq LLM)
                                              ↓
                                         Route to appropriate agents:
                                         - WeatherAgent (OpenWeather API)
                                         - TimeAgent (pytz library)
                                         - NewsAgent (NewsAPI)
```

## Troubleshooting

### Common Issues:

1. **API Key Errors**: Ensure all API keys are correctly set in `.env` file
2. **Module Import Errors**: Make sure virtual environment is activated and dependencies are installed
3. **Network Errors**: Check internet connection for API calls
4. **Timezone Errors**: City names must match entries in `timezones.json`

### Debug Mode:

The application prints LLM responses for debugging. You'll see:
```
🧠 LLM Raw Output:
{"weather_location": "Paris", "time_location": "Tokyo", "news_requested": true}
```

## License

This is a demonstration project for the AgentSquad framework.

## Support

For issues with:
- AgentSquad framework: Check the official AgentSquad documentation
- API services: Consult respective API provider documentation
- This demo: Review the code comments and test files for examples
