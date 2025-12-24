# Base Image: Lightweight Python 3.11
FROM python:3.11-slim

# Set Working Directory
WORKDIR /app

# Install System Dependencies (Required for some Python packages)
# build-essential for compiling, curl for healthchecks
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Requirements
COPY requirements.txt .

# Install Python Dependencies (No Cache to keep image small)
RUN pip install --no-cache-dir -r requirements.txt

# Copy Application Code
COPY . .

# Expose Streamlit Port
EXPOSE 8501

# Healthcheck to ensure container is responsive
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Entry Point
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
