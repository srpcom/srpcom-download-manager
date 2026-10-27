import os
import json
import uuid
from typing import Dict, List, Optional, Callable
from .downloader import DownloadTask, detect_category

DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

class DownloadManager:
    def __init__(self, data_file: str = "downloads_data.json"):
        self.data_file = data_file
        self.tasks: Dict[str, DownloadTask] = {}
        self.global_speed_limit = 0  # 0 = unlimited, otherwise bytes/sec
        self.max_concurrent = 3      # Maximum simultaneous active downloads
        self.on_task_added: Optional[Callable[[DownloadTask], None]] = None
        self.on_task_updated: Optional[Callable[[DownloadTask], None]] = None
        self.on_task_removed: Optional[Callable[[str], None]] = None
        self.on_task_completed: Optional[Callable[[DownloadTask], None]] = None

    def load_tasks(self):
        if not os.path.exists(self.data_file):
            return

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                records = json.load(f)

            for rec in records:
                task = DownloadTask(
                    task_id=rec["task_id"],
                    url=rec["url"],
                    save_dir=rec["save_dir"],
                    filename=rec["filename"],
                    connections=rec.get("connections", 8),
                    task_type=rec.get("task_type", "file"),
                    video_quality=rec.get("video_quality", "best")
                )
                task.total_size = rec.get("total_size", 0)
                task.downloaded_size = rec.get("downloaded_size", 0)
                task.category = rec.get("category", detect_category(task.filename))
                saved_status = rec.get("status", "Paused")
                task.status = "Paused" if saved_status == "Downloading" else saved_status

                # Bind callbacks
                task.speed_limit = self.global_speed_limit
                task.on_progress = self._handle_task_progress
                task.on_status_change = self._handle_task_status_change
                task.on_complete = self._handle_task_completed

                self.tasks[task.task_id] = task
        except Exception as e:
            print(f"Error loading tasks: {e}")

    def save_tasks(self):
        try:
            records = []
            for task in self.tasks.values():
                records.append({
                    "task_id": task.task_id,
                    "url": task.url,
                    "save_dir": task.save_dir,
                    "filename": task.filename,
                    "connections": task.connections,
                    "task_type": task.task_type,
                    "video_quality": getattr(task, "video_quality", "best"),
                    "total_size": task.total_size,
                    "downloaded_size": task.downloaded_size,
                    "category": task.category,
                    "status": "Paused" if task.status == "Downloading" else task.status
                })
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving tasks: {e}")

    def _handle_task_progress(self, task: DownloadTask):
        if self.on_task_updated:
            self.on_task_updated(task)

    def _handle_task_status_change(self, task: DownloadTask):
        self.save_tasks()
        if self.on_task_updated:
            self.on_task_updated(task)

    def _handle_task_completed(self, task: DownloadTask):
        self.save_tasks()
        if self.on_task_completed:
            self.on_task_completed(task)
        self.check_queue()

    def check_queue(self):
        """Start next queued task if active downloads < max_concurrent."""
        active_count = sum(1 for t in self.tasks.values() if t.status == "Downloading")
        if active_count < self.max_concurrent:
            for task in self.tasks.values():
                if task.status == "Queued":
                    task.start()
                    active_count += 1
                    if active_count >= self.max_concurrent:
                        break

    def set_global_speed_limit(self, limit_bps: int):
        self.global_speed_limit = limit_bps
        for task in self.tasks.values():
            task.speed_limit = limit_bps

    def add_task(
        self,
        url: str,
        save_dir: str = DEFAULT_DOWNLOAD_DIR,
        filename: str = "",
        connections: int = 8,
        start_now: bool = True,
        task_type: str = "file",
        video_quality: str = "best",
        cookies: str = "",
        referer: str = "",
        user_agent: str = ""
    ) -> DownloadTask:
        task_id = str(uuid.uuid4())[:8]
        task = DownloadTask(
            task_id=task_id,
            url=url,
            save_dir=save_dir,
            filename=filename,
            connections=connections,
            task_type=task_type,
            video_quality=video_quality,
            cookies=cookies,
            referer=referer,
            user_agent=user_agent
        )
        task.speed_limit = self.global_speed_limit
        task.on_progress = self._handle_task_progress
        task.on_status_change = self._handle_task_status_change
        task.on_complete = self._handle_task_completed

        self.tasks[task_id] = task
        self.save_tasks()

        if self.on_task_added:
            self.on_task_added(task)

        if start_now:
            active_count = sum(1 for t in self.tasks.values() if t.status == "Downloading")
            if active_count < self.max_concurrent:
                task.start()
            else:
                task.status = "Queued"
                if task.on_status_change:
                    task.on_status_change(task)

        return task

    def pause_task(self, task_id: str):
        if task_id in self.tasks:
            self.tasks[task_id].pause()
            self.save_tasks()
            self.check_queue()

    def resume_task(self, task_id: str):
        if task_id in self.tasks:
            self.tasks[task_id].start()
            self.save_tasks()

    def delete_task(self, task_id: str, delete_file: bool = False):
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.delete_files(delete_downloaded=delete_file)
            del self.tasks[task_id]
            self.save_tasks()
            if self.on_task_removed:
                self.on_task_removed(task_id)

    def pause_all(self):
        for task in self.tasks.values():
            if task.status == "Downloading":
                task.pause()
        self.save_tasks()

    def resume_all(self):
        for task in self.tasks.values():
            if task.status in ("Paused", "Queued"):
                task.start()
        self.save_tasks()
