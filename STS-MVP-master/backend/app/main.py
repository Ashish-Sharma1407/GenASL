from dotenv import load_dotenv
load_dotenv()

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RENDER_SCRIPT = PROJECT_ROOT / "render_skeleton.py"


import os
from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File,WebSocket, WebSocketDisconnect
import asyncio
from fastapi.staticfiles import StaticFiles
from app.llm_service import english_to_asl_gloss_intent
from app.schema import StitchRequest
from app.job_manager import (
    create_job,
    get_job,
    JobStatus,
    run_generate_job,
    CANONICALIZER
)
from app.minio_service import upload_and_get_url
from app.stitching_service import stitch_gloss_keys, insert_pauses_between_signs
from app.pose_stitching_service import stitch_pose_sequences
import numpy as np
import tempfile
import subprocess
import sys
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ENABLE_STT = os.getenv("ENABLE_STT", "false").lower() == "true"

if ENABLE_STT:
    try:
        from app.realtime_whisper_service import router as stt_router
        app.include_router(stt_router)
    except Exception as exc:
        print(f"STT router disabled due to import error: {exc}")

PUBLIC_DIR = PROJECT_ROOT / "asl_videos" / "public"
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")


OUTPUT_DIR = os.path.abspath("../asl_videos/stitched")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _speech_to_text(audio_path: str) -> str:
    try:
        from app.whisper_service import speech_to_text
    except Exception as exc:
        raise RuntimeError(f"STT backend unavailable: {exc}") from exc
    return speech_to_text(audio_path)


# ============================================================
# LOW-LEVEL STITCHING (UNCHANGED)
# ============================================================

def run_stitch_job(job_id: str, gloss_keys: list[str]):
    job = get_job(job_id)
    if not job:
        return

    job.status = JobStatus.RUNNING

    try:
        # ======================
        # VIDEO STITCH (existing)
        # ======================
        tokens = insert_pauses_between_signs(gloss_keys)
        video_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")

        stitch_gloss_keys(tokens, video_path)

        video_url = upload_and_get_url(
            video_path,
            object_name=f"jobs/{job_id}.mp4"
        )

        # ======================
        # POSE STITCH (optional)
        # ======================
        skeleton_url = None
        skeleton_error = None
        try:
            poses, heads = stitch_pose_sequences(gloss_keys)

            with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as pose_f, \
                 tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as head_f:

                np.save(pose_f.name, poses)
                np.save(head_f.name, heads)

                skeleton_path = os.path.join(
                    OUTPUT_DIR, f"{job_id}_skeleton.mp4"
                )

                subprocess.run(
                    [
                        sys.executable,
                        str(RENDER_SCRIPT),
                        pose_f.name,
                        head_f.name,
                        skeleton_path,
                    ],
                    check=True
                )

            skeleton_url = upload_and_get_url(
                skeleton_path,
                object_name=f"jobs/{job_id}_skeleton.mp4"
            )
        except Exception as e:
            skeleton_error = str(e)

        # ======================
        # FINAL RESULT
        # ======================
        job.status = JobStatus.DONE
        job.result = {
            "video": video_url,
            "skeleton": skeleton_url,
            "skeleton_error": skeleton_error,
        }

    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)


@app.post("/jobs/stitch")
def submit_stitch_job(
    payload: StitchRequest,
    background_tasks: BackgroundTasks
):
    job = create_job()
    background_tasks.add_task(
        run_stitch_job, job.id, payload.gloss_keys
    )
    return {"job_id": job.id}


# ============================================================
# GENASL ENDPOINT (NEW)
# ============================================================

@app.post("/jobs/generate")
def submit_generate_job(
    payload: dict,  # { "text": "Can you help me with my homework?" }
    background_tasks: BackgroundTasks
):
    if "text" not in payload or not payload["text"].strip():
        raise HTTPException(status_code=400, detail="Missing text")

    job = create_job()
    output_path = os.path.join(OUTPUT_DIR, f"{job.id}.mp4")

    background_tasks.add_task(
        run_generate_job,
        job.id,
        payload["text"],
        output_path,
        upload_and_get_url,
    )

    return {"job_id": job.id}

# ============================================================
# SPEECH → GENASL ENDPOINT (NEW)
# ============================================================

@app.post("/jobs/generate-from-audio")
async def submit_generate_audio_job(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No audio file")

    # Save uploaded audio temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        audio_path = tmp.name

    # ======================
    # SPEECH → TEXT
    # ======================
    try:
        text = _speech_to_text(audio_path)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Speech could not be recognized"
        )

    # ======================
    # EXISTING PIPELINE
    # ======================
    job = create_job()
    output_path = os.path.join(OUTPUT_DIR, f"{job.id}.mp4")

    background_tasks.add_task(
        run_generate_job,
        job.id,
        text,
        output_path,
        upload_and_get_url,
    )

    return {
        "job_id": job.id,
        "recognized_text": text
    }


@app.websocket("/ws/realtime-translate")
async def realtime_translate(ws: WebSocket):
    await ws.accept()

    try:
        while True:
            # Receive audio chunk
            audio_bytes = await ws.receive_bytes()

            # Save temporary chunk
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_bytes)
                audio_path = tmp.name

            # Speech → text
            try:
                text = _speech_to_text(audio_path)
            except RuntimeError:
                await ws.send_json({
                    "error": "STT backend unavailable on this machine"
                })
                await ws.close()
                return

            if not text:
                continue

            # Text → gloss pipeline (reuse existing)
            intent = english_to_asl_gloss_intent(text)
            glosses = CANONICALIZER.canonicalize(intent)

            if not glosses:
                continue

            # Send gloss tokens immediately
            await ws.send_json({
                "text": text,
                "glosses": glosses
            })

    except WebSocketDisconnect:
        pass


# ============================================================
# JOB POLLING
# ============================================================

@app.get("/jobs/{job_id}")
def poll_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "status": job.status,
        "result": job.result,
        "error": job.error,
    }


# @app.post("/poses/{gloss}")
# def generate_pose(gloss: str):
#     try:
#         path = extract_pose_for_gloss(gloss)
#         return {"gloss": gloss, "pose_path": path}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
