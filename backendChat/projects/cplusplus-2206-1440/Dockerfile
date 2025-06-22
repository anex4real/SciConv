# Use the official Ubuntu image as the base
FROM ubuntu:20.04

# Avoiding user interaction with tzdata
ENV DEBIAN_FRONTEND=noninteractive

# Install essential tools
RUN apt-get update && apt-get install -y \
    g++ \
    make \
    libcurl4-openssl-dev \
    libgumbo-dev

# Set the working directory to /files
WORKDIR /files

# Copy all the files from the local "files" directory to the Docker image's "files" directory
COPY files/ .