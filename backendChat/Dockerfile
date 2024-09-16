# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory to /files
WORKDIR /files

# Copy the current directory contents into the container at /files
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install flask==2.3.2 flask-cors==3.0.10 beautifulsoup4==4.11.1 docker==5.0.3 openai
EXPOSE 8080

ENV OPENAI_API_KEY=sk-proj-qepUh5gGMRDgmqTRIVNpT3BlbkFJpOAXTCkCnvYtUTFvEKJk
CMD ["python",  "main.py"]