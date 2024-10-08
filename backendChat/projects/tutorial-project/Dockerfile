# Use the official Python image from the Docker Hub
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /files

# Copy the local directory files into the container
COPY files/ .

# Install necessary Python packages listed as dependencies
RUN pip install numpy pandas matplotlib networkx scikit-learn stumpy tqdm