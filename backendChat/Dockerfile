# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory to /files
WORKDIR /backendChat

# Copy the current directory contents into the container at /files
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 for the application
EXPOSE 8080




# Command to run your application
CMD ["python", "main.py"]
