# Dockerfile für Advanced AI Trading Bot
# pandas-ta 0.3.14b0 supports Python < 3.11, so we pin to 3.10 here.
FROM python:3.13

# Metadata
LABEL maintainer="Trading Bot Team"
LABEL version="2.0"
LABEL description="Advanced AI Trading Bot with Multi-Source Learning"

# System Dependencies installieren
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis
WORKDIR /app

# Python Dependencies zuerst kopieren (für Docker Cache)
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# TextBlob und NLTK Daten herunterladen (für Sentiment-Analyse)
RUN python -m textblob.download_corpora && \
    python -c "import nltk; nltk.download('punkt'); nltk.download('brown'); nltk.download('wordnet')"

# Projekt-Code kopieren
COPY . .

# Verzeichnisse erstellen
RUN mkdir -p /app/logs /app/models /app/models/versions \
    /app/training_data /app/news_data /app/portfolio

# Volumes für persistente Daten
VOLUME ["/app/logs", "/app/models", "/app/training_data", "/app/news_data", "/app/portfolio"]

# Port für Monitoring/API (falls Web-Interface hinzugefügt wird)
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/app/logs/trading_bot.log') else 1)"

# Standardkommando
CMD ["python", "main.py"]
