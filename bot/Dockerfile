# docker build -t mh-bot .
FROM python:3.9-slim

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY ./src ./src
WORKDIR ./src

CMD ["python", "main.py"]
