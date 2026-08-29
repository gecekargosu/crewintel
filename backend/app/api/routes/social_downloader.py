"""Social Media Downloader — API Route (v2)

yt-dlp ile YouTube, Instagram, TikTok, Facebook, Pinterest, Twitter videolarını indirir.
- Format fallback zinciri (best→1080→720→480→bestvideo+bestaudio)
- Eş zamanlı indirme desteği
- İndirme geçmişi
- YouTube için JS runtime kurulumu dahil
"""

import os
import re
import uuid
import subprocess
import json
from pathlib import Path
from typing import Optional
from datetime import datetime


from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from app.api.deps import get_current_user
from app.models.user import User
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/social", tags=["social-downloader"])

# ── Config ────────────────────────────────────────────────────────────────────
# Persistent paths (survive Docker restarts)
DATA_DIR = Path("/app/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

DOWNLOAD_DIR = DATA_DIR / "social-downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

COOKIE_DIR = DATA_DIR / "social-cookies"
COOKIE_DIR.mkdir(parents=True, exist_ok=True)
# Rate limiting (per-user)
import time
from collections import defaultdict
_user_requests: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 20  # max requests per window


# Cookie encryption
import hashlib

def _get_encrypt_key():
    """Get encryption key from settings."""
    from app.core.config import get_settings
    settings = get_settings()
    return hashlib.sha256(settings.jwt_secret_key.encode()).digest()

def _encrypt_cookie(content: str) -> bytes:
    """Simple XOR encryption for cookie files."""
    key = _get_encrypt_key()
    data = content.encode('utf-8')
    encrypted = bytearray()
    for i, byte in enumerate(data):
        encrypted.append(byte ^ key[i % len(key)])
    return bytes(encrypted)

def _decrypt_cookie(encrypted: bytes) -> str:
    """Simple XOR decryption for cookie files."""
    key = _get_encrypt_key()
    decrypted = bytearray()
    for i, byte in enumerate(encrypted):
        decrypted.append(byte ^ key[i % len(key)])
    return decrypted.decode('utf-8')

def _check_rate_limit(user_id: str):
    """Check if user has exceeded rate limit."""
    now = time.time()
    # Clean old requests
    _user_requests[user_id] = [t for t in _user_requests[user_id] if now - t < RATE_LIMIT_WINDOW]
    if len(_user_requests[user_id]) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail=f"Cok fazla istek. {RATE_LIMIT_WINDOW} saniye icinde en fazla {RATE_LIMIT_MAX} istek yapabilirsiniz."
        )
    _user_requests[user_id].append(now)


# Task history file (persist across restarts)
TASKS_FILE = DATA_DIR / "tasks.json"

# Task tracking (concurrent-safe)
_tasks: dict[str, dict] = {}
_download_counter = 0


def _load_tasks():
    """Load task history from JSON file."""
    global _tasks, _download_counter
    if TASKS_FILE.exists():
        try:
            saved = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
            _tasks = saved.get("tasks", {})
            _download_counter = saved.get("counter", 0)
            # Only load completed/failed tasks, not stale 'downloading' ones
            now = datetime.now().isoformat()
            for tid, task in list(_tasks.items()):
                if task.get("status") == "downloading":
                    # Mark stale downloading tasks as failed
                    task["status"] = "failed"
                    task["error"] = "Sunucu yeniden baslatildi"
                    task["completed_at"] = now
        except Exception:
            pass


def _save_tasks():
    """Save task history to JSON file."""
    try:
        TASKS_FILE.write_text(
            json.dumps({"tasks": _tasks, "counter": _download_counter}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception:
        pass


# Load on startup
_load_tasks()


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
        r"(?:youtube\.com|youtu\.be)",
    ],
    "instagram": [
        r"instagram\.com/(p|reel|tv|stories|videos)",
        r"instagr\.am/",
    ],
    "tiktok": [
        r"tiktok\.com/",
        r"vm\.tiktok\.com/",
        r"vt\.tiktok\.com/",
    ],
    "facebook": [
        r"facebook\.com/.+/videos",
        r"facebook\.com/watch",
        r"facebook\.com/reel",
        r"fb\.watch/",
        r"facebook\.com/.+/posts/",
    ],
    "pinterest": [
        r"pinterest\.com/",
        r"pin\.it/",
    ],
    "twitter": [
        r"(?:twitter|x)\.com/.+/status",
    ],
    "linkedin": [
        r"linkedin\.com/posts/",
        r"linkedin\.com/feed/update/",
        r"linkedin\.com/video/",
        r"linkedin\.com/watch/",
        r"linkedin\.com/reel/",
        r"linkedin\.com/learning/",
        r"linkedin\.com/embed/",
        r"linkedin\.com/.+/videos/",
        r"linkedin\.com/.+/live/",
    ],
}

