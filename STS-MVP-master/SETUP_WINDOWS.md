# STS MVP Windows Setup

## 1) Open the correct project root
This repo is nested. Use this folder as root:

C:/Users/ashis/Downloads/STS-MVP-master/STS-MVP-master

## 2) Install system prerequisites
- Python 3.10 or 3.11 (recommended)
- Node.js 20+
- FFmpeg (must provide ffmpeg + ffprobe in PATH)
- Ollama (for text -> gloss generation)
- MinIO server (for generated video URLs)

## 3) Prepare dataset folders
At project root, create this structure:

asl_videos/
  words/
  poses/
  heads/
  stitched/
asllvd_raw/
asllvd_metadata/

Notes:
- Put your downloaded ASLLVD batch videos in asllvd_raw/.
- Put the ASLLVD CSV metadata file in asllvd_metadata/ with the name:
  asllvd_signs_2024_06_27.csv

## 4) Build words clips from raw ASLLVD videos
From backend folder:

cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python asllvd_streaming_cutter.py
python renaming_hash_clips.py

This creates normalized sign clips in asl_videos/words.

## 5) Extract pose/head arrays
From project root:

cd ..
python extract_all_poses.py
python extract_all_head.py

This creates .npy files in asl_videos/poses and asl_videos/heads.

## 6) Configure backend environment
In backend, copy .env.example -> .env and fill values.
Required minimum:
- ASL_WORDS_DIR=absolute path to asl_videos/words
- MINIO_ENDPOINT=127.0.0.1:9000
- MINIO_ACCESS_KEY=minioadmin
- MINIO_SECRET_KEY=minioadmin
- MINIO_SECURE=false
- OLLAMA_URL=http://localhost:11434
- OLLAMA_MODEL=llama3
- WHISPER_DEVICE=cpu
- WHISPER_MODEL_SIZE=small
- WHISPER_COMPUTE_TYPE=int8

Install spaCy English model once:

python -m spacy download en_core_web_sm

## 7) Start MinIO and Ollama
MinIO (Docker):

docker run -p 9000:9000 -p 9001:9001 --name minio -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin -v minio_data:/data quay.io/minio/minio server /data --console-address ":9001"

Ollama:

ollama serve
ollama pull llama3

## 8) Run backend
From backend folder:

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

## 9) Run frontend
In a new terminal:

cd frontend
npm install
npm run dev

Open the URL shown by Vite (usually http://127.0.0.1:5173).

## 10) Quick health checks
- Backend docs: http://127.0.0.1:8000/docs
- Frontend microphone prompt should appear.
- Press Generate ASL Translation after speech input.

## Common failures
- RuntimeError MINIO_ENDPOINT not set: set backend .env correctly.
- OSError Missing spaCy model: run python -m spacy download en_core_web_sm.
- ffmpeg/ffprobe not found: install FFmpeg and restart terminal.
- No videos generated: check asl_videos/words is populated.
- WS transcribe unstable on CPU: set WHISPER_DEVICE=cpu and use smaller model.
