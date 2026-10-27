import os
import re
import time
import math
import shutil
import urllib.parse
import threading
import collections
from typing import Callable, Optional, Dict, List
import requests

try:
    import yt_dlp
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False

CHUNK_SIZE = 64 * 1024  # 64 KB read buffer
MERGE_BUFFER = 1024 * 1024  # 1 MB merge buffer
MIN_SPLIT_SIZE = 1024 * 1024  # 1 MB threshold for Dynamic Chunk Splitting

VIDEO_DOMAINS = [
    "youtube.com", "youtu.be", "vimeo.com", "dailymotion.com",
    "tiktok.com", "facebook.com", "fb.watch", "instagram.com",
    "twitter.com", "x.com", "twitch.tv", "bilibili.com"
]

def is_video_streaming_url(url: str) -> bool:
    if not url:
        return False
    try:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        return any(d in host for d in VIDEO_DOMAINS)
    except Exception:
        return False

def clean_filename(title: str, ext: str = "") -> str:
    if not title:
        return "video" + (f".{ext.lstrip('.')}" if ext else "")
    # Remove illegal windows filesystem characters: \ / * ? : " < > |
    cleaned = re.sub(r'[\\/*?:"<>|]', "", title)
    # Remove non-printable characters and surrogate/emojis above 0xFFFF that crash Tkinter
    cleaned = "".join(c for c in cleaned if c.isprintable() and ord(c) < 0x10000)
    # Strip leading/trailing spaces and dots
    cleaned = re.sub(r'\s+', " ", cleaned).strip(". ")
    if not cleaned:
        cleaned = "video"
    if ext:
        ext_clean = "." + ext.lstrip(".")
        if not cleaned.lower().endswith(ext_clean.lower()):
            cleaned += ext_clean
    return cleaned

CATEGORY_EXTENSIONS = {
    "Compressed": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".tgz"],
    "Documents": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".csv", ".epub"],
    "Video": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
    "Music": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"],
    "Programs": [".exe", ".msi", ".apk", ".bat", ".cmd", ".ps1"]
}

def detect_category(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    for cat, exts in CATEGORY_EXTENSIONS.items():
        if ext in exts:
            return cat
    return "Other"

def format_size(bytes_size: int) -> str:
    if bytes_size <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(bytes_size, 1024)))
    i = min(i, len(units) - 1)
    p = math.pow(1024, i)
    s = round(bytes_size / p, 2)
    return f"{s} {units[i]}"

def format_time(seconds: float) -> str:
    if seconds <= 0 or math.isinf(seconds) or math.isnan(seconds):
        return "--:--"
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m:02d}m {s:02d}s"

class SegmentInfo:
    def __init__(self, index: int, start: int, end: int, downloaded: int = 0):
        self.index = index
        self.start = start
        self.end = end
        self.downloaded = downloaded
        self.is_active = False
        self._is_finished = False

    @property
    def total(self) -> int:
        return (self.end - self.start + 1) if self.end >= self.start else 0

    @property
    def is_finished(self) -> bool:
        return self._is_finished or (self.total > 0 and self.downloaded >= self.total)

    @is_finished.setter
    def is_finished(self, value: bool):
        self._is_finished = bool(value)

