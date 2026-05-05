@echo off
REM Quick start script for GenASL local deployment (Windows)

echo.
echo 🚀 GenASL Local Deployment Script
echo ===================================
echo.

REM Check Docker
where docker >nul 2>nul
if errorlevel 1 (
    echo ❌ Docker not found. Please install Docker Desktop.
    exit /b 1
)

echo ✓ Docker found

REM Check Docker Compose
where docker-compose >nul 2>nul
if errorlevel 1 (
    echo ❌ Docker Compose not found. Please install Docker Desktop with Compose.
    exit /b 1
)

echo ✓ Docker Compose found

REM Create demo dataset
echo.
echo 📦 Creating demo dataset...
python scripts/create_demo_dataset.py

echo.
echo 🐳 Starting Docker Compose services...
docker-compose up -d

echo.
echo ⏳ Waiting for services to be healthy...
timeout /t 30

echo.
echo 📊 Service Status:
docker-compose ps

echo.
echo ✅ Services starting...
echo.
echo Access URLs:
echo   Frontend:     http://localhost:3000
echo   Backend:      http://localhost:8000
echo   Backend Docs: http://localhost:8000/docs
echo   MinIO Console: http://localhost:9001
echo.
echo Next steps:
echo   1. Visit http://localhost:3000
echo   2. Type 'hello' and click 'Generate ASL Translation'
echo   3. Wait 30-60 seconds for video generation
echo.
echo To stop: docker-compose down
echo.
echo For deployment: See DEPLOYMENT_GUIDE.md
echo.
pause
