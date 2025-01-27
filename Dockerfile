FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the bot directly
CMD ["python3", "main.py"]
