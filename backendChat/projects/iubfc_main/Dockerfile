# Use the official C++ base image from the Docker Hub
FROM gcc:latest

# Set the working directory in the container
WORKDIR /files

# Copy the local directory files to the container's work directory
COPY files/ .

# Install general dependencies
RUN apt-get update && apt-get install -y \
    libc6-dev