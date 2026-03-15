FROM python:3.11-slim

WORKDIR /app

COPY server /app/server

RUN pip install --no-cache-dir /app/server

EXPOSE 8100

CMD ["python", "-m", "uvicorn", "lens_server.main:app", "--host", "0.0.0.0", "--port", "8100"]
