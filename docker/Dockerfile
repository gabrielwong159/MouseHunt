# docker build -t mh_bot .
FROM python:3.7-slim

# add google chrome to apt sources
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl gnupg unzip
RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add \
    && echo "deb [arch=amd64]  http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list

# install all module dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        # chromedriver dependencies
        google-chrome-stable=76.0.3809.132-1 xvfb xauth \
        # tesseract dependencies
        g++ autoconf automake libtool pkg-config \
        libpng-dev libjpeg62-turbo-dev libtiff5-dev zlib1g-dev \
        libleptonica-dev tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# install chromedriver
RUN wget https://chromedriver.storage.googleapis.com/76.0.3809.68/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/bin/chromedriver \
    && chown root:root /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver

# download project and install python dependencies
WORKDIR /home
RUN git clone -b docker --single-branch https://github.com/gabrielwong159/MouseHunt.git

WORKDIR /home/MouseHunt
RUN pip3 install -r requirements.txt

CMD xvfb-run python3 main.py

