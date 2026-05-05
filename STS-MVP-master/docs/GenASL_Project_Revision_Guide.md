# GenASL Project Revision Guide

## 1. Project Name

The project is called GenASL.

GenASL is a Speech/Text to American Sign Language video generation system.

In simple words, the user speaks or types an English sentence, and the system creates an ASL video by joining together pre-recorded ASL sign clips.

## 2. One-Line Explanation

GenASL converts English speech or typed text into an American Sign Language video using ASLLVD dataset sign clips, an LLM for ASL gloss generation, and FFmpeg for video stitching.

## 3. Main Idea

The project does not create signs from nothing.

It uses existing ASL sign videos from a dataset. Each word or sign has a small video clip. When a user enters a sentence, the backend finds the required clips and combines them into one final video.

Example:

Input sentence:

What is your name?

Possible ASL gloss:

YOUR NAME WHAT

The backend searches for:

YOUR.mp4
NAME.mp4
WHAT.mp4

Then it joins these clips into one ASL translation video.

## 4. Frontend

Location:

frontend/src/App.jsx
frontend/src/components/LiveSTT.jsx

The frontend is built using React, Vite, Tailwind CSS, and Lucide icons.

What the frontend does:

- Shows a chat-like user interface.
- Lets the user type text.
- Lets the user use the microphone.
- Sends text to the backend API.
- Polls the backend until the generated video is ready.
- Displays the final ASL video.
- Displays the skeleton/pose video if available.
- Displays the ASL gloss tokens used for translation.

Important frontend behavior:

- Text input is sent to POST /jobs/generate.
- The frontend receives a job_id.
- It repeatedly calls GET /jobs/{job_id}.
- When the job status becomes DONE, it shows the video result.

## 5. Backend

Location:

backend/app/main.py

The backend is built using FastAPI.

Main backend responsibilities:

- Receive text or speech input.
- Convert speech to text using Whisper.
- Convert English text into ASL gloss tokens using an LLM through Ollama.
- Match gloss tokens with available ASLLVD video clips.
- Stitch matching video clips into one final video using FFmpeg.
- Generate skeleton video if pose/head data is available.
- Return video URLs to the frontend.

Important API endpoints:

- POST /jobs/generate
- GET /jobs/{job_id}
- POST /jobs/generate-from-audio
- WebSocket /ws/transcribe

## 6. Dataset Used

Dataset name:

ASLLVD - American Sign Language Lexicon Video Dataset

Important dataset folders:

asllvd_metadata/
asllvd_raw/
asl_videos/words/
asl_videos/poses/
asl_videos/heads/
asl_videos/public/

Important metadata file:

asllvd_metadata/asllvd_signs_2024_06_27.csv

The CSV file contains:

- Sign/gloss name.
- Source video filename.
- Start frame of the sign.
- End frame of the sign.
- Handshape information.
- Sign type.
- Class label.

Simple explanation:

The CSV tells the project where each sign is located inside a longer ASL video.

For example, if the sign BOOK appears from frame 1000 to 1050 in a raw video, the project cuts that section and saves it as BOOK.mp4.

## 7. Dataset Preparation

Raw ASLLVD videos are stored in:

asllvd_raw/

The script below reads the CSV and cuts individual sign clips:

backend/asllvd_streaming_cutter.py

It uses FFmpeg to extract sign videos and saves them in:

asl_videos/words/

Another script handles special file names:

backend/renaming_hash_clips.py

The current project contains around 2623 ASL word clips in asl_videos/words/.

## 8. Text to ASL Gloss

Location:

backend/app/llm_service.py

This file sends the English sentence to an LLM running through Ollama.

The LLM converts English into ASL gloss-style tokens.

Example:

English:

What is your name?

ASL gloss intent:

["YOUR", "NAME", "WHAT"]

Important point:

The LLM does not create the video. It only gives the ASL word order or gloss tokens.

## 9. Canonicalizer

Location:

backend/app/canonicalizer.py

The canonicalizer checks whether the gloss tokens returned by the LLM actually exist in the dataset.

Example:

If the LLM returns MOVIE, the canonicalizer checks if MOVIE.mp4 exists in asl_videos/words/.

If the exact word is not available, it may:

- Try a close matching dataset word.
- Try a base word variant.
- Fingerspell the word using letter clips.

This step is important because the system can only render signs that exist in the dataset.

## 10. Video Stitching

Location:

backend/app/stitching_service.py

This part combines many small ASL clips into one final video.

It uses FFmpeg.

Example:

YOUR.mp4 + pause + NAME.mp4 + pause + WHAT.mp4

becomes:

final_output.mp4

The backend also inserts small pause tokens between signs to make the output easier to watch.

## 11. Job System

Location:

backend/app/job_manager.py

The system uses a simple in-memory job manager.

Flow:

