#!/bin/bash
# Setup script for Tiger ID

set -e

echo "Setting up Tiger ID..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠ Please edit .env with your configuration before continuing"
fi

# Start infrastructure services
echo "Starting infrastructure services..."
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
cd backend
alembic upgrade head
cd ..

# Initialize database
echo "Initializing database..."
python scripts/init_db.py

echo ""
echo "✓ Setup complete!"
echo ""
echo "To start the application:"
echo "  streamlit run app/app.py"
echo ""
echo "To start all services:"
echo "  docker-compose up -d"