PLATFORM_NAMES = {
    "youtube": "YouTube",
    "instagram": "Instagram",
    "tiktok": "TikTok",
    "facebook": "Facebook",
    "pinterest": "Pinterest",
    "twitter": "Twitter/X",
    "linkedin": "LinkedIn",
}


def detect_platform(url: str) -> Optional[str]:
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return platform
    return None


# ── yt-dlp Helpers ────────────────────────────────────────────────────────────
# Browser-like User-Agent — Instagram checks this
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

def get_cookie_args(platform: str) -> list[str]:
    """Get cookie args for a platform if cookies exist. Decrypts encrypted cookie files."""
    if not platform:
        return []
    cookie_file = COOKIE_DIR / f"{platform}.txt"
    if not cookie_file.exists():
        return []
    # Decrypt cookie and write to temp file for yt-dlp
    import tempfile
    try:
        raw = cookie_file.read_bytes()
        decrypted = _decrypt_cookie(raw)
        tmp = tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', prefix=f'{platform}_cookies_',
            delete=False, encoding='utf-8'
        )
        tmp.write(decrypted)
        tmp.close()
        return ["--cookies", tmp.name]
    except Exception:
        # Fallback: try reading as plain text (unencrypted)
        return ["--cookies", str(cookie_file)]


def run_ytdlp(args: list[str], timeout: int = 60) -> dict:
    """Run yt-dlp with given args and return parsed JSON output."""
    cmd = ["yt-dlp", "--no-warnings", "--user-agent", BROWSER_UA, "--js-runtimes", "node"] + args
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


def extract_info(url: str, platform: str = "") -> dict:
    """Extract video metadata without downloading. Uses cookies if available."""
    cookie_args = get_cookie_args(platform)
    result = run_ytdlp([
        "--dump-json",
        "--no-download",
    ] + cookie_args + [url], timeout=45)
    return json.loads(result["output"])


