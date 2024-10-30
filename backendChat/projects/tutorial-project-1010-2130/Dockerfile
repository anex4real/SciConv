# Use an official Ubuntu as the base image
FROM ubuntu:20.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Update and install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    apt-transport-https \
    ca-certificates \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install code-server (VS Code in browser)
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Create a user to run code-server
RUN useradd -m coder

# Set up work directory and permissions
WORKDIR /files
RUN chown -R coder:coder /home/coder

# Switch to the non-root user
USER coder

# Expose port for code-server
EXPOSE 8080

# Start code-server with default settings
CMD ["code-server", "--bind-addr", "0.0.0.0:8080", "--auth", "none", "/files"]


 #docker build -t visualcode:0 .
 #docker container run -p 8080:8080 visualcode:0