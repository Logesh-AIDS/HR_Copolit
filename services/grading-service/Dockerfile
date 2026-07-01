# services/grading-service/Dockerfile
FROM python:3.11-slim

WORKDIR /workspace

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY services/grading-service/requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r /workspace/requirements.txt
RUN pip install --no-cache-dir email-validator pydantic-settings redis SQLAlchemy psycopg2-binary

COPY services/common /workspace/services/common
COPY services/grading-service /workspace/services/grading-service

ENV PYTHONPATH=/workspace:/workspace/services/grading-service

EXPOSE 8002

CMD ["python", "services/grading-service/app/main.py"]
