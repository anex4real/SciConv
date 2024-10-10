FROM ubuntu:latest

# Install Bash
RUN apt-get update && apt-get install -y bash

# Set the working directory
WORKDIR /files

# Copy all files into the container
COPY files/ .