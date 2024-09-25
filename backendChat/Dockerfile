# Use an official Python runtime as a parent image
FROM python:3.10

# Install Docker client (optional, if needed)
RUN apt-get update && apt-get install -y docker.io && rm -rf /var/lib/apt/lists/*

# Create a user and add to the docker group if it doesn't exist
RUN getent group docker || groupadd -g 1001 docker && \
    useradd -m -u 1001 -g docker youruser

# Set the working directory to /files
WORKDIR /files

# Copy the current directory contents into the container at /files
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 for the application
EXPOSE 8080

# Set the OpenAI API key as an environment variable
# NOTE: It is not recommended to hardcode sensitive keys in the Dockerfile
# Consider passing this in at runtime instead for security.
ENV OPENAI_API_KEY=sk-proj-qepUh5gGMRDgmqTRIVNpT3BlbkFJpOAXTCkCnvYtUTFvEKJk

# Switch to the new user
USER youruser

# Command to run your application
CMD ["python", "main.py"]
