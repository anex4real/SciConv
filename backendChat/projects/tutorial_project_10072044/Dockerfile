
# Use an official Python runtime as a parent image
FROM python:3.6-slim

# Set the working directory to /files
WORKDIR /files

# Copy the current directory contents into the container at /files
COPY files/ .

# Install any needed packages specified in requirements.txt
RUN pip install numpy pandas stumpy tqdm matplotlib networkx scikit-learn

# Make port 80 available to the world outside this container
EXPOSE 80
