# LangGraph Studio Quick Start

## Setup Steps

### 1. Get LangSmith API Key (Required for Studio)
1. Go to: https://smith.langchain.com/
2. Sign up or log in
3. Go to Settings > API Keys
4. Click "Create API Key"
5. Copy the key

### 2. Add to .env
```env
LANGSMITH_API_KEY=lsv2_pt_your_key_here
```

### 3. Install LangGraph CLI
```cmd
pip install langgraph-cli
```

### 4. Run Studio
```cmd
langgraph dev
```

### 5. Open Browser
http://localhost:8123

## Test Input

```json
{
  "site": "makemytrip",
  "from_city": "Pune",
  "to_city": "Delhi",
  "travel_date": "16/10/2025"
}
```

## Visualize Graph

In Studio, you'll see:
- Node: browser_scraper
- Node: llm_processor
- Flow: START → browser_scraper → llm_processor → END

## Notes

- LangSmith API key is FREE
- Studio runs on localhost:8123
- Your graph is defined in `flight_agent.py:create_graph`
