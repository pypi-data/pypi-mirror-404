"""锁文件工具模块。"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class LockError(Exception):
    """锁文件异常基类。"""
    pass


class LockExistsError(LockError):
    """锁文件已存在异常。"""
    pass


class LockNotFoundError(LockError):
    """锁文件不存在异常。"""
    pass


class LockManager:
    """锁文件管理器。"""
    
    DEFAULT_LOCK_FILE = ".auto_lock"
    
    def __init__(self, project_path: str, lock_file: Optional[str] = None):
        """初始化锁管理器。"""
        self.project_path = Path(project_path)
        self.lock_file = lock_file or self.DEFAULT_LOCK_FILE
        self.lock_path = self.project_path / self.lock_file
    
    def acquire(self, description: str = "") -> Dict[str, Any]:
        """获取锁。"""
        if self.lock_path.exists():
            raise LockExistsError(f"锁文件已存在: {self.lock_path}")
        
        lock_info = {
            "created_at": datetime.now().isoformat(),
            "pid": os.getpid(),
            "description": description
        }
        
        with open(self.lock_path, 'w', encoding='utf-8') as f:
            json.dump(lock_info, f, ensure_ascii=False, indent=2)
        
        return lock_info
    
    def release(self) -> None:
        """释放锁。"""
        if not self.lock_path.exists():
            raise LockNotFoundError("锁文件不存在")
        
        self.lock_path.unlink()
    
    def is_locked(self) -> bool:
        """检查是否已加锁。"""
        return self.lock_path.exists()
    
    def get_lock_info(self) -> Optional[Dict[str, str]]:
        """获取锁信息。"""
        if not self.lock_path.exists():
            return None
        
        with open(self.lock_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def check_and_cleanup(self) -> bool:
        """检查并清理过期锁。"""
        if not self.lock_path.exists():
            return True
        
        try:
            lock_info = self.get_lock_info()
            if lock_info is None:
                return True
            
            created_at = datetime.fromisoformat(lock_info["created_at"])
            now = datetime.now()
            hours_diff = (now - created_at).total_seconds() / 3600
            
            if hours_diff > 24:
                self.release()
                return True
            
            return False
        except Exception:
            return False


def create_lock(project_path: str, description: str = "") -> LockManager:
    """创建锁。"""
    manager = LockManager(project_path)
    manager.acquire(description)
    return manager


def remove_lock(project_path: str) -> None:
    """移除锁。"""
    manager = LockManager(project_path)
    manager.release()
