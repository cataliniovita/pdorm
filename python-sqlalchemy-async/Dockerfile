FROM python:3.12-alpine

RUN apk add --no-cache curl build-base postgresql-dev

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py /app/app.py

EXPOSE 5000
CMD ["python", "app.py"]


