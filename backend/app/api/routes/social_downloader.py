"""Social Media Downloader — API Route

yt-dlp ile YouTube, Instagram, TikTok, Facebook, Pinterest, Twitter videolarını indirir.
Ana CREWINTEL backend'ine entegre edilmiş versiyon.
"""

import re
import uuid
import subprocess
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/social", tags=["social-downloader"])

# ── Config ────────────────────────────────────────────────────────────────────
DOWNLOAD_DIR = Path("/tmp/social-downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Task tracking
_tasks: dict[str, dict] = {}


# ── Models ────────────────────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    quality: str = "best"  # best, 1080, 720, 480, audio
    format_type: str = "video"  # video, audio


# ── Platform Detection ────────────────────────────────────────────────────────
PLATFORM_PATTERNS = {
    "youtube": [
        r"(?:youtube\.com|youtu\.be|youtube\.com/shorts)",
        r"youtube\.com/watch\?v=",
    ],
    "instagram": [
        r"instagram\.com/(p|reel|tv|stories)",
        r"instagr\.am/",
    ],
    "tiktok": [
        r"tiktok\.com/",
        r"vm\.tiktok\.com/",
        r"vt\.tiktok\.com/",
    ],
    "facebook": [
        r"facebook\.com/.+/videos",
        r"fb\.watch/",
        r"facebook\.com/reel",
    ],
    "pinterest": [
        r"pinterest\.com/.+/pin/",
        r"pin\.it/",
    ],
    "twitter": [
        r"twitter\.com/.+/status",
        r"x\.com/.+/status",
    ],
}


def detect_platform(url: str) -> Optional[str]:
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return platform
    return None


# ── yt-dlp Helpers ────────────────────────────────────────────────────────────
def run_ytdlp(args: list[str], timeout: int = 60) -> dict:
    """Run yt-dlp with given args and return parsed JSON output."""
    cmd = ["yt-dlp", "--no-warnings", "--no-check-certificates"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            raise Exception(result.stderr.strip() or "yt-dlp failed")
        return {"success": True, "output": result.stdout.strip(), "error": None}
    except subprocess.TimeoutExpired:
        raise Exception("İşlem zaman aşımına uğradı (60sn)")
    except Exception as e:
        raise Exception(str(e))


def extract_info(url: str) -> dict:
    """Extract video metadata without downloading."""
    result = run_ytdlp([
        "--dump-json",
        "--no-download",
        url,
    ], timeout=30)
    return json.loads(result["output"])


# ── API Endpoints ─────────────────────────────────────────────────────────────
@router.get("/downloader/platforms")
async def supported_platforms():
    """List supported platforms."""
    return {
        "platforms": [
            {"id": "youtube", "name": "YouTube", "icon": "▶️", "supports": ["video", "audio", "shorts"]},
            {"id": "instagram", "name": "Instagram", "icon": "📷", "supports": ["video", "reels", "stories"]},
            {"id": "tiktok", "name": "TikTok", "icon": "🎵", "supports": ["video"]},
            {"id": "facebook", "name": "Facebook", "icon": "📘", "supports": ["video", "reels"]},
            {"id": "pinterest", "name": "Pinterest", "icon": "📌", "supports": ["video", "image"]},
            {"id": "twitter", "name": "Twitter/X", "icon": "🐦", "supports": ["video"]},
        ]
    }


@router.post("/downloader/analyze")
async def analyze(req: AnalyzeRequest):
    """Analyze a URL and return platform info + video metadata."""
    platform = detect_platform(req.url)
    if not platform:
        raise HTTPException(status_code=400, detail="Desteklenmeyen platform veya geçersiz URL")

    try:
        info = extract_info(req.url)

        # Quality options
        formats = []
        if info.get("formats"):
            seen = set()
            for f in info["formats"]:
                h = f.get("height")
                if h and h not in seen and f.get("url"):
                    seen.add(h)
                    formats.append({
                        "quality": f"{h}p",
                        "height": h,
                        "ext": f.get("ext", "mp4"),
                        "filesize": f.get("filesize") or f.get("filesize_approx"),
                    })
            formats.sort(key=lambda x: x["height"], reverse=True)

        # Always add audio option
        formats.append({"quality": "audio", "height": 0, "ext": "mp3", "filesize": None})

        return {
            "success": True,
            "platform": platform,
            "title": info.get("title", "Bilinmeyen"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "upload_date": info.get("upload_date"),
            "description": (info.get("description") or "")[:500],
            "view_count": info.get("view_count"),
            "like_count": info.get("like_count"),
            "formats": formats[:10],  # Max 10 seçenek
        }

    except Exception as e:
        error_msg = str(e)
        if "Private video" in error_msg or "login" in error_msg.lower():
            raise HTTPException(status_code=403, detail="Bu içerik giriş gerektiriyor veya gizli")
        elif "DRM" in error_msg:
            raise HTTPException(status_code=403, detail="Bu medya DRM korumalı")
        elif "Unsupported" in error_msg or "not supported" in error_msg.lower():
            raise HTTPException(status_code=400, detail="Platform bu içeriğin indirilmesine izin vermiyor")
        else:
            raise HTTPException(status_code=500, detail=f"Analiz hatası: {error_msg[:200]}")


@router.post("/downloader/download")
async def download(req: DownloadRequest, background_tasks: BackgroundTasks):
    """Start a download task and return task ID."""
    platform = detect_platform(req.url)
    if not platform:
        raise HTTPException(status_code=400, detail="Desteklenmeyen platform")

    task_id = uuid.uuid4().hex[:12]
    output_dir = DOWNLOAD_DIR / task_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Task tracking
    _tasks[task_id] = {
        "status": "downloading",
        "started_at": datetime.now().isoformat(),
        "files": [],
    }

    # Build yt-dlp command
    if req.format_type == "audio":
        output_template = str(output_dir / "%(title).80s.%(ext)s")
        cmd = [
            "yt-dlp",
            "-x", "--audio-format", "mp3",
            "-o", output_template,
            "--no-warnings",
            "--no-check-certificates",
            req.url,
        ]
    else:
        format_spec = "best"
        if req.quality == "1080":
            format_spec = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
        elif req.quality == "720":
            format_spec = "bestvideo[height<=720]+bestaudio/best[height<=720]"
        elif req.quality == "480":
            format_spec = "bestvideo[height<=480]+bestaudio/best[height<=480]"

        output_template = str(output_dir / "%(title).80s.%(ext)s")
        cmd = [
            "yt-dlp",
            "-f", format_spec,
            "--merge-output-format", "mp4",
            "-o", output_template,
            "--no-warnings",
            "--no-check-certificates",
            req.url,
        ]

    # Run in background
    def run_download():
        try:
            subprocess.run(cmd, capture_output=True, timeout=300)
            # Mark as completed
            files = list(output_dir.glob("*"))
            _tasks[task_id]["status"] = "completed"
            _tasks[task_id]["files"] = [
                {"name": f.name, "size": f.stat().st_size}
                for f in files if f.is_file()
            ]
        except Exception:
            _tasks[task_id]["status"] = "failed"

    background_tasks.add_task(run_download)

    return {
        "task_id": task_id,
        "status": "started",
        "message": "İndirme başlatıldı",
    }


@router.get("/downloader/{task_id}/status")
async def download_status(task_id: str):
    """Check download status."""
    # First check in-memory tracker
    if task_id in _tasks:
        task = _tasks[task_id]
        if task["status"] == "completed":
            return {
                "status": "completed",
                "files": task["files"],
            }
        elif task["status"] == "failed":
            return {"status": "failed", "error": "İndirme başarısız oldu"}

    # Fallback: check filesystem
    output_dir = DOWNLOAD_DIR / task_id
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Görev bulunamadı")

    files = list(output_dir.glob("*"))
    file_list = [
        {"name": f.name, "size": f.stat().st_size, "path": str(f)}
        for f in files if f.is_file()
    ]

    if file_list:
        return {"status": "completed", "files": file_list}
    else:
        return {"status": "downloading"}


@router.get("/downloader/{task_id}/file")
async def download_file(task_id: str):
    """Download the completed file."""
    output_dir = DOWNLOAD_DIR / task_id
    files = list(output_dir.glob("*"))
    if not files:
        raise HTTPException(status_code=404, detail="Dosya bulunamadı")

    file_path = files[0]
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream",
    )
