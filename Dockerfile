# Use Python 3.11 as the base image
FROM python:3.11-slim

# Set working directory in the container
WORKDIR /app


# Copy requirements file first
COPY requirements.txt /app/

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
# Copy the rest of the application
COPY . /app/

# Make scripts executable
RUN chmod +x scripts/setup.sh

# Expose the port the app runs on
EXPOSE 5000

# Set environment variables
#ENV GOOGLE_APPLICATION_CREDENTIALS="/app/keys/arxiv-trends-key.json"
#ENV GOOGLE_CLOUD_PROJECT="arxiv-trends"

ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["bash", "scripts/setup.sh"]
# CMD ["python", "app.py"]
#CMD ["gunicorn", "app:app", "--timeout", "300", "--bind", "0.0.0.0:5000"]