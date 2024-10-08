FROM python:3-slim

RUN apt-get update && apt-get install -y bash

WORKDIR /files

COPY files/ .

RUN pip install requests beautifulsoup4 pandas