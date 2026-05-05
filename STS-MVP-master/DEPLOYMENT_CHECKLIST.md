# GenASL Deployment Checklist

Complete this checklist to deploy your project to Railway.app for your resume.

## Step 1: Prepare Your GitHub Repository ✓

- [ ] Create GitHub account (if you don't have one): https://github.com/signup
- [ ] Create a new repository called `GenASL`
- [ ] Clone this project locally

```bash
# In your project folder:
git init
git add .
git commit -m "Initial commit: GenASL"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/GenASL.git
git push -u origin main
```

## Step 2: Create Railway.app Account ✓

- [ ] Go to https://railway.app
- [ ] Sign up (free)
- [ ] Authorize with GitHub

## Step 3: Deploy Backend on Railway ✓

1. [ ] In Railway Dashboard: Click "New Project"
2. [ ] Select "Deploy from GitHub"
3. [ ] Choose your `GenASL` repository
4. [ ] Railway auto-detects the `Dockerfile`
5. [ ] Add environment variables:
   - `MINIO_ENDPOINT=localhost:9000`
   - `OLLAMA_URL=http://localhost:11434`
   - `OLLAMA_MODEL=llama2`
   - `WHISPER_DEVICE=cpu`
   - `WHISPER_MODEL_SIZE=tiny`
   - `ASL_WORDS_DIR=/app/demo_data/words`
   - `ENVIRONMENT=production`

## Step 4: Deploy Frontend on Railway ✓

1. [ ] In same Railway Project: Click "New Service"
2. [ ] Select GitHub (same repo)
3. [ ] Set build path to: `frontend`
4. [ ] Set Dockerfile: `Dockerfile.prod`
5. [ ] Add environment variables:
   - `REACT_APP_API_URL=https://YOUR_BACKEND_URL` (get from Railway)

## Step 5: Test Deployment ✓

- [ ] Wait for both services to deploy (5-10 minutes)
- [ ] Visit frontend URL
- [ ] Type "hello" in chat
- [ ] Click "Generate ASL Translation"
- [ ] Confirm video generates (may take 30-60s)

## Step 6: Add to Resume ✓

Include these in your portfolio:

```markdown
### GenASL - Speech to ASL Video Generator
**Live Demo**: https://genasL.railway.app
**GitHub**: https://github.com/YOUR_USERNAME/GenASL

A full-stack application converting English speech to American Sign Language videos.
- **Backend**: Python FastAPI, Ollama LLM, FFmpeg video processing
- **Frontend**: React, Vite, Tailwind CSS
- **Deployment**: Docker, Railway.app

Key Features:
- Real-time speech recognition with Whisper
- LLM-powered English-to-ASL gloss conversion
- Video stitching of pre-recorded sign clips
- Pose/skeleton visualization
- Responsive web interface
```

## Step 7: Optional Enhancements ✓

### Add Custom Domain (Optional)

1. [ ] Go to Railway Project Settings
2. [ ] Add Custom Domain: `genasL.yourdomain.com`
3. [ ] Update DNS records (Railway will provide instructions)

### Add GitHub Actions CI/CD (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy with Railway CLI
        run: |
          npx @railway/cli deploy --force
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

### Add Status Badge to README (Optional)

```markdown
[![Deploy](https://img.shields.io/badge/deploy-railway-0B0D0E?style=flat&labelColor=000&logo=railway&logoColor=0B0D0E)](https://railway.app/template)
```

---

## Troubleshooting Deployment

### Backend Service Fails to Deploy

**Error**: `Dockerfile not found`
- ✓ Make sure `Dockerfile` is in project root
- ✓ Commit and push: `git push origin main`

**Error**: `Port already in use`
- ✓ Railway auto-assigns ports; ignore local port conflicts

**Error**: `Service won't start`
- View logs in Railway Dashboard
- Check all environment variables are set
- Verify `.env.deployment` has correct values

### Frontend Shows Blank Page

- [ ] Check `REACT_APP_API_URL` environment variable is set
- [ ] Verify backend URL is correct (from Railway)
- [ ] Check browser console for errors (F12)

### Video Won't Generate

- [ ] Backend logs show error? View in Railway
- [ ] Check demo data exists: `demo_data/words/`
- [ ] Ensure `OLLAMA_URL` and `MINIO_ENDPOINT` are correct

---

## Quick Reference

| Component | URL |
|-----------|-----|
| Frontend | https://genasL.railway.app |
| Backend API | https://genasL-backend.railway.app |
| API Docs | https://genasL-backend.railway.app/docs |
| GitHub Repo | https://github.com/YOUR_USERNAME/GenASL |

---

## How It Works (For Interviews)

**Question**: "Tell me about GenASL"

**Answer Template**:
> GenASL is a full-stack web application that converts English speech or text into American Sign Language videos. 
> 
> **How it works**:
> 1. User speaks or types English text
> 2. Backend transcribes audio with OpenAI's Whisper
> 3. LLM (Ollama) converts English to ASL glosses
> 4. System matches glosses to pre-recorded sign videos from ASLLVD dataset
> 5. FFmpeg stitches videos together
> 6. Frontend displays final ASL video with skeleton overlay
>
> **Technologies**:
> - Backend: Python/FastAPI, MediaPipe, FFmpeg
> - Frontend: React/Vite with Tailwind CSS
> - Infrastructure: Docker, Railway.app (deployed on free tier)
>
> **Key Challenge**: Matching natural English to visual ASL while maintaining grammatical correctness
> 
> **Solution**: Combined LLM-powered gloss generation with video stitching pipeline

---

## Success Indicators ✓

If you see these, your deployment is working:

- ✅ Frontend loads at `https://genasL.railway.app`
- ✅ Chat interface appears with text input
- ✅ Backend health check: `/health` returns 200
- ✅ Video generation works (takes 30-60 seconds)
- ✅ Skeleton visualization displays
- ✅ All visible in browser without errors

---

## Next: Polish for Interviews

1. **Add Project Screenshot**: Save screenshot of working app
2. **Record Demo Video**: Show text→ASL generation
3. **Practice Explanation**: 2-minute demo script
4. **Prepare Technical Details**: Be ready to discuss architecture
5. **Show Code**: Have GitHub repo organized and documented

---

**You're ready to deploy! Questions?**

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed help.

🚀 Good luck with your interviews!
