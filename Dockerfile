FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY core/ core/
COPY ui/ ui/
COPY data/ data/

ENV PORT=8080
EXPOSE 8080

# Cloud Run sets PORT; vertex_app reads it and binds Streamlit to 0.0.0.0.
CMD ["python", "ui/vertex_app.py"]
