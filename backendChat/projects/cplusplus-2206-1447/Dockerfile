FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
    g++ \
    libcurl4-openssl-dev \
    libgumbo-dev

WORKDIR /files

COPY files/ .