# GenASL Deployment Guide

## Overview

GenASL is a Speech-to-ASL video generation system. This guide covers deploying it to production with minimal resources using Railway.app.

### Project Architecture

- **Backend**: FastAPI (Python) - Processes text, generates gloss, stitches videos
- **Frontend**: React + Vite - Chat UI with microphone support
- **Services Required**: MinIO (storage), Ollama (LLM), FFmpeg (video processing)

---

## Option 1: Deploy to Railway.app (Recommended for Resume)

Railway.app offers a free tier and is ideal for portfolio projects.

### Prerequisites

1. **GitHub Account** - Railway deploys from git repos
2. **Railway Account** - Sign up at https://railway.app
3. **Git Repository** - Push your code to GitHub

### Steps

#### 1. Push Code to GitHub

```bash
# In your project root
git init
git add .
git commit -m "Initial commit: GenASL deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/GenASL.git
git push -u origin main
```

#### 2. Set Up Railway Project

1. Go to [https://railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub"
4. Connect your GitHub account and select the GenASL repository
5. Railway will automatically detect the Dockerfile

#### 3. Configure Services

Railway uses these services:

```
Backend Service:
- Build: Dockerfile
- Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
- Environment Variables: (see below)

Frontend Service:
- Build: frontend/ with Dockerfile.prod
- Port: 3000
```

#### 4. Set Environment Variables

In Railway dashboard, add these variables:

**Backend Service:**
```
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2
WHISPER_DEVICE=cpu
WHISPER_MODEL_SIZE=tiny
ASL_WORDS_DIR=/app/demo_data/words
ENVIRONMENT=production
```

**Frontend Service:**
```
REACT_APP_API_URL=https://YOUR_RAILWAY_BACKEND_URL
REACT_APP_WS_URL=wss://YOUR_RAILWAY_BACKEND_URL
```

#### 5. Deploy

```bash
# Push changes trigger automatic deployment
git push origin main
```

Monitor deployment in Railway dashboard. First deployment takes 5-10 minutes.

---

## Option 2: Local Development & Testing

For local testing before deploying:

### Prerequisites

- Docker & Docker Compose installed
- Python 3.11
- Node.js 20+

### Quick Start

```bash
# From project root

# 1. Start services
docker-compose up -d

# 2. Wait for services to be healthy (~30s)
docker-compose logs -f

# 3. Initialize demo data
python scripts/create_demo_dataset.py

# 4. Test backend health
curl http://localhost:8000/health

# 5. Open frontend
# http://localhost:3000
```

### Stop Services

```bash
docker-compose down
```

---

## Option 3: Manual Deployment to AWS EC2

For production-grade hosting:

### 1. Create EC2 Instance

```bash
# t3.medium recommended (free tier: t2.micro with limitations)
# Ubuntu 22.04 LTS
# Security Group: Allow ports 80, 443, 8000, 5173
```

### 2. Install Dependencies

```bash
ssh -i your-key.pem ec2-user@your-instance-ip

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo apt-get install git -y
```

### 3. Deploy

```bash
# Clone repo
git clone https://github.com/YOUR_USERNAME/GenASL.git
cd GenASL

# Start with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f
```

### 4. Set Up Reverse Proxy (Nginx)

```bash
sudo apt-get install nginx -y
```

Create `/etc/nginx/sites-available/genasL`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_websocket_enabled on;
    }
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/genasL /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

---

## Demo Dataset

For initial deployment, a minimal demo dataset is included with these ASL signs:

- HELLO
- THANK
- YOU
- GOOD
- MORNING
- NAME
- WHAT
- YOUR

This provides enough functionality to demonstrate the system without requiring the full ASLLVD dataset (~50GB).

### Using Full Dataset

To add the complete ASLLVD dataset:

1. Download ASLLVD from: http://asllvd.org/
2. Extract to `asllvd_raw/`
3. Run extraction scripts:

```bash
python extract_all_poses.py
python extract_all_head.py
```

---

## Testing the Deployment

### 1. Health Checks

```bash
# Backend health
curl https://your-domain.com/api/health

# Frontend
# Visit https://your-domain.com
```

### 2. Test API

```bash
curl -X POST https://your-domain.com/api/jobs/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "hello world"}'
```

### 3. Test Frontend

- Navigate to https://your-domain.com
- Type "hello" in the chat
- Click "Generate ASL Translation"
- Wait for video generation (30-60 seconds depending on server)

---

## Troubleshooting

### Issue: Backend not responding

```bash
# Check logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

### Issue: Video not generating

```bash
# Ensure demo data exists
ls -la demo_data/words/

# Check MinIO connection
curl http://localhost:9000/minio/health/live

# Check Ollama connection
curl http://localhost:11434/api/generate -d '{"model":"llama2", "prompt":"test"}'
```

### Issue: Frontend can't reach backend

Check environment variables:
```bash
# In Railway or your deployment
REACT_APP_API_URL=https://your-backend-url
```

---

## Resumé Presentation

### What to Include

1. **GitHub Link**: https://github.com/YOUR_USERNAME/GenASL
   - Shows code quality and organization
   
2. **Live Demo Link**: https://genasL.railway.app
   - Interactive demonstration of system
   
3. **Project Description**:
   > GenASL: A full-stack Speech-to-ASL video generation system built with Python/FastAPI backend and React frontend. Processes English text, generates ASL gloss using LLM (Ollama), matches video clips from ASLLVD dataset, and stitches them into coherent ASL videos. Deployed on Railway.app.

4. **Key Technologies**:
   - Backend: Python, FastAPI, Ollama, FFmpeg, MediaPipe
   - Frontend: React, Vite, Tailwind CSS
   - DevOps: Docker, Docker Compose, Railway.app

5. **Key Features**:
   - ✅ Real-time speech-to-text transcription
   - ✅ LLM-powered gloss generation
   - ✅ Video stitching pipeline
   - ✅ Skeleton/pose visualization
   - ✅ Full API documentation

---

## Cost Estimate

| Service | Cost |
|---------|------|
| Railway (backend + frontend) | Free-$5/month |
| Domain name (.com via Namecheap) | $0.98/year |
| **Total** | **~$1/month** |

---

## Next Steps

1. ✅ Push code to GitHub
2. ✅ Create Railway account and connect GitHub
3. ✅ Deploy backend and frontend
4. ✅ Test live deployment
5. ✅ Add to resumé with live link

Good luck with your deployment! 🚀
