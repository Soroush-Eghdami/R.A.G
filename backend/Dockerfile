FROM python:3.13-slim

WORKDIR /app

# Install build deps for chromadb / pymupdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libglib2.0-0 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY rag/ ./rag/
COPY backend/manage.py ./
COPY run.py ./
COPY .env ./

# Create data dir for Chroma + uploads
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--noreload"]
