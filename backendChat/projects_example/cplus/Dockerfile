# Use an official C++ base image
FROM gcc:latest

# Set the working directory in the container
WORKDIR /files

# Copy the local directory files to the container's workspace.
COPY files/ .

# Install any needed dependencies here
# Since no external dependencies were specified just upgrade the system
RUN apt-get update && apt-get upgrade -y