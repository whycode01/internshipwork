# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install required system packages for pip and dependencies
RUN apt-get update && apt-get install -y gcc libffi-dev

# Copy dependency definitions first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy entire project into container
COPY . .

# Ensure required folders exist
RUN mkdir -p chat_sessions uploaded_images

# Expose ports: FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501

# Run backend and frontend
CMD ["bash", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0"]
