FROM python:3.11-slim

# System dependencies: ffmpeg for video, libgl for PIL
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# HF Spaces writes to /data (persistent volume)
ENV VAH_DATA_DIR=/data
ENV PYTHONUNBUFFERED=1
# Suppress ChromaDB telemetry
ENV ANONYMIZED_TELEMETRY=false

# HF Spaces runs on port 7860
EXPOSE 7860

CMD ["uvicorn", "web.server:app", "--host", "0.0.0.0", "--port", "7860"]
