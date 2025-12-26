# Strands Agents + Ollama (local llama3.2:3b)

## Setup
```bash
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
ollama pull llama3.2:3b
ollama serve
```

## Run
```bash
python -u app/agent.py
python -u app/run_stream.py
```

## Notes
Tools may or may not be invoked depending on model ability. Change `model_id` to switch models.
