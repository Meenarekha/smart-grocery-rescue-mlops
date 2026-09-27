FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY requirements.txt .

# Install CPU-only PyTorch first.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.8.0+cpu \
    torchvision==0.23.0+cpu

# Install application dependencies.
RUN pip install --no-cache-dir \
    pandas \
    numpy \
    scikit-learn \
    joblib \
    streamlit \
    python-dotenv \
    mlflow \
    dagshub \
    pytest \
    easyocr \
    Pillow

COPY src ./src
COPY data ./data
COPY models ./models
COPY results ./results
COPY pytest.ini .

EXPOSE 8501

CMD ["streamlit", "run", "src/app/app.py", "--server.address=0.0.0.0", "--server.port=8501"]