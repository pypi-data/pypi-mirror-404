"""Git监控模块。"""
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import logging


logger = logging.getLogger(__name__)


class GitMonitorError(Exception):
    """Git监控异常基类。"""
    pass


class GitNotInstalledError(GitMonitorError):
    """Git未安装异常。"""
    pass


class NotRepositoryError(GitMonitorError):
    """非Git仓库异常。"""
    pass


class NetworkError(GitMonitorError):
    """网络异常。"""
    pass


class ChangeType(Enum):
    """变更类型枚举。"""
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


@dataclass
class CommitInfo:
    """提交信息。"""
    hash: str
    short_hash: str
    message: str
    author: str
    timestamp: str
    files: List[Dict[str, Any]] = field(default_factory=list)
    parents: List[str] = field(default_factory=list)


@dataclass
class ChangeInfo:
    """文件变更信息。"""
    file_path: str
    change_type: ChangeType
    old_path: Optional[str] = None
    diff: Optional[str] = None


@dataclass
class GitEvent:
    """Git事件。"""
    event_type: str
    commit: Optional[CommitInfo] = None
    changes: List[ChangeInfo] = field(default_factory=list)
    branch: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    raw_output: str = ""


class GitConfig:
    """Git监控配置。"""
    
    DEFAULT_POLLING_INTERVAL = 30
    MAX_POLLING_INTERVAL = 300
    MIN_POLLING_INTERVAL = 10
    EXPONENTIAL_BASE = 2
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    
    def __init__(
        self,
        polling_interval: int = DEFAULT_POLLING_INTERVAL,
        max_polling_interval: int = MAX_POLLING_INTERVAL,
        enable_exponential_backoff: bool = True,
        enable_webhook: bool = False,
        webhook_url: Optional[str] = None
    ):
        self.polling_interval = max(self.MIN_POLLING_INTERVAL, polling_interval)
        self.max_polling_interval = max_polling_interval
        self.enable_exponential_backoff = enable_exponential_backoff
        self.enable_webhook = enable_webhook
        self.webhook_url = webhook_url


