FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Change to Shell Form so it expands Render's custom port variable at runtime
CMD uvicorn api:app --host 0.0.0.0 --port $PORT