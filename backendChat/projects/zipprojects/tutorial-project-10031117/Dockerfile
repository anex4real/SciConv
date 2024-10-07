
FROM python:3.8-slim

RUN apt-get update && apt-get install -y \
    build-essential

RUN pip install numpy pandas stumpy tqdm networkx matplotlib scikit-learn pickle5

WORKDIR /files
COPY files .
