# docker build -t mh-bot .
FROM python:3.9-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 tesseract-ocr libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY ./src ./src
WORKDIR ./src

CMD ["python", "main.py"]
