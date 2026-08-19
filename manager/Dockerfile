FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py db.py security.py recovery.py ./
COPY templates ./templates
COPY static ./static
EXPOSE 8087
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8087", "--no-proxy-headers"]
