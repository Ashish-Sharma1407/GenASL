import os
import shutil
from pathlib import Path
from datetime import timedelta
from minio import Minio

# =========================
# CONFIG
# =========================

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
USE_MINIO = os.getenv("USE_MINIO", "true").lower() == "true"

BUCKET = os.getenv("MINIO_BUCKET", "genasl-videos")
LOCAL_BASE_URL = os.getenv("LOCAL_BASE_URL", "http://127.0.0.1:8000")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_PUBLIC_DIR = PROJECT_ROOT / "asl_videos" / "public"


# =========================
# CLIENT
# =========================

client = None
if USE_MINIO and MINIO_ENDPOINT:
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )


# =========================
# BUCKET HELPERS
# =========================

def ensure_bucket():
    """
    Create bucket if it does not exist.
    Safe to call multiple times.
    """
    if client is None:
        return

    found = client.bucket_exists(BUCKET)
    if not found:
        client.make_bucket(BUCKET)


def _local_url_for(object_name: str) -> str:
    object_name = object_name.strip("/").replace("\\", "/")
    dst = LOCAL_PUBLIC_DIR / object_name
    dst.parent.mkdir(parents=True, exist_ok=True)
    return f"{LOCAL_BASE_URL}/static/{object_name}"


# =========================
# UPLOAD + URL
# =========================

def upload_and_get_url(
    local_path: str,
    object_name: str,
    expiry_minutes: int = 10
) -> str:
    """
    Upload a file and return a presigned GET URL.
    """

    # Fallback mode: copy outputs into a static folder served by FastAPI.
    if client is None:
        public_url = _local_url_for(object_name)
        dst = LOCAL_PUBLIC_DIR / object_name.strip("/").replace("\\", "/")
        shutil.copy2(local_path, dst)
        return public_url

    ensure_bucket()

    client.fput_object(
        bucket_name=BUCKET,
        object_name=object_name,
        file_path=local_path,
        content_type="video/mp4"
    )

    url = client.presigned_get_object(
        bucket_name=BUCKET,
        object_name=object_name,
        expires=timedelta(minutes=expiry_minutes)
    )

    return url