class GitMonitor:
    """Git监控器。"""
    
    def __init__(self, project_path: str, config: Optional[GitConfig] = None):
        """初始化Git监控器。"""
        self.project_path = Path(project_path)
        self.config = config or GitConfig()
        self._processed_commits: Set[str] = set()
        self._last_commit: Optional[str] = None
        self._last_poll_time: float = 0
        self._current_poll_interval: int = self.config.polling_interval
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._callbacks: List[callable] = []
        self._lock = threading.Lock()
        
        self._ensure_git_installed()
        self._ensure_repository()
    
    def _ensure_git_installed(self) -> None:
        """检查Git是否已安装。"""
        try:
            subprocess.run(
                ["git", "--version"],
                check=True,
                capture_output=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise GitNotInstalledError("Git未安装或无法访问")
    
    def _ensure_repository(self) -> None:
        """检查是否为Git仓库。"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=str(self.project_path),
                check=True,
                capture_output=True
            )
            if result.stdout.strip() != "true":
                raise NotRepositoryError("当前目录不是Git仓库")
        except subprocess.CalledProcessError:
            raise NotRepositoryError("当前目录不是Git仓库")
    
    def _run_git_command(self, *args, check: bool = True, retries: int = 0) -> subprocess.CompletedProcess:
        """运行Git命令。"""
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                check=check,
                timeout=30
            )
            return result
        except subprocess.TimeoutExpired:
            raise NetworkError("Git操作超时")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            if "could not read" in error_msg.lower() or "connection" in error_msg.lower():
                if retries < self.config.MAX_RETRIES:
                    time.sleep(self.config.RETRY_DELAY * (retries + 1))
                    return self._run_git_command(*args, check=check, retries=retries + 1)
                raise NetworkError(f"网络错误: {error_msg}")
            raise GitMonitorError(f"Git命令执行失败: {error_msg}")
    
    def get_current_branch(self) -> str:
        """获取当前分支名称。"""
        result = self._run_git_command("rev-parse", "--abbrev-ref", "HEAD")
        return result.stdout.strip()
    
    def get_remote_url(self) -> Optional[str]:
        """获取远程仓库URL。"""
        try:
            result = self._run_git_command("remote", "get-url", "origin", check=False)
            return result.stdout.strip() if result.stdout else None
        except GitMonitorError:
            return None
    
    def fetch_remote(self) -> bool:
        """拉取远程变更。"""
        try:
            self._run_git_command("fetch", "origin")
            return True
        except GitMonitorError:
            return False
    
    def get_commit_hash(self, ref: str = "HEAD") -> Optional[str]:
        """获取指定引用的提交哈希。"""
        try:
            result = self._run_git_command("rev-parse", ref)
            return result.stdout.strip()
        except GitMonitorError:
            return None
    
    def get_commit_info(self, commit_hash: str) -> Optional[CommitInfo]:
        """获取提交详细信息。"""
        try:
            hash_result = self._run_git_command("rev-parse", commit_hash)
            full_hash = hash_result.stdout.strip()
            short_hash = full_hash[:7]
            
            msg_result = self._run_git_command("log", "-1", "--format=%H|%an|%ae|%ai|%s", commit_hash)
            msg_parts = msg_result.stdout.strip().split("|", 4)
            
            if len(msg_parts) >= 5:
                author_email = msg_parts[2]
                timestamp = msg_parts[3]
                message = msg_parts[4]
            else:
                author_email = ""
                timestamp = ""
                message = ""
            
            files_result = self._run_git_command("show", "--name-status", "--pretty=format:", commit_hash)
            files = []
            for line in files_result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("\t", 1)
                    if len(parts) == 2:
                        status = parts[0].strip()
                        file_path = parts[1].strip()
                        change_type = self._parse_change_type(status)
                        files.append({
                            "path": file_path,
                            "type": change_type.value
                        })
            
            parents_result = self._run_git_command("rev-list", "--parents", "-n", "1", commit_hash)
            parents = parents_result.stdout.strip().split()[1:] if parents_result.stdout.strip() else []
            
            return CommitInfo(
                hash=full_hash,
                short_hash=short_hash,
                message=message,
                author=msg_parts[1] if len(msg_parts) > 1 else "unknown",
                timestamp=timestamp,
                files=files,
                parents=parents
            )
        except GitMonitorError:
            return None
    
    def _parse_change_type(self, status: str) -> ChangeType:
        """解析变更类型。"""
        status_map = {
            "A": ChangeType.ADDED,
            "M": ChangeType.MODIFIED,
            "D": ChangeType.DELETED,
            "R": ChangeType.RENAMED
        }
        return status_map.get(status[0] if status else "", ChangeType.MODIFIED)
    
    def get_new_commits(self, since_ref: Optional[str] = None) -> List[CommitInfo]:
        """获取新提交列表。"""
        commits = []
        since = since_ref or self._last_commit or "HEAD"
        
        try:
            rev_list_result = self._run_git_command(
                "rev-list", "--reverse", f"^{since}", "HEAD"
            )
            
            if not rev_list_result.stdout.strip():
                return commits
            
            commit_hashes = rev_list_result.stdout.strip().split("\n")
            
            for commit_hash in commit_hashes:
                commit_hash = commit_hash.strip()
                if commit_hash and commit_hash not in self._processed_commits:
                    commit_info = self.get_commit_info(commit_hash)
                    if commit_info:
                        commits.append(commit_info)
                        self._processed_commits.add(commit_hash)
            
            if commits:
                self._last_commit = commits[-1].hash
            
            return commits
        except GitMonitorError:
            return []
    
    def detect_changes(self) -> List[GitEvent]:
        """检测变更。"""
        events = []
        current_branch = self.get_current_branch()
        
        self.fetch_remote()
        new_commits = self.get_new_commits()
        
        for commit in new_commits:
            changes = []
            for file_info in commit.files:
                change_type = ChangeType(file_info["type"]) if file_info["type"] in [e.value for e in ChangeType] else ChangeType.MODIFIED
                changes.append(ChangeInfo(
                    file_path=file_info["path"],
                    change_type=change_type
                ))
            
            event = GitEvent(
                event_type="new_commit",
                commit=commit,
                changes=changes,
                branch=current_branch
            )
            events.append(event)
        
        return events
    
    def detect_state_file_changes(self) -> Dict[str, Any]:
        """检测状态文件变更。"""
        state_file = self.project_path / "state" / "project_state.yaml"
        
        if not state_file.exists():
            return {"has_changes": False, "reason": "状态文件不存在"}
        
        changes = self.detect_changes()
        
        for event in changes:
            for change in event.changes:
                if "project_state.yaml" in change.file_path:
                    return {
                        "has_changes": True,
                        "commit": event.commit.hash if event.commit else None,
                        "change_type": change.change_type.value
                    }
        
        return {"has_changes": False}
    
    def get_status_summary(self) -> Dict[str, Any]:
        """获取监控状态摘要。"""
        return {
            "project_path": str(self.project_path),
            "current_branch": self.get_current_branch(),
            "remote_url": self.get_remote_url(),
            "last_commit": self._last_commit,
            "processed_commits_count": len(self._processed_commits),
            "polling_interval": self._current_poll_interval,
            "is_running": self._running,
            "config": {
                "polling_interval": self.config.polling_interval,
                "max_polling_interval": self.config.max_polling_interval,
                "enable_exponential_backoff": self.config.enable_exponential_backoff
            }
        }
    
    def add_callback(self, callback: callable) -> None:
        """添加变更回调函数。"""
        with self._lock:
            self._callbacks.append(callback)
    
    def _notify_callbacks(self, events: List[GitEvent]) -> None:
        """通知回调函数。"""
        with self._lock:
            callbacks = self._callbacks.copy()
        
        for callback in callbacks:
            try:
                callback(events)
            except Exception as e:
                logger.error(f"回调函数执行失败: {e}")
    
    def _adjust_polling_interval(self, has_changes: bool) -> None:
        """调整轮询间隔。"""
        if not self.config.enable_exponential_backoff:
            self._current_poll_interval = self.config.polling_interval
            return
        
        if has_changes:
            self._current_poll_interval = self.config.polling_interval
        else:
            self._current_poll_interval = min(
                self._current_poll_interval * self.config.EXPONENTIAL_BASE,
                self.config.max_polling_interval
            )
    
    def start_monitoring(self, callback: Optional[callable] = None) -> None:
        """开始监控（轮询模式）。"""
        if self._running:
            return
        
        if callback:
            self.add_callback(callback)
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def _monitor_loop(self) -> None:
        """监控循环。"""
        while self._running:
            try:
                current_time = time.time()
                elapsed = current_time - self._last_poll_time
                
                if elapsed >= self._current_poll_interval:
                    events = self.detect_changes()
                    has_changes = len(events) > 0
                    self._adjust_polling_interval(has_changes)
                    self._last_poll_time = current_time
                    
                    if events:
                        self._notify_callbacks(events)
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
            
            time.sleep(1)
    
    def stop_monitoring(self) -> None:
        """停止监控。"""
        self._running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
        self._monitor_thread = None
    
    def reset_processed_commits(self) -> None:
        """重置已处理提交记录。"""
        self._processed_commits.clear()
        self._last_commit = None
    
    def check_remote_connection(self) -> bool:
        """检查远程仓库连接。"""
        try:
            self._run_git_command("ls-remote", "--heads", "origin")
            return True
        except GitMonitorError:
            return False
