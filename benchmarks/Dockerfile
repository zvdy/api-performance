FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY benchmarks/requirements.txt requirements.txt
COPY api/requirements.txt api-requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r api-requirements.txt

# Create directory for API code
RUN mkdir -p /usr/local/lib/python3.10/site-packages/api

# Copy benchmark code
COPY benchmarks/ .

# Set environment variables
ENV API_BASE_URL=http://api:8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/usr/local/lib/python3.10/site-packages

# Default command (can be overridden)
CMD ["python", "run.py"] 