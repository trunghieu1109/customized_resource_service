FROM python:3.12.8-alpine3.21

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN sed -i 's/mysignature/signature/g' /usr/local/lib/python3.12/site-packages/vastai/vast.py

COPY . .

COPY environment.ini .

EXPOSE 10309

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10309", "--reload"]
