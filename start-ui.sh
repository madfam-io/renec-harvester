#!/bin/bash
# Startup script for RENEC Harvester UI

echo "Starting RENEC Harvester Web Interface..."

# Kill any existing processes on our ports
echo "Cleaning up existing processes..."
lsof -ti:3001 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start FastAPI backend
echo "Starting FastAPI backend on port 8000..."
cd /Users/aldoruizluna/labspace/renec-harvester
source venv/bin/activate
python -m src.api.main &
FASTAPI_PID=$!

# Give FastAPI time to start
sleep 3

# Start Next.js frontend  
echo "Starting Next.js frontend on port 3001..."
cd /Users/aldoruizluna/labspace/renec-harvester/ui
npm run dev &
NEXTJS_PID=$!

# Give Next.js time to start
sleep 5

echo ""
echo "🚀 RENEC Harvester Web Interface is starting up!"
echo ""
echo "📊 Frontend: http://localhost:3001"
echo "🔧 API Docs: http://localhost:8000/docs"  
echo "💾 Database: PostgreSQL on localhost:5432"
echo "🗂️  Redis: localhost:6379"
echo "📈 Grafana: http://localhost:3000 (admin/renec_grafana_pass)"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $FASTAPI_PID 2>/dev/null || true
    kill $NEXTJS_PID 2>/dev/null || true
    lsof -ti:3001 | xargs kill -9 2>/dev/null || true
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    echo "Services stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for processes to finish
wait $FASTAPI_PID $NEXTJS_PID