- A user submits text.
- Backend creates a job with a unique job_id.
- Job status starts as PENDING.
- Backend processes the job in the background.
- Status changes to RUNNING.
- When complete, status becomes DONE.
- If something fails, status becomes FAILED.

The frontend keeps checking the job status until the final video is ready.

## 12. Speech Recognition

Locations:

backend/app/whisper_service.py
backend/app/realtime_whisper_service.py

Speech recognition is done using faster-whisper.

Flow:

- Browser records microphone audio.
- Audio is sent to the backend.
- Whisper converts speech into English text.
- That text is sent into the same text-to-ASL pipeline.

So speech input and typed input eventually follow the same backend process.

## 13. Pose and Skeleton Generation

Important files:

extract_pose.py
extract_head.py
extract_all_poses.py
extract_all_head.py
render_skeleton.py
backend/app/pose_stitching_service.py

The system also creates skeleton-style ASL videos.

How it works:

- MediaPipe reads ASL video clips.
- It detects body, hand, and head landmarks.
- These landmarks are saved as NumPy .npy files.
- Pose data is stored in asl_videos/poses/.
- Head motion data is stored in asl_videos/heads/.
- render_skeleton.py draws a skeleton video from these arrays.

The frontend can show both:

- Real ASL video.
- Skeleton/pose video.

## 14. Storage and Video URLs

Location:

backend/app/minio_service.py

Generated videos can be uploaded to MinIO.

If MinIO is not configured, the project falls back to serving files locally from:

asl_videos/public/

This makes the generated videos accessible through URLs that the frontend can play.

## 15. Complete System Flow

Step-by-step flow:

1. User types or speaks in the frontend.
2. If speech is used, Whisper converts speech to text.
3. Text is sent to the FastAPI backend.
4. LLM converts English text into ASL gloss tokens.
5. Canonicalizer maps those tokens to actual ASLLVD clip names.
6. Backend finds matching .mp4 files in asl_videos/words/.
7. FFmpeg stitches those clips into one video.
8. Pose/head data is stitched and rendered into a skeleton video if available.
9. Final video URLs are returned.
10. Frontend displays the generated ASL video.

## 16. Important Technologies

Frontend:

- React
- Vite
- Tailwind CSS
- Lucide icons
- Browser microphone API
- WebSocket

Backend:

- FastAPI
- Python
- faster-whisper
- Ollama
- llama3
- spaCy
- FFmpeg
- MediaPipe
- OpenCV
- NumPy
- MinIO

Dataset:

- ASLLVD

## 17. What To Say In A Presentation

You can explain the project like this:

Our project is called GenASL. It converts English speech or typed text into American Sign Language video. The frontend is a React chat interface where users can type or speak. The backend is built using FastAPI. If the user speaks, Whisper first converts speech to text. Then an LLM converts English into ASL gloss order. After that, the backend checks the ASLLVD dataset for matching sign clips. It stitches those clips together using FFmpeg and returns the final ASL video to the frontend. We also use MediaPipe to extract pose and head landmarks, so the system can generate a skeleton visualization of the signs.

## 18. Honest Limitation

This is an MVP.

It does not generate completely new sign language animations from scratch.

It works by stitching existing signs from the ASLLVD dataset.

If a word is not present in the dataset, the system may skip it, map it to a close word, or fingerspell it using letter signs.

Best way to describe it:

GenASL is a dataset-based ASL video generation system, not a fully neural sign-language avatar.

## 19. Simple Viva Questions

Question: What problem does this project solve?

Answer: It helps convert English speech or text into an ASL video, making communication more accessible.

Question: Which dataset is used?

Answer: ASLLVD, the American Sign Language Lexicon Video Dataset.

Question: What is ASL gloss?

Answer: ASL gloss is a written representation of ASL signs, usually using uppercase words in ASL grammar order.

Question: Does the LLM generate the video?

Answer: No. The LLM only converts English into ASL gloss tokens. The videos come from the ASLLVD dataset.

Question: Why is FFmpeg used?

Answer: FFmpeg is used to cut and stitch video clips.

Question: Why is MediaPipe used?

Answer: MediaPipe is used to extract body, hand, and face/head landmarks for skeleton visualization.

Question: What is the role of the frontend?

Answer: The frontend takes user input, sends it to the backend, and displays the generated video.

Question: What is the role of the backend?

Answer: The backend handles speech recognition, ASL gloss generation, clip matching, video stitching, and result delivery.

Question: What happens if a word is missing from the dataset?

Answer: The system tries matching, variants, or fingerspelling. If nothing works, that sign may be skipped.

## 20. Short Final Summary

GenASL is a full-stack MVP that converts English speech or text into ASL video. The React frontend collects user input and displays results. The FastAPI backend uses Whisper for speech-to-text, Ollama/LLM for English-to-ASL gloss conversion, ASLLVD video clips for signs, FFmpeg for stitching, and MediaPipe/OpenCV for skeleton visualization.
