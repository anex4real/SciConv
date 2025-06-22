FROM debian:bullseye-slim

RUN apt-get update && apt-get install -y \
    g++ \
    libcurl4-gnutls-dev \
    libgumbo-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /files
COPY files/ .