# Anony API

A FastAPI-based service for anonymizing and deanonymizing text using reversible PII replacement.

## Features

- **Anonymize**: Replace PII in text with fake data.
- **Deanonymize**: Restore original text using a token.
- **Token-based mapping**: Secure, temporary mapping for deanonymization.
- **SQLite storage**: Mappings stored with automatic expiration and cleanup.

## API Documentation

Interactive API docs are available at [`/docs`](http://localhost:8001/docs).

## Quickstart

### Requirements

- Python 3.11+
- See `requirements.txt` for dependencies.

### Local Run

```bash
pip install -r requirements.txt
python main.py
```

API will be available at `http://localhost:8001` by default.

### Docker

```bash
TO DO
```

## Notes

- Mappings expire after 30 day by default.
- For development only; do not use for production PII without review.
