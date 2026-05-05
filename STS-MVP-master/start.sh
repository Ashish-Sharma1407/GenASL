#!/bin/bash
# Quick start script for GenASL local deployment

echo "🚀 GenASL Local Deployment Script"
echo "================================="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi

echo "✓ Docker found"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo "✓ Docker Compose found"

# Create demo dataset
echo ""
echo "📦 Creating demo dataset..."
if command -v python &> /dev/null; then
    python scripts/create_demo_dataset.py
else
    echo "⚠️  Python not found. Skipping demo dataset creation."
    echo "   Run manually: python scripts/create_demo_dataset.py"
fi

echo ""
echo "🐳 Starting Docker Compose services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy (30-60 seconds)..."
sleep 10

# Check services
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✅ Services starting..."
echo ""
echo "Access URLs:"
echo "  Frontend:     http://localhost:3000"
echo "  Backend:      http://localhost:8000"
echo "  Backend Docs: http://localhost:8000/docs"
echo "  MinIO Console: http://localhost:9001"
echo ""
echo "Next steps:"
echo "  1. Visit http://localhost:3000"
echo "  2. Type 'hello' and click 'Generate ASL Translation'"
echo "  3. Wait 30-60 seconds for video generation"
echo ""
echo "To stop: docker-compose down"
echo ""
echo "For deployment: See DEPLOYMENT_GUIDE.md"
