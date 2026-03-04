FROM python:3.11

WORKDIR /app
COPY . .


RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

RUN pip install -r requirements.txt

RUN reflex init
RUN reflex export --frontend-only --no-zip 2>/dev/null || true

EXPOSE 8000

ENV API_URL=https://algoritmosdespacho-production.up.railway.app


CMD ["reflex", "run", "--env", "prod", "--backend-host", "0.0.0.0", "--backend-port", "8000"]