FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_lg

COPY . .

EXPOSE 8001

CMD ["python", "main.py"]