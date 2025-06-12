FROM python:3.12.8-alpine3.21

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY environment.ini .

EXPOSE 10311

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10311", "--reload", "--reload-dir", "./app"]
