FROM python:3.10-slim

WORKDIR /app/
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --requirement requirements.txt

COPY . .

CMD gunicorn app:app & python3 main.py
