# GenASL - Speech to ASL Video Generation

A full-stack application that converts English speech or text into American Sign Language videos using pre-recorded sign clips, LLM-powered gloss generation, and video stitching.

![Project Demo](./docs/demo.gif)

## 🎯 Quick Start (5 minutes)

### Option A: Try Locally with Docker (Recommended for Testing)

```bash
# 1. Create demo dataset
python scripts/create_demo_dataset.py

# 2. Start all services
docker-compose up -d

# 3. Wait ~30 seconds for services to initialize
docker-compose logs -f  # Press Ctrl+C when ready

# 4. Visit http://localhost:3000
# 5. Type "hello" and click Generate ASL Translation
```

Stop with: `docker-compose down`

### Option B: Deploy to Production (Railway.app)

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for step-by-step instructions.

**One-click Deploy**: [Deploy to Railway](#)

---

## 📋 System Requirements

### Local Development
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- FFmpeg
- 8GB RAM minimum

### Cloud Deployment
- GitHub account
- Railway.app account (free tier available)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (React + Vite)         │
│  - Chat UI with text/voice input        │
│  - Video playback and visualization     │
└────────────────┬────────────────────────┘
                 │ HTTP/WebSocket
         ┌───────▼────────┐
         │  FastAPI REST  │
         │   Backend      │
         ├────────────────┤
         │ LLM (Ollama)   │
         │ FFmpeg (video) │
         │ MinIO (storage)│
         └────────────────┘
                 │
    ┌────────────┼─────────────┐
    │            │             │
    ▼            ▼             ▼
┌────────┐ ┌────────┐ ┌──────────────┐
│ MinIO  │ │ Ollama │ │ ASLLVD Data  │
│ Videos │ │ Models │ │ Signs & Pose │
└────────┘ └────────┘ └──────────────┘
```

---

## 🔧 Local Development Setup

### 1. Clone & Setup

```bash
git clone https://github.com/YOUR_USERNAME/GenASL.git
cd GenASL

# Create Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cd ..

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Create Demo Dataset

```bash
python scripts/create_demo_dataset.py
```

### 3. Start Services

**Option A: Docker Compose (Recommended)**
```bash
docker-compose up -d
# Frontend: http://localhost:3000
# Backend: http://localhost:8000/docs
```

**Option B: Manual Start**

Terminal 1 - Backend:
```bash
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

Terminal 3 - MinIO (Docker):
```bash
docker run -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  quay.io/minio/minio server /data
```

Terminal 4 - Ollama:
```bash
ollama serve
# In another terminal: ollama pull llama2
```

---

## 🚀 Deployment

### Quick Deploy to Railway.app

1. Push code to GitHub
2. Go to [Railway.app](https://railway.app)
3. Click "New Project" → "Deploy from GitHub"
4. Select this repository
5. Railway auto-detects Dockerfile and deploys

**Full instructions**: See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

---

## 📚 API Documentation

### Available Endpoints

**Health Check**
```bash
GET /health
```

**Generate ASL Video**
```bash
POST /jobs/generate
Content-Type: application/json

{
  "text": "Hello, what is your name?",
  "speed": 1.0,
  "include_pose": true
}
```

**Get Job Status**
```bash
GET /jobs/{job_id}
```

**Full API Docs**: http://localhost:8000/docs (when running)

---

## 🎮 Features

- ✅ **Speech Recognition**: Real-time transcription using Whisper
- ✅ **Text Input**: Type English sentences
- ✅ **ASL Gloss Generation**: LLM-powered conversion to ASL glosses
- ✅ **Video Stitching**: Combines pre-recorded sign clips
- ✅ **Pose Visualization**: Optional skeleton visualization
- ✅ **Job Queue**: Asynchronous processing with status tracking
- ✅ **Responsive UI**: Mobile-friendly React interface

---

## 📊 Dataset

### Demo Dataset
Includes 8 basic signs for testing (included in repo).

### Full ASLLVD Dataset
For production, download from [ASLLVD Project](http://asllvd.org/):

```bash
# Extract videos to asllvd_raw/
python extract_all_poses.py
python extract_all_head.py
# Creates: asl_videos/words/, poses/, heads/
```

---

## 🛠️ Configuration

### Backend (.env)

```env
# LLM Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Audio Processing
WHISPER_DEVICE=cpu
WHISPER_MODEL_SIZE=tiny

# Paths
ASL_WORDS_DIR=/path/to/asl_videos/words
```

### Frontend (.env)

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Health checks
curl http://localhost:8000/health
curl http://localhost:3000
```

---

## 📦 Project Structure

```
GenASL/
├── backend/              # FastAPI Python application
│   ├── app/
│   │   ├── main.py      # FastAPI app
│   │   ├── job_manager.py
│   │   ├── llm_service.py
│   │   ├── stitching_service.py
│   │   └── pose_service.py
│   ├── requirements.txt
│   └── .env.deployment
├── frontend/             # React + Vite
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/LiveSTT.jsx
│   │   └── index.css
│   ├── package.json
│   └── Dockerfile.prod
├── scripts/              # Data processing & setup
│   ├── create_demo_dataset.py
│   └── extract_all_poses.py
├── demo_data/            # Sample data for testing
│   ├── words/            # Video clips
│   ├── poses/            # Skeleton data
│   └── heads/            # Face data
├── docker-compose.yml    # Local dev environment
├── Dockerfile            # Backend containerization
├── railway.json          # Railway.app config
├── DEPLOYMENT_GUIDE.md   # Detailed deployment docs
└── README.md             # This file
```

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check environment variables
cat backend/.env

# Restart services
docker-compose restart backend

# View logs
docker-compose logs backend
```

### No video generation
```bash
# Check demo data exists
ls -la demo_data/words/

# Verify Ollama is running
curl http://localhost:11434/api/generate
```

### Frontend can't reach backend
```bash
# Check API URL is correct
echo $REACT_APP_API_URL

# Test backend directly
curl http://localhost:8000/health
```

---

## 📄 License

MIT License - Feel free to use this for portfolios and learning.

---

## 🤝 Contributing

Contributions welcome! To improve GenASL:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 💬 Support

For issues or questions:
- 📖 See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- 🐛 Check existing [GitHub Issues](https://github.com/YOUR_USERNAME/GenASL/issues)
- 💡 Open a new issue with details

---

## 👨‍💻 About

**GenASL** was developed as a demonstration of full-stack software engineering, covering:
- **Backend**: RESTful APIs, async job processing, LLM integration
- **Frontend**: React UI, real-time transcription, video streaming
- **DevOps**: Docker containerization, cloud deployment
- **ML/AI**: Whisper speech recognition, Ollama LLM integration, MediaPipe pose detection
- **Video Processing**: FFmpeg stitching and pipeline automation

Perfect for showcasing modern software development skills.

---

Made with ❤️ by Your Name
