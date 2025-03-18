FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy benchmark code
COPY . .

# Set environment variables
ENV API_BASE_URL=http://api:8000
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
CMD ["python", "run.py"] 