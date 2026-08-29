"""Social Media Downloader — API Route (v2)

yt-dlp ile YouTube, Instagram, TikTok, Facebook, Pinterest, Twitter videolarını indirir.
- Format fallback zinciri (best→1080→720→480→bestvideo+bestaudio)
- Eş zamanlı indirme desteği
- İndirme geçmişi
- YouTube için JS runtime kurulumu dahil
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

# Task tracking (concurrent-safe)
_tasks: dict[str, dict] = {}
_download_counter = 0


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

PLATFORM_NAMES = {
    "youtube": "YouTube",
    "instagram": "Instagram",
    "tiktok": "TikTok",
    "facebook": "Facebook",
    "pinterest": "Pinterest",
    "twitter": "Twitter/X",
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
    cmd = ["yt-dlp", "--no-check-certificates", "--no-warnings"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            raise Exception(result.stderr.strip() or result.stdout.strip() or "yt-dlp failed")
        return {"success": True, "output": result.stdout.strip(), "error": None}
    except subprocess.TimeoutExpired:
        raise Exception("Islem zaman asimina ugradi (60sn)")
    except Exception as e:
        raise Exception(str(e))


def extract_info(url: str) -> dict:
    """Extract video metadata without downloading."""
    result = run_ytdlp([
        "--dump-json",
        "--no-download",
        url,
    ], timeout=45)
    return json.loads(result["output"])


def build_format_args(quality: str, format_type: str) -> list[str]:
    """Build yt-dlp format arguments with robust fallback chain."""
    if format_type == "audio":
        return ["-x", "--audio-format", "mp3"]

    # Format fallback chain — tries each until one works
    # YouTube serves video+audio separately, so we need bestvideo+bestaudio
    fallbacks = {
        "best": [
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        ],
        "1080": [
            "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        ],
        "720": [
            "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]",
        ],
        "480": [
            "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]",
        ],
    }

    specs = fallbacks.get(quality, fallbacks["best"])
    format_spec = specs[0]

    return ["-f", format_spec, "--merge-output-format", "mp4"]


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


@router.get("/downloader/history")
async def download_history():
    """Get all downloaded files across all tasks."""
    all_files = []
    for task_id, task in sorted(_tasks.items(), key=lambda x: x[1].get("started_at", ""), reverse=True):
        if task["status"] == "completed" and task.get("files"):
            for f in task["files"]:
                all_files.append({
                    "task_id": task_id,
                    "name": f.get("name", ""),
                    "size": f.get("size", 0),
                    "platform": task.get("platform", "unknown"),
                    "title": task.get("title", ""),
                    "thumbnail": task.get("thumbnail", ""),
                    "downloaded_at": task.get("completed_at", task.get("started_at", "")),
                })
    return {"files": all_files, "total": len(all_files)}


@router.get("/downloader/active")
async def active_downloads():
    """Get all currently downloading tasks."""
    active = []
    for task_id, task in _tasks.items():
        if task["status"] == "downloading":
            active.append({
                "task_id": task_id,
                "url": task.get("url", ""),
                "title": task.get("title", ""),
                "platform": task.get("platform", "unknown"),
                "thumbnail": task.get("thumbnail", ""),
                "started_at": task.get("started_at", ""),
            })
    return {"tasks": active, "count": len(active)}


@router.post("/downloader/analyze")
async def analyze(req: AnalyzeRequest):
    """Analyze a URL and return platform info + video metadata."""
    platform = detect_platform(req.url)
    if not platform:
        raise HTTPException(status_code=400, detail="Desteklenmeyen platform veya gecersiz URL")

    try:
        info = extract_info(req.url)

        # Quality options — use actual available formats
        formats = []
        if info.get("formats"):
            seen = set()
            for f in info["formats"]:
                h = f.get("height")
                ext = f.get("ext", "mp4")
                # Skip storyboards, mhtml, and non-video formats
                if ext in ("mhtml", "json"):
                    continue
                if h and h not in seen:
                    seen.add(h)
                    formats.append({
                        "quality": f"{h}p",
                        "height": h,
                        "ext": ext,
                        "filesize": f.get("filesize") or f.get("filesize_approx"),
                    })
            formats.sort(key=lambda x: x["height"], reverse=True)

        # Always add audio option
        formats.append({"quality": "Ses (MP3)", "height": 0, "ext": "mp3", "filesize": None})

        return {
            "success": True,
            "platform": platform,
            "platform_name": PLATFORM_NAMES.get(platform, platform),
            "title": info.get("title", "Bilinmeyen"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "upload_date": info.get("upload_date"),
            "description": (info.get("description") or "")[:500],
            "view_count": info.get("view_count"),
            "like_count": info.get("like_count"),
            "formats": formats[:10],
        }

    except Exception as e:
        error_msg = str(e)
        if "Private video" in error_msg or "login" in error_msg.lower():
            raise HTTPException(status_code=403, detail="Bu icerik giris gerektiriyor veya gizli")
        elif "DRM" in error_msg:
            raise HTTPException(status_code=403, detail="Bu medya DRM korumali")
        elif "Unsupported" in error_msg or "not supported" in error_msg.lower():
            raise HTTPException(status_code=400, detail="Platform bu icerigin indirilmesine izin vermiyor")
        else:
            raise HTTPException(status_code=500, detail=f"Analiz hatasi: {error_msg[:300]}")


@router.post("/downloader/download")
async def download(req: DownloadRequest, background_tasks: BackgroundTasks):
    """Start a download task. Supports concurrent downloads."""
    global _download_counter
    platform = detect_platform(req.url)
    if not platform:
        raise HTTPException(status_code=400, detail="Desteklenmeyen platform")

    task_id = uuid.uuid4().hex[:12]
    output_dir = DOWNLOAD_DIR / task_id
    output_dir.mkdir(parents=True, exist_ok=True)

    _download_counter += 1

    # Task tracking
    _tasks[task_id] = {
        "status": "downloading",
        "started_at": datetime.now().isoformat(),
        "files": [],
        "url": req.url,
        "platform": platform,
        "title": "",
        "thumbnail": "",
        "progress": 0,
    }

    # Build yt-dlp command with robust format fallback
    format_args = build_format_args(req.quality, req.format_type)
    output_template = str(output_dir / "%(title).80s.%(ext)s")

    cmd = ["yt-dlp"] + format_args + [
        "-o", output_template,
        "--no-check-certificates",
        "--no-warnings",
        "--newline",  # Progress on new lines
        req.url,
    ]

    # Run in background (concurrent-safe)
    def run_download():
        try:
            # First try with the format spec
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            # If failed, try with simpler fallback
            if result.returncode != 0:
                error_text = (result.stderr or "").lower()
                # Retry with "best" fallback
                if "format" in error_text or "requested" in error_text:
                    fallback_cmd = [
                        "yt-dlp",
                        "-f", "best",
                        "-o", output_template,
                        "--no-check-certificates",
                        "--no-warnings",
                        req.url,
                    ]
                    result = subprocess.run(fallback_cmd, capture_output=True, text=True, timeout=600)

                # If still failed, try without format spec at all
                if result.returncode != 0:
                    fallback_cmd2 = [
                        "yt-dlp",
                        "-o", output_template,
                        "--no-check-certificates",
                        "--no-warnings",
                        req.url,
                    ]
                    result = subprocess.run(fallback_cmd2, capture_output=True, text=True, timeout=600)

            if result.returncode != 0:
                error_msg = (result.stderr or result.stdout or "Bilinmeyen hata").strip()
                _tasks[task_id]["status"] = "failed"
                _tasks[task_id]["error"] = error_msg[:500]
                return

            # Check if files exist
            files = [f for f in output_dir.glob("*") if f.is_file()]
            if not files:
                _tasks[task_id]["status"] = "failed"
                _tasks[task_id]["error"] = "Dosya indirilemedi — platform giris gerektirebilir"
                return

            _tasks[task_id]["status"] = "completed"
            _tasks[task_id]["completed_at"] = datetime.now().isoformat()
            _tasks[task_id]["files"] = [
                {"name": f.name, "size": f.stat().st_size}
                for f in files
            ]

        except subprocess.TimeoutExpired:
            _tasks[task_id]["status"] = "failed"
            _tasks[task_id]["error"] = "Indirme zaman asimina ugradi (10 dakika)"
        except Exception as e:
            _tasks[task_id]["status"] = "failed"
            _tasks[task_id]["error"] = str(e)[:500]

    background_tasks.add_task(run_download)

    return {
        "task_id": task_id,
        "status": "started",
        "message": "Indirme baslatildi",
        "queue_position": _download_counter,
    }


@router.get("/downloader/{task_id}/status")
async def download_status(task_id: str):
    """Check download status."""
    # In-memory tracker
    if task_id in _tasks:
        task = _tasks[task_id]
        if task["status"] == "completed":
            return {
                "status": "completed",
                "files": task["files"],
                "title": task.get("title", ""),
                "platform": task.get("platform", ""),
            }
        elif task["status"] == "failed":
            return {
                "status": "failed",
                "error": task.get("error", "Indirme basarisiz oldu"),
            }
        else:
            return {
                "status": "downloading",
                "progress": task.get("progress", 0),
            }

    # Fallback: check filesystem
    output_dir = DOWNLOAD_DIR / task_id
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Gorev bulunamadi")

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
        raise HTTPException(status_code=404, detail="Dosya bulunamadi")

    file_path = files[0]
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream",
    )
