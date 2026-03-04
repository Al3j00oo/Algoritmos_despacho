FROM python:3.11

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt
RUN reflex init

EXPOSE 3000
EXPOSE 8000

CMD ["reflex", "run", "--env", "prod", "--backend-host", "0.0.0.0"]
