#!/bin/bash

# ReguChain Watch Demo Script
# This script demonstrates the real-time RAG system with before/after simulation

echo "================================================"
echo "ReguChain Watch - Real-time RAG Demo"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Copying from .env.example${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please update .env with your API keys before running the demo${NC}"
    echo ""
fi

# Function to check if service is running
check_service() {
    if curl -s -o /dev/null -w "%{http_code}" $1 | grep -q "200"; then
        echo -e "${GREEN}✓ $2 is running${NC}"
        return 0
    else
        echo -e "${RED}✗ $2 is not running${NC}"
        return 1
    fi
}

# Start services
echo "Starting services..."
echo "--------------------"

# Option 1: Docker Compose (Recommended)
if command -v docker-compose &> /dev/null; then
    echo "Starting with Docker Compose..."
    docker-compose up -d --build
    echo "Waiting for services to start (30 seconds)..."
    sleep 30
else
    echo "Docker Compose not found. Starting services manually..."
    
    # Start backend
    echo "Starting backend..."
    cd backend
    pip install -r requirements.txt
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    cd ..
    
    # Start frontend
    echo "Starting frontend..."
    cd frontend
    npm install
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    
    echo "Waiting for services to start (20 seconds)..."
    sleep 20
fi

echo ""
echo "Checking service health..."
echo "--------------------------"

# Check if services are running
check_service "http://localhost:8000/health" "Backend API"
BACKEND_STATUS=$?

check_service "http://localhost:3000" "Frontend"
FRONTEND_STATUS=$?

if [ $BACKEND_STATUS -ne 0 ] || [ $FRONTEND_STATUS -ne 0 ]; then
    echo -e "${RED}Error: Services are not running properly${NC}"
    echo "Please check the logs and ensure all dependencies are installed"
    exit 1
fi

echo ""
echo -e "${GREEN}All services are running!${NC}"
echo ""

# Demo walkthrough
echo "================================================"
echo "DEMO WALKTHROUGH"
echo "================================================"
echo ""

echo "1. Open your browser at: http://localhost:3000"
echo ""

echo "2. Initial Query (BEFORE simulation):"
echo "   - Question: 'Is wallet 0xDEMO0001 involved in any sanctions or illegal activities?'"
echo "   - Target: '0xDEMO0001'"
echo "   - Expected: Low to medium risk (depending on initial data)"
echo ""

echo "3. Click 'Analyze' and observe:"
echo "   - Risk score gauge"
echo "   - Evidence sources from regulatory feeds"
echo "   - Live feed showing recent ingestions"
echo ""

echo "4. Simulate New Sanction:"
echo "   - Click the yellow 'Simulate Ingestion' button"
echo "   - This will inject new OFAC and news entries for the target"
echo "   - Watch the Live Feed update with new entries"
echo ""

echo "5. Re-run Query (AFTER simulation):"
echo "   - Use the same question and target"
echo "   - Expected: HIGH RISK (70+ score)"
echo "   - New evidence will show the simulated sanctions"
echo ""

echo "================================================"
echo "API ENDPOINTS FOR TESTING"
echo "================================================"
echo ""

echo "Backend API Documentation: http://localhost:8000/docs"
echo ""

echo "Test commands:"
echo "--------------"

echo "1. Check system status:"
echo "   curl http://localhost:8000/api/status | jq"
echo ""

echo "2. Run a query:"
echo "   curl -X POST http://localhost:8000/api/query \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"question\": \"Check 0xDEMO0001\", \"target\": \"0xDEMO0001\"}' | jq"
echo ""

echo "3. Simulate ingestion:"
echo "   curl -X POST http://localhost:8000/api/ingest/simulate \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"target\": \"0xDEMO0001\"}' | jq"
echo ""

echo "================================================"
echo "RECORDING THE DEMO VIDEO"
echo "================================================"
echo ""

echo "Tips for recording:"
echo "1. Start recording before opening the browser"
echo "2. Show the initial query with low/medium risk"
echo "3. Highlight the 'Simulate Ingestion' button"
echo "4. Show the Live Feed updating in real-time"
echo "5. Re-run the same query to show HIGH RISK"
echo "6. Expand evidence to show new sanctions"
echo "7. Total demo time: 2-3 minutes"
echo ""

echo -e "${GREEN}Demo is ready! Open http://localhost:3000 to begin${NC}"
echo ""

# Keep script running
echo "Press Ctrl+C to stop all services..."
wait
