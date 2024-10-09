FROM python:3.8-slim-buster

RUN apt-get update && apt-get install -y \
    curl \
    jq \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /files
COPY files/ .