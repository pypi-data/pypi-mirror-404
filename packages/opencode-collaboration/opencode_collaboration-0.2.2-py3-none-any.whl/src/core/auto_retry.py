"""智能重试模块。"""
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import logging

from ..utils.yaml import load_yaml, save_yaml
from .git import GitHelper, GitOperationError, GitConflictError

logger = logging.getLogger(__name__)


@dataclass
class AutoRetryConfig:
    """智能重试配置"""
    max_retries: int = 10
    retry_interval: int = 30
    exponential_backoff: bool = True
    max_interval: int = 300
    verbose: bool = True


class RetryableError(Exception):
    """可重试错误"""
    pass


class NonRetryableError(Exception):
    """不可重试错误"""
    pass


class AutoRetry:
    """智能重试器"""
    
    RETRYABLE_ERRORS = [
        "ConnectionError",
        "Timeout",
        "Connection reset",
        "Connection refused",
        "NetworkUnreachable",
        "Temporary failure in name resolution",
        "443",
        "Failed to connect",
        "Couldn't connect to server",
        "Connection timed out",
        "HTTP 5",
        "error in libcurl",
        "Error in the HTTP2 framing layer",
    ]
    
    NON_RETRYABLE_ERRORS = [
        "Authentication failed",
        "Permission denied",
        "401",
        "403",
        "invalid credentials",
        "could not read Username",
    ]
    
    def __init__(self, project_path: str, config: Optional[AutoRetryConfig] = None):
        """初始化智能重试器"""
        self.project_path = Path(project_path)
        self.git_helper = GitHelper(str(project_path))
        self.config = config or AutoRetryConfig()
        self.state_file = self.project_path / "state" / "project_state.yaml"
    
    def _load_state(self) -> Dict[str, Any]:
        """加载状态"""
        if self.state_file.exists():
            return load_yaml(str(self.state_file))
        return {}
    
    def _save_state(self, state: Dict[str, Any]) -> None:
        """保存状态"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        save_yaml(str(self.state_file), state)
    
    def _should_retry(self, error: Exception) -> bool:
        """判断是否应该重试"""
        error_str = str(error).lower()
        
        for keyword in self.NON_RETRYABLE_ERRORS:
            if keyword.lower() in error_str:
                return False
        
        for keyword in self.RETRYABLE_ERRORS:
            if keyword.lower() in error_str:
                return True
        
        return False
    
    def _calculate_delay(self, attempt: int) -> int:
        """计算延迟时间（秒）"""
        if self.config.exponential_backoff:
            delay = min(
                self.config.retry_interval * (2 ** attempt),
                self.config.max_interval
            )
        else:
            delay = self.config.retry_interval
        return delay
    
    def _log_retry(self, attempt: int, error: str, delay: int) -> None:
        """记录重试日志"""
        remaining = self.config.max_retries - attempt
        logger.info(f"[Retry {attempt}/{self.config.max_retries}] {error}")
        logger.info(f"  等待 {delay} 秒后重试 ({remaining} 次重试机会)")
    
    def push_with_retry(self, message: str, remotes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        带重试的推送
        
        Args:
            message: 提交信息
            remotes: 远程仓库列表（默认所有）
        
        Returns:
            {
                "success": bool,
                "remotes": List[str],
                "attempts": int,
                "duration": int
            }
        """
        from ..utils.date import get_current_time
        start_time = time.time()
        
        if remotes is None:
            remotes = self.git_helper.get_all_remotes()
        
        result = {
            "success": False,
            "remotes": [],
            "attempts": 0,
            "duration": 0
        }
        
        for attempt in range(1, self.config.max_retries + 1):
            result["attempts"] = attempt
            
            try:
                if attempt == 1:
                    logger.info(f"开始推送到 {', '.join(remotes)}...")
                else:
                    delay = self._calculate_delay(attempt - 1)
                    if self.config.verbose:
                        self._log_retry(attempt, "推送失败", delay)
                    time.sleep(delay)
                
                for remote in remotes:
                    self.git_helper._run_git_command("push", remote, "--tags")
                    result["remotes"].append(remote)
                
                result["success"] = True
                result["duration"] = int(time.time() - start_time)
                logger.info(f"✓ 推送成功（尝试 {attempt} 次，耗时 {result['duration']} 秒）")
                return result
                
            except GitOperationError as e:
                error_msg = str(e)
                
                if not self._should_retry(e):
                    logger.error(f"✗ 不可恢复的错误: {error_msg}")
                    result["duration"] = int(time.time() - start_time)
                    return result
                
                if attempt >= self.config.max_retries:
                    logger.error(f"✗ 重试次数耗尽: {error_msg}")
                    result["duration"] = int(time.time() - start_time)
                    return result
        
        result["duration"] = int(time.time() - start_time)
        return result
    
    def pull_with_retry(self, remote: str = "origin") -> Dict[str, Any]:
        """
        带重试的拉取
        
        Args:
            remote: 远程仓库
        
        Returns:
            {
                "success": bool,
                "attempts": int,
                "duration": int
            }
        """
        start_time = time.time()
        
        result = {
            "success": False,
            "attempts": 0,
            "duration": 0
        }
        
        for attempt in range(1, self.config.max_retries + 1):
            result["attempts"] = attempt
            
            try:
                if attempt == 1:
                    logger.info(f"从 {remote} 拉取...")
                else:
                    delay = self._calculate_delay(attempt - 1)
                    if self.config.verbose:
                        self._log_retry(attempt, "拉取失败", delay)
                    time.sleep(delay)
                
                self.git_helper._run_git_command("pull", remote)
                result["success"] = True
                result["duration"] = int(time.time() - start_time)
                logger.info(f"✓ 拉取成功（尝试 {attempt} 次，耗时 {result['duration']} 秒）")
                return result
                
            except GitOperationError as e:
                error_msg = str(e)
                
                if not self._should_retry(e):
                    logger.error(f"✗ 不可恢复的错误: {error_msg}")
                    result["duration"] = int(time.time() - start_time)
                    return result
                
                if attempt >= self.config.max_retries:
                    logger.error(f"✗ 重试次数耗尽: {error_msg}")
                    result["duration"] = int(time.time() - start_time)
                    return result
        
        result["duration"] = int(time.time() - start_time)
        return result
