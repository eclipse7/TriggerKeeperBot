# Pull base image
FROM python:3.7-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Copy project
COPY ./app/ /app/

# Install dependencies
RUN pip install -r /app/requirements.txt
