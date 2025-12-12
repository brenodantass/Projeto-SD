FROM python:3.11-slim

WORKDIR /app

# Dependências do sistema (opcional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/

# Porta será definida por processo via args/ports de execução
ENV NUM_PROCESSES=3
ENV INITIAL_CLOCK=5
ENV PEERS=""
ENV PROCESS_ID=0
ENV DELAY_MESSAGE_ID=""
ENV DELAY_MS=0

# Executa FastAPI com log mais limpo
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "warning"]

