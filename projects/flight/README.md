# Flight Scraper Agent - LangGraph Studio

A LangGraph-based flight scraper using browser automation and LLM processing.

## Setup

### 1. Install Dependencies
```cmd
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here
```

Get API keys:
- **Groq API Key**: https://console.groq.com/keys
- **LangSmith API Key**: https://smith.langchain.com/ (Settings > API Keys)

### 3. Install LangGraph CLI
```cmd
pip install langgraph-cli
```

## Run with LangGraph Studio

### Start Studio Server
```cmd
langgraph dev
```

Open: **http://localhost:8123**

### Test Input
```json
{
  "site": "makemytrip",
  "from_city": "Pune",
  "to_city": "Delhi",
  "travel_date": "16/10/2025"
}
```

## Run from Command Line
```cmd
python main.py
```

## Graph Structure

```
START → browser_scraper → llm_processor → END
```

### Nodes:
1. **browser_scraper** - Scrapes flight data from websites
2. **llm_processor** - Analyzes and structures data using LLM

### Supported Sites:
- makemytrip
- booking
- skyscanner

## Files
- `flight_agent.py` - LangGraph workflow
- `flight_scraper_node.py` - Browser automation node
- `llm_processor_node.py` - LLM processing node
- `flight_sites_config.py` - Site configurations
- `main.py` - CLI interface
- `langgraph.json` - LangGraph Studio config
- `verify_setup.py` - Setup verification script

## Verify Setup
```cmd
python verify_setup.py
```
