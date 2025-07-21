#!/bin/bash
set -e

echo "Starting RAG application..."


# Wait for Postgres and Elasticsearch to be ready
echo "Waiting for services..."
sleep 10

# Initialize database
echo "Initializing database..."
python scripts/init_db.py


# Ingest data to Elasticsearch
echo "Ingesting data into Elasticsearch..."
python modules/ingest_data.py

# Start the Flask application
echo "Starting Flask app..."
python app.py
# For production
# exec gunicorn app:app --timeout 300 --bind 0.0.0.0:5000
