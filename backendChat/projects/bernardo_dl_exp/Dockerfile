# Use the official Python image from the Docker Hub
FROM python:3.8-slim

# Set the working directory
WORKDIR /files

# Copy the contents of the files directory from the local host to the '/files' folder in the container
COPY files/ .

# Install the required dependencies
RUN pip install numpy scikit-learn