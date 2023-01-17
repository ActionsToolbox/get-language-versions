FROM python:3.11-alpine

RUN pip install beautifulsoup4 requests packaging

COPY entrypoint.py /entrypoint.py

ENTRYPOINT ["python", "/entrypoint.py"]
