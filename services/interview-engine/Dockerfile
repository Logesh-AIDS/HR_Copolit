# services/interview-engine/Dockerfile
FROM python:3.11-slim

WORKDIR /workspace

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY services/interview-engine/requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r /workspace/requirements.txt
RUN pip install --no-cache-dir email-validator pydantic-settings redis SQLAlchemy psycopg2-binary bcrypt python-jose passlib

COPY services/common /workspace/services/common
COPY services/interview-engine /workspace/services/interview-engine

ENV PYTHONPATH=/workspace:/workspace/services/interview-engine

EXPOSE 8003

CMD ["python", "services/interview-engine/app/main.py"]