def build_format_specs(quality: str, format_type: str, platform: str = "") -> list[list[str]]:
    """Build ordered list of yt-dlp argument sets to try (most specific → least).
    Each item is a complete argument list fragment (e.g. ['-f', 'bestvideo+bestaudio']).
    """
    cookie_args = get_cookie_args(platform)

    if format_type == "audio":
        return [
            ["-x", "--audio-format", "mp3"] + cookie_args,
        ]

    # Progressive fallback: specific → generic → no format spec at all
    all_specs = []
    
    # Only add height-specific spec if quality is a number
    if quality.isdigit():
        h = int(quality)
        all_specs.append(["-f", f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={h}]+bestaudio/best[height<={h}]", "--merge-output-format", "mp4"])
    
    # Universal fallbacks (always included)
    all_specs.extend([
        # 2nd try: just bestvideo+bestaudio merge (any codec)
        ["-f", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"] + cookie_args,
        # 3rd try: just "best" (single combined stream)
        ["-f", "best", "--merge-output-format", "mp4"] + cookie_args,
        # 4th try: no format specification at all — let yt-dlp decide
        cookie_args,
    ])

    return all_specs


# ── API Endpoints ─────────────────────────────────────────────────────────────
@router.get("/downloader/platforms")
async def supported_platforms(current_user: User = Depends(get_current_user)):
    """List supported platforms."""
    return {
        "platforms": [
            {"id": "youtube", "name": "YouTube", "icon": "▶️", "supports": ["video", "audio", "shorts"]},
            {"id": "instagram", "name": "Instagram", "icon": "📷", "supports": ["video", "reels", "stories"]},
            {"id": "tiktok", "name": "TikTok", "icon": "🎵", "supports": ["video"]},
            {"id": "facebook", "name": "Facebook", "icon": "📘", "supports": ["video", "reels"]},
            {"id": "pinterest", "name": "Pinterest", "icon": "📌", "supports": ["video", "image"]},
            {"id": "twitter", "name": "Twitter/X", "icon": "🐦", "supports": ["video"]},
            {"id": "linkedin", "name": "LinkedIn", "icon": "💼", "supports": ["video", "posts"]},
        ]
    }


@router.get("/downloader/history")
async def download_history(current_user: User = Depends(get_current_user)):
    """Get all downloaded files for current user only."""
    all_files = []
    for task_id, task in sorted(_tasks.items(), key=lambda x: x[1].get("started_at", ""), reverse=True):
        if task.get("user_id") != current_user.id:
            continue
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
async def active_downloads(current_user: User = Depends(get_current_user)):
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
async def analyze(req: AnalyzeRequest, current_user: User = Depends(get_current_user)):
    _check_rate_limit(str(current_user.id))
    """Analyze a URL and return platform info + video metadata."""
    platform = detect_platform(req.url)
    if not platform:
        raise HTTPException(status_code=400, detail="Desteklenmeyen platform veya gecersiz URL")

    try:
        info = extract_info(req.url, platform=platform)

        # Quality options — only show downloadable formats (HTTPS, not m3u8/mhtml)
        formats = []
        if info.get("formats"):
            seen = set()
            for f in info["formats"]:
                h = f.get("height")
                ext = f.get("ext", "mp4")
                proto = f.get("protocol", "")
                # Skip: storyboards, mhtml, m3u8-only (HLS), audio-only
                if ext in ("mhtml", "json"):
                    continue
                if proto == "m3u8" or proto == "m3u8_native":
                    continue
                if not h or h == 0:
                    continue
                if h not in seen:
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

        # If no downloadable video formats found, add best available
        if not any(f["height"] > 0 for f in formats):
            formats.insert(0, {"quality": "En iyi kalite (otomatik)", "height": -1, "ext": "mp4", "filesize": None})

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



# ── Cookie Management ────────────────────────────────────────────────────────
@router.get("/downloader/cookies")
async def list_cookies(current_user: User = Depends(get_current_user)):
    """List saved cookies for all platforms (metadata only, no content)."""
    cookies = {}
    for platform in ["youtube", "instagram", "tiktok", "facebook", "pinterest", "twitter", "linkedin"]:
        cookie_file = COOKIE_DIR / f"{platform}.txt"
        if cookie_file.exists():
            stat = cookie_file.stat()
            cookies[platform] = {
                "exists": True,
                "size": stat.st_size,
                "last_modified": stat.st_mtime,
                "configured": True,
            }
        else:
            cookies[platform] = {"exists": False, "configured": False}
    return {"cookies": cookies}


class CookieSaveRequest(BaseModel):
    platform: str
    cookies: str  # Netscape cookie format


@router.post("/downloader/cookies")
async def save_cookies(req: CookieSaveRequest, current_user: User = Depends(get_current_user)):
    """Save cookies for a platform (Netscape format)."""
    valid_platforms = ["youtube", "instagram", "tiktok", "facebook", "pinterest", "twitter", "linkedin"]
    if req.platform not in valid_platforms:
        raise HTTPException(status_code=400, detail=f"Gecersiz platform: {req.platform}")


    cookie_file = COOKIE_DIR / f"{req.platform}.txt"
    # Ensure Netscape header
    cookie_content = req.cookies
    if not cookie_content.strip().startswith("# Netscape"):
        header = "# Netscape HTTP Cookie File" + chr(10) + "# http://curl.haxx.se/rfc/cookie_spec.html" + chr(10) + "# This is a generated file!  Do not edit." + chr(10) + chr(10)
        cookie_content = header + cookie_content
    # Encrypt and save cookie file
    encrypted = _encrypt_cookie(cookie_content)
    cookie_file.write_bytes(encrypted)
    
    # Secure cookie file permissions (read/write owner only)
    try:
        os.chmod(cookie_file, 0o600)
    except OSError:
        pass  # Windows may not support chmod

    return {
        "status": "saved",
        "platform": req.platform,
        "size": len(req.cookies),
        "lines": req.cookies.count(chr(10)),
    }


@router.delete("/downloader/cookies/{platform}")
async def delete_cookies(platform: str, current_user: User = Depends(get_current_user)):
    """Delete cookies for a platform."""
    cookie_file = COOKIE_DIR / f"{platform}.txt"
    if cookie_file.exists():
        cookie_file.unlink()
    return {"status": "deleted", "platform": platform}


@router.post("/downloader/download")
async def download(req: DownloadRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    _check_rate_limit(str(current_user.id))
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
        "user_id": current_user.id,
    }
    _save_tasks()

    # Build format specs to try in order
    output_template = str(output_dir / "%(title).80s.%(ext)s")
    format_specs = build_format_specs(req.quality, req.format_type, platform)

    # Run in background (concurrent-safe)
    def run_download():
        print(f"Download started: task_id={task_id}, url={req.url}, quality={req.quality}")
        last_error = "Bilinmeyen hata"
        result = None

        # Try each format spec in order until one succeeds
        for i, spec in enumerate(format_specs):
            print(f"Task {task_id}: Trying format spec {i+1}/{len(format_specs)}: {spec}")
            cmd = ["yt-dlp"] + spec + [
                "-o", output_template,
                "--no-check-certificates",
                "--no-warnings",
                "--user-agent", BROWSER_UA,
                "--js-runtimes", "node",
                req.url,
            ]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                if result.returncode == 0:
                    # Check if files exist
                    files = [f for f in output_dir.glob("*") if f.is_file()]
                    if files:
                        print(f"Task {task_id}: Download completed with spec {i+1}, file={files[0].name}")
                        _tasks[task_id]["status"] = "completed"
                        _tasks[task_id]["completed_at"] = datetime.now().isoformat()
                        _tasks[task_id]["files"] = [
                            {"name": f.name, "size": f.stat().st_size}
                            for f in files
                        ]
                        _save_tasks()
                        return
                    else:
                        print(f"Task {task_id}: yt-dlp returned 0 but no files in {output_dir}")
                        last_error = "Dosya indirilemedi"
                else:
                    print(f"Task {task_id}: Format spec {i+1} failed: {(result.stderr or '').strip()[:200]}")
                    last_error = (result.stderr or result.stdout or "Format uyumsuz").strip()[:200]
            except subprocess.TimeoutExpired:
                last_error = "Zaman asimi (10 dk)"
                break
            except Exception as e:
                last_error = str(e)[:200]

        # All formats failed
        print(f"Task {task_id}: All format specs failed. Last error: {last_error[:200]}")
        # Translate common errors to Turkish
        error_msg = last_error
        if "format" in error_msg.lower() or "requested" in error_msg.lower():
            error_msg = "Secilen kalite bu video icin uygun degil — daha dusuk bir kalite secin"
        elif "login" in error_msg.lower() or "private" in error_msg.lower():
            error_msg = "Bu video ozel/gizli — giris yapmaniz gerekiyor"
        elif "drm" in error_msg.lower():
            error_msg = "Bu video DRM ile korumali — indirilemez"
        elif "unavailable" in error_msg.lower() or "not available" in error_msg.lower():
            error_msg = "Video su an erisilebilir degil"
        elif "geo" in error_msg.lower() or "blocked" in error_msg.lower():
            error_msg = "Video bolgenizden erisime kapali"
        else:
            error_msg = f"Indirme basarisiz: {error_msg[:150]}"

        _tasks[task_id]["status"] = "failed"
        _tasks[task_id]["error"] = error_msg
        _save_tasks()
        print(f"Task {task_id}: FAILED — {error_msg[:100]}")

    background_tasks.add_task(run_download)

    return {
        "task_id": task_id,
        "status": "started",
        "message": "Indirme baslatildi",
        "queue_position": _download_counter,
    }


@router.get("/downloader/{task_id}/status")
async def download_status(task_id: str, current_user: User = Depends(get_current_user)):
    """Check download status."""
    # In-memory tracker
    if task_id in _tasks:
        task = _tasks[task_id]
        if task.get("user_id") != current_user.id:
            raise HTTPException(status_code=403, detail="Bu task size ait degil")
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
            # Auto-stale: if downloading for > 5 minutes, mark as failed
            from datetime import datetime, timedelta
            started = task.get("started_at", "")
            if started:
                try:
                    started_dt = datetime.fromisoformat(started)
                    if datetime.now() - started_dt > timedelta(minutes=5):
                        task["status"] = "failed"
                        task["error"] = "Indirme zaman asimina ugradi (sunucu tarafinda)"
                        return {
                            "status": "failed",
                            "error": task["error"],
                        }
                except Exception:
                    pass
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
async def download_file(task_id: str, current_user: User = Depends(get_current_user)):
    """Download the completed file."""
    if task_id in _tasks and _tasks[task_id].get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Bu task size ait degil")
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

@router.delete("/downloader/{task_id}")
async def delete_download(task_id: str, current_user: User = Depends(get_current_user)):
    """Delete a downloaded file and remove from history."""
    if task_id in _tasks and _tasks[task_id].get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Bu task size ait degil")
    # Remove from tasks
    if task_id in _tasks:
        del _tasks[task_id]

    # Remove files from disk
    output_dir = DOWNLOAD_DIR / task_id
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir, ignore_errors=True)

    return {"status": "deleted", "task_id": task_id}
