# Flight Scraper - Setup Complete

## Files Structure
```
flight/
├── .env                      # API keys (GROQ + LANGSMITH)
├── langgraph.json           # LangGraph Studio config
├── flight_agent.py          # Main graph with nodes & edges
├── flight_scraper_node.py   # Browser automation node
├── llm_processor_node.py    # LLM processing node  
├── flight_sites_config.py   # Site configurations
├── main.py                  # CLI interface
├── requirements.txt         # Dependencies
├── verify_setup.py          # Setup checker
├── README.md               # Main docs
└── STUDIO_GUIDE.md         # Studio setup guide
```

## LangGraph Architecture

### Graph Structure
```
START
  ↓
browser_scraper (scrapes flight data)
  ↓
llm_processor (analyzes & structures data)
  ↓
END
```

### State Flow
```python
Input:
  site, from_city, to_city, travel_date

After browser_scraper:
  + browser_result, success, site_used

After llm_processor:
  + llm_analysis, structured_flights, recommendations
```

## Running Options

### Option 1: Command Line
```cmd
python main.py
```
Full browser automation with real scraping.

### Option 2: LangGraph Studio (Visual)
```cmd
langgraph dev
```
Then open: http://localhost:8123

See your graph visually with nodes and edges!

## Recent Fixes

1. **Model Changed**: llama-3.2-11b → llama-3.3-70b-versatile (better reasoning)
2. **Temperature**: Set to 0 for consistency
3. **Task Simplified**: Clearer, shorter instructions
4. **Max Failures**: Reduced to 3 for faster feedback
5. **No Emojis**: Clean code, emojis only in browser-use logs

## What You Need

### Required:
- ✓ GROQ_API_KEY (for LLM)
- ✓ Python 3.10+
- ✓ Dependencies installed

### Optional (for Studio):
- LangSmith API key (free)
- langgraph-cli

## Next Steps

1. **Test CLI**: `python main.py`
2. **Get LangSmith Key**: https://smith.langchain.com/
3. **Add to .env**: `LANGSMITH_API_KEY=lsv2_pt_...`
4. **Run Studio**: `langgraph dev`
5. **View Graph**: http://localhost:8123

## Verify Everything
```cmd
python verify_setup.py
```

This checks all configurations!
