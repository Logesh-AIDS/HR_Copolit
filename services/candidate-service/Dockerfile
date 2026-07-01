# services/candidate-service/Dockerfile
FROM python:3.11-slim

WORKDIR /workspace

# Install postgres client and build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy python dependencies list
COPY services/candidate-service/requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r /workspace/requirements.txt
RUN pip install --no-cache-dir email-validator pydantic-settings redis bcrypt python-jose passlib docx2txt pytesseract

# Copy source directories
COPY services/common /workspace/services/common
COPY services/candidate-service /workspace/services/candidate-service

# Configure Python path
ENV PYTHONPATH=/workspace:/workspace/services/candidate-service

EXPOSE 8000

# Run main module
CMD ["python", "services/candidate-service/app/main.py"]
