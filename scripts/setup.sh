#!/bin/bash
set -e

echo "Starting RAG application..."

# Initialize database
echo "Initializing database..."
python scripts/init_db.py

# Start the Flask application
echo "Starting Flask app..."
python app.py
# For production
# exec gunicorn app:app --timeout 300 --bind 0.0.0.0:5000