FROM python:3.11

WORKDIR /app
COPY . .

# Node.js 20 (requerido por Reflex)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

RUN pip install -r requirements.txt
RUN reflex init

# Compilar el frontend durante el BUILD (aqui hay suficiente RAM)
ENV NODE_OPTIONS="--max-old-space-size=2048"
RUN reflex export --frontend-only --no-zip 2>/dev/null || true

EXPOSE 8000

ENV API_URL=https://algoritmosdespacho-production.up.railway.app

CMD ["reflex", "run", "--env", "prod", "--backend-host", "0.0.0.0", "--backend-port", "8000"]