class DownloadTask:
    def __init__(
        self,
        task_id: str,
        url: str,
        save_dir: str,
        filename: str = "",
        connections: int = 32,
        task_type: str = "file",
        video_quality: str = "best",
        cookies: str = "",
        referer: str = "",
        user_agent: str = ""
    ):
        self.task_id = task_id
        self.url = url
        self.save_dir = save_dir
        self.filename = filename
        self.connections = connections
        self.task_type = "video" if (task_type == "video" or is_video_streaming_url(url)) else "file"
        self.video_quality = video_quality
        self.cookies = cookies
        self.referer = referer
        self.user_agent = user_agent
        self.thumbnail_url = ""
        
        self.total_size = 0
        self.downloaded_size = 0
        self.supports_ranges = False
        self.status = "Queued"  # Queued, Downloading, Paused, Completed, Error
        self.error_message = ""
        self.category = "Video" if self.task_type == "video" else "Other"
        self.speed = 0.0  # bytes per second
        self.eta = 0.0    # seconds
        self.speed_limit = 0  # 0 = unlimited, otherwise bytes/sec
        self.speed_history = collections.deque(maxlen=60)
        
        self.segments: List[SegmentInfo] = []
        self.segment_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.worker_threads: List[threading.Thread] = []
        
        # Callbacks
        self.on_progress: Optional[Callable[['DownloadTask'], None]] = None
        self.on_status_change: Optional[Callable[['DownloadTask'], None]] = None
        self.on_complete: Optional[Callable[['DownloadTask'], None]] = None

    @property
    def target_file_path(self) -> str:
        return os.path.join(self.save_dir, self.filename)

    @property
    def progress_percentage(self) -> float:
        if self.total_size <= 0:
            return 0.0
        return min(100.0, (self.downloaded_size / self.total_size) * 100.0)

    def get_part_file_path(self, segment_index: int) -> str:
        return os.path.join(self.save_dir, f".{self.filename}.part_{segment_index}")

    def inspect_url(self) -> bool:
        """Inspect headers or video metadata to determine filename, size, and range support."""
        if self.task_type == "video" or is_video_streaming_url(self.url):
            self.task_type = "video"
            if HAS_YTDLP:
                try:
                    ydl_opts = {
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': True,
                        'noplaylist': True,
                    }
                    http_headers = {}
                    if self.user_agent:
                        http_headers['User-Agent'] = self.user_agent
                    if self.referer:
                        http_headers['Referer'] = self.referer
                    if self.cookies:
                        http_headers['Cookie'] = self.cookies
                    if http_headers:
                        ydl_opts['http_headers'] = http_headers

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(self.url, download=False)
                        if info:
                            raw_title = info.get('title') or "video"
                            ext = "mp3" if self.video_quality == "audio" else "mp4"
                            self.filename = clean_filename(raw_title, ext)
                            self.category = "Music" if self.video_quality == "audio" else "Video"
                            self.supports_ranges = True
                            self.thumbnail_url = info.get('thumbnail') or ""
                            return True
                except Exception as e:
                    print(f"yt-dlp inspect error: {e}")
            
        headers = {
            "User-Agent": self.user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        if self.referer:
            headers["Referer"] = self.referer
        if self.cookies:
            headers["Cookie"] = self.cookies
        try:
            # First try HEAD
            response = requests.head(self.url, headers=headers, allow_redirects=True, timeout=15)
            
            # If server forbids HEAD or returns error, try GET with range: 0-0
            if response.status_code >= 400 or response.status_code == 405:
                range_headers = headers.copy()
                range_headers["Range"] = "bytes=0-0"
                response = requests.get(self.url, headers=range_headers, stream=True, timeout=15)

            # Determine filename
            if not self.filename:
                cd = response.headers.get("Content-Disposition", "")
                if cd and "filename=" in cd:
                    fname_match = re.findall(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';]+)["\']?', cd, flags=re.IGNORECASE)
                    if fname_match:
                        self.filename = urllib.parse.unquote(fname_match[0].strip())
                
                if not self.filename:
                    parsed_path = urllib.parse.urlparse(response.url).path
                    base = os.path.basename(parsed_path)
                    self.filename = urllib.parse.unquote(base) if base else "downloaded_file"

            # Clean filename from illegal characters in Windows
            self.filename = clean_filename(self.filename)
            self.category = detect_category(self.filename)

            # Determine size and ranges support
            content_length = response.headers.get("Content-Length")
            accept_ranges = response.headers.get("Accept-Ranges", "").lower()
            content_range = response.headers.get("Content-Range", "")

            if content_length and content_length.isdigit():
                self.total_size = int(content_length)

            if accept_ranges == "bytes" or content_range:
                self.supports_ranges = True
                if content_range and not self.total_size:
                    # Content-Range format: bytes 0-0/123456
                    match = re.search(r"/(\d+)", content_range)
                    if match:
                        self.total_size = int(match.group(1))
            else:
                self.supports_ranges = False

            return True
        except Exception as e:
            self.error_message = f"Failed to inspect URL: {str(e)}"
            self.status = "Error"
            if self.on_status_change:
                self.on_status_change(self)
            return False

    def setup_segments(self):
        """Prepare segment ranges and inspect existing partial files."""
        os.makedirs(self.save_dir, exist_ok=True)
        self.segments = []

        if not self.supports_ranges or self.total_size <= 0:
            # Fallback to single segment
            part_path = self.get_part_file_path(0)
            existing = os.path.getsize(part_path) if os.path.exists(part_path) else 0
            self.segments.append(SegmentInfo(0, 0, self.total_size - 1 if self.total_size > 0 else 0, existing))
            return

        # Multi-segment partition
        chunk_size = self.total_size // self.connections
        for i in range(self.connections):
            start = i * chunk_size
            end = (self.total_size - 1) if (i == self.connections - 1) else ((i + 1) * chunk_size - 1)
            part_path = self.get_part_file_path(i)
            existing = os.path.getsize(part_path) if os.path.exists(part_path) else 0
            
            # Bound existing downloaded to avoid overflow
            existing = min(existing, end - start + 1)
            self.segments.append(SegmentInfo(i, start, end, existing))

    def _download_segment(self, seg: SegmentInfo):
        part_path = self.get_part_file_path(seg.index)
        current_pos = seg.start + seg.downloaded

        if current_pos > seg.end and seg.end >= seg.start:
            with self.segment_lock:
                seg.is_finished = True
                seg.is_active = False
            return

        headers = {
            "User-Agent": self.user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        if self.referer:
            headers["Referer"] = self.referer
        if self.cookies:
            headers["Cookie"] = self.cookies

        if self.supports_ranges and self.total_size > 0:
            headers["Range"] = f"bytes={current_pos}-{seg.end}"

        try:
            mode = "ab" if (os.path.exists(part_path) and seg.downloaded > 0) else "wb"
            with requests.get(self.url, headers=headers, stream=True, timeout=20) as resp:
                if self.supports_ranges and resp.status_code not in (200, 206):
                    raise RuntimeError(f"HTTP Error {resp.status_code} for range request")

                with open(part_path, mode) as f:
                    last_chunk_time = time.time()
                    for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                        if self.stop_event.is_set():
                            break
                        if chunk:
                            # Dynamic check: did another thread split our remaining range and shrink seg.end?
                            with self.segment_lock:
                                remaining_for_seg = (seg.end - (seg.start + seg.downloaded) + 1)

                            if remaining_for_seg <= 0:
                                break

                            chunk_len = len(chunk)
                            if chunk_len > remaining_for_seg:
                                f.write(chunk[:remaining_for_seg])
                                seg.downloaded += remaining_for_seg
                                break
                            else:
                                f.write(chunk)
                                seg.downloaded += chunk_len
                                if (seg.start + seg.downloaded) > seg.end:
                                    break

                            # Speed Limiter
                            if self.speed_limit > 0:
                                with self.segment_lock:
                                    num_active = max(1, sum(1 for s in self.segments if s.is_active))
                                per_thread_limit = self.speed_limit / num_active
                                now = time.time()
                                elapsed = now - last_chunk_time
                                expected_time = chunk_len / per_thread_limit
                                if expected_time > elapsed:
                                    sleep_sec = min(2.0, expected_time - elapsed)
                                    time.sleep(sleep_sec)
                                last_chunk_time = time.time()
        except Exception as e:
            if not self.stop_event.is_set():
                self.error_message = f"Segment {seg.index} error: {str(e)}"
        finally:
            with self.segment_lock:
                seg.is_active = False
                if seg.end >= seg.start and (seg.start + seg.downloaded) > seg.end:
                    seg.is_finished = True

    def _segment_worker(self, worker_id: int):
        """Worker thread executing Dynamic Chunk Splitting (work-stealing)."""
        while not self.stop_event.is_set():
            seg_to_download = None
            with self.segment_lock:
                # 1. Grab an unstarted or unfinished inactive segment
                for s in self.segments:
                    if not s.is_finished and not s.is_active:
                        s.is_active = True
                        seg_to_download = s
                        break

                # 2. Dynamic Chunk Splitting (Work-Stealing):
                # If all segments are either finished or actively downloading,
                # steal work from the segment with the largest remaining byte buffer!
                if not seg_to_download and self.supports_ranges and self.total_size > 0:
                    best_seg = None
                    max_rem = 0
                    for s in self.segments:
                        if not s.is_finished and s.is_active:
                            rem = s.end - (s.start + s.downloaded) + 1
                            if rem > max_rem:
                                max_rem = rem
                                best_seg = s

                    # Only split if remaining buffer >= MIN_SPLIT_SIZE (1 MB)
                    if best_seg and max_rem >= MIN_SPLIT_SIZE:
                        curr_pos = best_seg.start + best_seg.downloaded
                        half = max_rem // 2
                        new_start = curr_pos + half
                        new_end = best_seg.end

                        # Shrink the victim segment's end boundary
                        best_seg.end = new_start - 1

                        # Allocate new dynamic sub-segment
                        new_index = len(self.segments)
                        new_seg = SegmentInfo(new_index, new_start, new_end, 0)
                        new_seg.is_active = True
                        self.segments.append(new_seg)
                        seg_to_download = new_seg

            if not seg_to_download:
                # No work available to do or steal
                break

            self._download_segment(seg_to_download)

    def _run_video_download(self):
        try:
            os.makedirs(self.save_dir, exist_ok=True)
            self.category = "Music" if self.video_quality == "audio" else "Video"

            # Format selector based on quality
            if self.video_quality == "audio":
                fmt = "bestaudio/best"
                postprocessors = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            elif self.video_quality == "1080":
                fmt = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
                postprocessors = []
            elif self.video_quality == "720":
                fmt = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best"
                postprocessors = []
            elif self.video_quality == "480":
                fmt = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]/best"
                postprocessors = []
            elif self.video_quality == "360":
                fmt = "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=360]+bestaudio/best[height<=360]/best"
                postprocessors = []
            else:  # "best"
                fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best"
                postprocessors = []

            if self.filename and not self.filename.endswith(".part"):
                stem = os.path.splitext(self.filename)[0]
                outtmpl = os.path.join(self.save_dir, f"{stem}.%(ext)s")
            else:
                outtmpl = os.path.join(self.save_dir, "%(title)s.%(ext)s")

            last_progress_time = [time.time()]

            def hook(d):
                if self.stop_event.is_set():
                    raise RuntimeError("Download paused by user")

                status = d.get("status")
                if status == "downloading":
                    dl_bytes = d.get("downloaded_bytes", 0)
                    tot_bytes = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                    speed = d.get("speed", 0.0) or 0.0
                    eta = d.get("eta", 0.0) or 0.0

                    self.downloaded_size = dl_bytes
                    if tot_bytes > 0:
                        self.total_size = tot_bytes
                    self.speed = speed
                    self.eta = eta
                    self.speed_history.append(speed)

                    now = time.time()
                    if now - last_progress_time[0] >= 0.3:
                        last_progress_time[0] = now
                        if self.on_progress:
                            self.on_progress(self)
                elif status == "finished":
                    final_filename = d.get("filename")
                    if final_filename:
                        self.filename = os.path.basename(final_filename)

            http_headers = {}
            if self.user_agent:
                http_headers['User-Agent'] = self.user_agent
            if self.referer:
                http_headers['Referer'] = self.referer
            if self.cookies:
                http_headers['Cookie'] = self.cookies

            ydl_opts = {
                'format': fmt,
                'outtmpl': outtmpl,
                'progress_hooks': [hook],
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'concurrent_fragment_downloads': max(1, min(32, self.connections)),
            }
            if http_headers:
                ydl_opts['http_headers'] = http_headers
            if postprocessors:
                ydl_opts['postprocessors'] = postprocessors

            if self.speed_limit > 0:
                ydl_opts['ratelimit'] = self.speed_limit

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                if info:
                    if 'requested_downloads' in info and info['requested_downloads']:
                        final_path = info['requested_downloads'][0].get('filepath')
                        if final_path and os.path.exists(final_path):
                            self.filename = os.path.basename(final_path)
                            self.total_size = os.path.getsize(final_path)
                            self.downloaded_size = self.total_size

            if self.stop_event.is_set():
                self.status = "Paused"
                self.speed = 0
                if self.on_status_change:
                    self.on_status_change(self)
                return

            self.status = "Completed"
            self.speed = 0
            self.eta = 0
            if os.path.exists(self.target_file_path):
                self.total_size = os.path.getsize(self.target_file_path)
                self.downloaded_size = self.total_size
            if self.on_complete:
                self.on_complete(self)
        except Exception as e:
            if self.stop_event.is_set():
                self.status = "Paused"
                self.speed = 0
                if self.on_status_change:
                    self.on_status_change(self)
            else:
                self.status = "Error"
                self.error_message = str(e)
                self.speed = 0
                if self.on_status_change:
                    self.on_status_change(self)

    def start(self):
        """Start or resume the download in background threads."""
        if self.status == "Downloading":
            return

        self.stop_event.clear()
        self.status = "Downloading"
        self.error_message = ""
        if self.on_status_change:
            self.on_status_change(self)

        def runner():
            if (self.task_type == "video" or is_video_streaming_url(self.url)) and HAS_YTDLP:
                self._run_video_download()
                return

            if not self.total_size or not self.filename:
                if not self.inspect_url():
                    return

            self.setup_segments()

            # Start worker threads with Dynamic Chunk Splitting
            num_workers = min(self.connections, len(self.segments))
            self.worker_threads = []
            for w_id in range(num_workers):
                t = threading.Thread(target=self._segment_worker, args=(w_id,), daemon=True)
                t.start()
                self.worker_threads.append(t)

            # Monitor progress
            last_bytes = sum(s.downloaded for s in self.segments)
            last_time = time.time()

            while any(t.is_alive() for t in self.worker_threads):
                if self.stop_event.is_set():
                    break
                time.sleep(0.4)
                now = time.time()
                dt = now - last_time
                with self.segment_lock:
                    current_bytes = sum(s.downloaded for s in self.segments)
                self.downloaded_size = current_bytes

                if dt >= 0.4:
                    inst_speed = max(0.0, (current_bytes - last_bytes) / dt)
                    self.speed = (self.speed * 0.7) + (inst_speed * 0.3) if self.speed > 0 else inst_speed
                    self.speed_history.append(self.speed)
                    remaining_bytes = max(0, self.total_size - current_bytes)
                    self.eta = (remaining_bytes / self.speed) if self.speed > 1024 else 0
                    last_bytes = current_bytes
                    last_time = now

                if self.on_progress:
                    self.on_progress(self)

            for t in self.worker_threads:
                t.join(timeout=1.0)

            if self.stop_event.is_set():
                if self.status != "Error":
                    self.status = "Paused"
                self.speed = 0
                if self.on_status_change:
                    self.on_status_change(self)
                return

            # Check if any segment failed
            with self.segment_lock:
                all_done = all(s.is_finished for s in self.segments) if (self.total_size > 0 and self.supports_ranges) else True
            if self.error_message:
                self.status = "Error"
                self.speed = 0
                if self.on_status_change:
                    self.on_status_change(self)
                return

            if all_done:
                # Merge segments
                try:
                    self._merge_files()
                    self.status = "Completed"
                    self.downloaded_size = self.total_size if self.total_size > 0 else os.path.getsize(self.target_file_path)
                    self.speed = 0
                    self.eta = 0
                    if self.on_complete:
                        self.on_complete(self)
                except Exception as e:
                    self.status = "Error"
                    self.error_message = f"Failed to assemble file: {str(e)}"
                
                if self.on_status_change:
                    self.on_status_change(self)
                if self.on_progress:
                    self.on_progress(self)

        threading.Thread(target=runner, daemon=True).start()

    def pause(self):
        """Pause the download safely."""
        if self.status == "Downloading":
            self.stop_event.set()
            self.status = "Paused"
            self.speed = 0
            if self.on_status_change:
                self.on_status_change(self)

    def _merge_files(self):
        """Assemble all downloaded chunks in byte-offset sorted order into final file."""
        temp_merged = self.target_file_path + ".assembling"
        with self.segment_lock:
            sorted_segments = sorted(self.segments, key=lambda s: s.start)

        with open(temp_merged, "wb") as outfile:
            for seg in sorted_segments:
                part_path = self.get_part_file_path(seg.index)
                if os.path.exists(part_path):
                    with open(part_path, "rb") as infile:
                        shutil.copyfileobj(infile, outfile, length=MERGE_BUFFER)

        # Rename to final file atomically
        if os.path.exists(self.target_file_path):
            os.remove(self.target_file_path)
        os.rename(temp_merged, self.target_file_path)

        # Cleanup part files
        for seg in self.segments:
            part_path = self.get_part_file_path(seg.index)
            if os.path.exists(part_path):
                try:
                    os.remove(part_path)
                except OSError:
                    pass

    def delete_files(self, delete_downloaded=True):
        """Delete temporary and downloaded files."""
        self.pause()
        for seg in list(self.segments):
            part_path = self.get_part_file_path(seg.index)
            if os.path.exists(part_path):
                try:
                    os.remove(part_path)
                except OSError:
                    pass
        if delete_downloaded and os.path.exists(self.target_file_path):
            try:
                os.remove(self.target_file_path)
            except OSError:
                pass
