#!/bin/bash
# Start script for Render deployment
# Uses PORT environment variable (provided by Render) or defaults to 8000

PORT=${PORT:-8000}
echo "Starting ReguChain Backend on port $PORT..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
