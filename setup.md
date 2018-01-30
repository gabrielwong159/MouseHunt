Several packages such as `libjpeg` and `zlib` are required.  
[Source](http://pillow.readthedocs.io/en/4.0.x/installation.html#linux-installation)
```
sudo apt-get install libjpeg zlib
```

## Setting up GeckoDriver
Go to the website to download `geckodriver`. Also download `iceweasel` for use in conjunction with `geckodriver`.

```
sudo apt-get install iceweasel

wget https://github.com/mozilla/geckodriver/releases/download/v0.18.0/geckodriver-v0.18.0-arm7hf.tar.gz
tar -xvzf geckodriver*
sudo mv geckodriver /usr/bin
```

## Setting up Tesseract OCR
```
sudo apt-get install tesseract-ocr
```
