# Use an official Python runtime as a parent image
FROM python:3

# Set the working directory to /files
WORKDIR /files

# Copy the current directory contents into the container at /files
COPY files/ .

# Install any needed packages specified in requirements
RUN pip install requests beautifulsoup4 matplotlib