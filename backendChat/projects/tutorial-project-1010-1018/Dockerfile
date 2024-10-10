# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory to /files
WORKDIR /files

# Copy the directory contents into the container at /files
COPY files/ .

# Install any needed packages specified in requirements
RUN pip install numpy pandas scikit-learn matplotlib stumpy networkx tqdm

# Make port 80 available to the world outside this container
EXPOSE 80