FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--app-dir", ".", "--host", "0.0.0.0", "--port", "8000"]
