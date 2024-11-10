# docker build -t mh-bot .
FROM python:3.9-slim AS requirements

RUN python -m pip install --no-cache-dir --upgrade poetry

COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --without-hashes -o /requirements.txt


FROM python:3.9-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 tesseract-ocr libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=requirements /requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src

CMD ["python", "-m", "src.main"]
