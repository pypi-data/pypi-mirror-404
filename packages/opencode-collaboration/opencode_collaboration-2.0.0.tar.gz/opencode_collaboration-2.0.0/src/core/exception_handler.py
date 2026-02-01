"""异常处理模块。"""
import traceback
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import threading
import time


logger = logging.getLogger(__name__)


class ExceptionType(Enum):
    """异常类型枚举。"""
    RETRYABLE = "retryable"
    RECOVERABLE = "recoverable"
    FATAL = "fatal"


class ExceptionSeverity(Enum):
    """异常严重程度枚举。"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ExceptionHandlerError(Exception):
    """异常处理器异常基类。"""
    pass


class UnhandledExceptionError(ExceptionHandlerError):
    """未处理异常。"""
    pass


class RecoveryError(ExceptionHandlerError):
    """恢复异常。"""
    pass


@dataclass
class ExceptionInfo:
    """异常信息。"""
    exception_type: ExceptionType
    severity: ExceptionSeverity
    message: str
    timestamp: str
    agent_id: str
    phase: str
    context: Dict[str, Any]
    stack_trace: str = ""
    exception_class: str = ""
    handled: bool = False
    recovery_attempts: int = 0
    last_recovery_time: Optional[str] = None


@dataclass
class CrashInfo:
    """崩溃信息。"""
    crash_id: str
    timestamp: str
    agent_id: str
    phase: str
    last_action: str
    state_version: int
    pending_tasks: List[str]
    exception_info: Optional[ExceptionInfo] = None
    recovery_status: str = "pending"
    recovery_attempts: int = 0


class NotificationChannel(Enum):
    """通知渠道枚举。"""
    LOG = "log"
    FILE = "file"
    WEBHOOK = "webhook"
    EMAIL = "email"


@dataclass
class NotificationConfig:
    """通知配置。"""
    channel: NotificationChannel
    enabled: bool = True
    webhook_url: Optional[str] = None
    email_recipients: List[str] = field(default_factory=list)
    min_severity: ExceptionSeverity = ExceptionSeverity.MEDIUM


class ExceptionHandler:
    """异常处理器。"""
    
    CRASH_LOG_DIR = "state/crash_logs"
    RECOVERY_DIR = "state/recovery"
    
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 5
    
    def __init__(self, agent_id: str, phase: str = "unknown"):
        """初始化异常处理器。"""
        self.agent_id = agent_id
        self.current_phase = phase
        self.crash_log_dir = Path(self.CRASH_LOG_DIR)
        self.recovery_dir = Path(self.RECOVERY_DIR)
        self._ensure_directories()
        
        self._exception_handlers: Dict[ExceptionType, Callable] = {}
        self._global_exception_handler: Optional[Callable] = None
        self._notification_configs: List[NotificationConfig] = []
        
        self._current_exception: Optional[ExceptionInfo] = None
        self._retry_count: int = 0
        
        self._register_default_handlers()
    
    def _ensure_directories(self) -> None:
        """确保必要目录存在。"""
        self.crash_log_dir.mkdir(parents=True, exist_ok=True)
        self.recovery_dir.mkdir(parents=True, exist_ok=True)
    
    def _register_default_handlers(self) -> None:
        """注册默认异常处理器。"""
        self._exception_handlers[ExceptionType.RETRYABLE] = self._handle_retryable
        self._exception_handlers[ExceptionType.RECOVERABLE] = self._handle_recoverable
        self._exception_handlers[ExceptionType.FATAL] = self._handle_fatal
    
    def register_exception_handler(
        self,
        exception_type: ExceptionType,
        handler: Callable[[ExceptionInfo], Tuple[bool, str]]
    ) -> None:
        """注册异常处理器。"""
        self._exception_handlers[exception_type] = handler
        logger.info(f"已注册异常处理器: {exception_type.value}")
    
    def set_global_exception_handler(
        self,
        handler: Callable[[Exception, ExceptionInfo], None]
    ) -> None:
        """设置全局异常处理器。"""
        self._global_exception_handler = handler
    
    def add_notification_config(self, config: NotificationConfig) -> None:
        """添加通知配置。"""
        self._notification_configs.append(config)
    
    def classify_exception(self, exception: Exception) -> Tuple[ExceptionType, ExceptionSeverity]:
        """分类异常。"""
        exception_class = type(exception).__name__
        exception_message = str(exception)
        
        retryable_patterns = [
            "network", "timeout", "connection", "retry",
            "git fetch", "git pull"
        ]
        
        recoverable_patterns = [
            "state", "lock", "conflict", "version",
            "yaml", "parse"
        ]
        
        fatal_patterns = [
            "permission", "disk", "memory", "keyboard_interrupt",
            "sigterm", "git not found"
        ]
        
        exception_str = f"{exception_class} {exception_message}".lower()
        
        for pattern in retryable_patterns:
            if pattern in exception_str:
                return ExceptionType.RETRYABLE, ExceptionSeverity.MEDIUM
        
        for pattern in recoverable_patterns:
            if pattern in exception_str:
                return ExceptionType.RECOVERABLE, ExceptionSeverity.HIGH
        
        for pattern in fatal_patterns:
            if pattern in exception_str:
                return ExceptionType.FATAL, ExceptionSeverity.CRITICAL
        
        if "git" in exception_str:
            return ExceptionType.RETRYABLE, ExceptionSeverity.MEDIUM
        
        return ExceptionType.RECOVERABLE, ExceptionSeverity.MEDIUM
    
    def handle_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        phase: Optional[str] = None
    ) -> Tuple[bool, str]:
        """处理异常。"""
        exception_type, severity = self.classify_exception(exception)
        
        exc_info = ExceptionInfo(
            exception_type=exception_type,
            severity=severity,
            message=str(exception),
            timestamp=datetime.now().isoformat(),
            agent_id=self.agent_id,
            phase=phase or self.current_phase,
            context=context or {},
            stack_trace=traceback.format_exc(),
            exception_class=type(exception).__name__
        )
        
        self._current_exception = exc_info
        
        if self._global_exception_handler:
            self._global_exception_handler(exception, exc_info)
        
        handler = self._exception_handlers.get(exception_type)
        if handler:
            return handler(exc_info)
        
        return False, f"未找到异常处理器: {exception_type.value}"
    
    def _handle_retryable(self, exc_info: ExceptionInfo) -> Tuple[bool, str]:
        """处理可重试异常。"""
        max_retries = self.DEFAULT_MAX_RETRIES
        
        if exc_info.recovery_attempts < max_retries:
            exc_info.recovery_attempts += 1
            delay = self.DEFAULT_RETRY_DELAY * (2 ** (exc_info.recovery_attempts - 1))
            
            logger.warning(
                f"可重试异常 (尝试 {exc_info.recovery_attempts}/{max_retries}): "
                f"{exc_info.message}, {delay}秒后重试"
            )
            
            time.sleep(delay)
            
            self._notify_exception(exc_info)
            
            return True, f"准备重试 ({exc_info.recovery_attempts}/{max_retries})"
        else:
            logger.error(f"可重试异常达到最大重试次数: {exc_info.message}")
            self._save_crash_log(exc_info)
            return False, "达到最大重试次数，需要手动干预"
    
    def _handle_recoverable(self, exc_info: ExceptionInfo) -> Tuple[bool, str]:
        """处理可恢复异常。"""
        logger.warning(f"可恢复异常: {exc_info.message}")
        
        self._save_crash_log(exc_info)
        
        recovery_success = self._attempt_recovery(exc_info)
        
        if recovery_success:
            self._notify_exception(exc_info)
            return True, "已恢复"
        
        return False, "恢复失败，需要手动干预"
    
    def _handle_fatal(self, exc_info: ExceptionInfo) -> Tuple[bool, str]:
        """处理致命异常。"""
        logger.error(f"致命异常: {exc_info.message}")
        
        self._save_crash_log(exc_info)
        
        self._save_recovery_info(exc_info)
        
        self._notify_exception(exc_info)
        
        return False, "致命异常，需要手动干预"
    
    def _attempt_recovery(self, exc_info: ExceptionInfo) -> bool:
        """尝试恢复。"""
        try:
            state_file = Path("state/project_state.yaml")
            
            if state_file.exists():
                import yaml
                with open(state_file, 'r') as f:
                    state = yaml.safe_load(f)
                
                if state and 'state_version' in state:
                    state['state_version'] += 1
                    
                    with open(state_file, 'w') as f:
                        yaml.dump(state, f)
                    
                    logger.info("状态版本已递增，恢复成功")
                    return True
            
            return True
            
        except Exception as e:
            logger.error(f"恢复尝试失败: {e}")
            return False
    
    def _save_crash_log(self, exc_info: ExceptionInfo) -> str:
        """保存崩溃日志。"""
        crash_id = f"{self.agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        crash_info = CrashInfo(
            crash_id=crash_id,
            timestamp=exc_info.timestamp,
            agent_id=exc_info.agent_id,
            phase=exc_info.phase,
            last_action=exc_info.context.get("last_action", "unknown"),
            state_version=exc_info.context.get("state_version", 0),
            pending_tasks=exc_info.context.get("pending_tasks", []),
            exception_info=exc_info
        )
        
        crash_file = self.crash_log_dir / f"{crash_id}.json"
        
        with open(crash_file, 'w', encoding='utf-8') as f:
            json.dump({
                "crash_id": crash_info.crash_id,
                "timestamp": crash_info.timestamp,
                "agent_id": crash_info.agent_id,
                "phase": crash_info.phase,
                "last_action": crash_info.last_action,
                "state_version": crash_info.state_version,
                "pending_tasks": crash_info.pending_tasks,
                "exception": {
                    "type": exc_info.exception_type.value,
                    "severity": exc_info.severity.value,
                    "message": exc_info.message,
                    "class": exc_info.exception_class,
                    "stack_trace": exc_info.stack_trace,
                    "recovery_attempts": exc_info.recovery_attempts
                },
                "recovery_status": crash_info.recovery_status,
                "recovery_attempts": crash_info.recovery_attempts
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"崩溃日志已保存: {crash_file}")
        
        return crash_id
    
    def _save_recovery_info(self, exc_info: ExceptionInfo) -> None:
        """保存恢复信息。"""
        recovery_info = {
            "agent_id": self.agent_id,
            "phase": exc_info.phase,
            "timestamp": exc_info.timestamp,
            "exception": {
                "type": exc_info.exception_type.value,
                "message": exc_info.message
            },
            "required_action": "manual_intervention",
            "last_state": exc_info.context.get("state", {})
        }
        
        recovery_file = self.recovery_dir / f"{self.agent_id}_recovery.json"
        
        with open(recovery_file, 'w', encoding='utf-8') as f:
            json.dump(recovery_info, f, ensure_ascii=False, indent=2)
        
        logger.info(f"恢复信息已保存: {recovery_file}")
    
    def _notify_exception(self, exc_info: ExceptionInfo) -> None:
        """发送异常通知。"""
        for config in self._notification_configs:
            if not config.enabled:
                continue
            
            if exc_info.severity.value < config.min_severity.value:
                continue
            
            try:
                if config.channel == NotificationChannel.LOG:
                    self._notify_log(exc_info)
                elif config.channel == NotificationChannel.FILE:
                    self._notify_file(exc_info, config)
                elif config.channel == NotificationChannel.WEBHOOK:
                    self._notify_webhook(exc_info, config)
            except Exception as e:
                logger.error(f"通知发送失败: {e}")
    
    def _notify_log(self, exc_info: ExceptionInfo) -> None:
        """日志通知。"""
        log_method = logger.error if exc_info.severity == ExceptionSeverity.CRITICAL else logger.warning
        log_method(
            f"异常通知 - 类型: {exc_info.exception_type.value}, "
            f"严重程度: {exc_info.severity.name}, "
            f"消息: {exc_info.message}"
        )
    
    def _notify_file(self, exc_info: ExceptionInfo, config: NotificationConfig) -> None:
        """文件通知。"""
        notification_file = Path("state/notifications.log")
        with open(notification_file, 'a', encoding='utf-8') as f:
            f.write(
                f"[{exc_info.timestamp}] "
                f"[{exc_info.agent_id}] "
                f"[{exc_info.exception_type.value}] "
                f"{exc_info.message}\n"
            )
    
    def _notify_webhook(self, exc_info: ExceptionInfo, config: NotificationConfig) -> None:
        """Webhook通知。"""
        import requests
        
        if not config.webhook_url:
            return
        
        payload = {
            "event": "exception",
            "agent_id": exc_info.agent_id,
            "phase": exc_info.phase,
            "exception_type": exc_info.exception_type.value,
            "severity": exc_info.severity.name,
            "message": exc_info.message,
            "timestamp": exc_info.timestamp
        }
        
        try:
            requests.post(config.webhook_url, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"Webhook通知失败: {e}")
    
    def save_crash_context(self, state_version: int, pending_tasks: List[str]) -> None:
        """保存崩溃上下文。"""
        if self._current_exception:
            self._current_exception.context["state_version"] = state_version
            self._current_exception.context["pending_tasks"] = pending_tasks
    
    def get_crash_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取崩溃历史。"""
        crash_files = sorted(
            self.crash_log_dir.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:limit]
        
        crashes = []
        for crash_file in crash_files:
            try:
                with open(crash_file, 'r', encoding='utf-8') as f:
                    crash_data = json.load(f)
                    crashes.append(crash_data)
            except Exception as e:
                logger.warning(f"读取崩溃日志失败: {crash_file}, {e}")
        
        return crashes
    
    def clear_old_crashes(self, days: int = 7) -> int:
        """清理旧崩溃日志。"""
        import time
        
        cutoff = time.time() - (days * 24 * 60 * 60)
        removed = 0
        
        for crash_file in self.crash_log_dir.glob("*.json"):
            if crash_file.stat().st_mtime < cutoff:
                crash_file.unlink()
                removed += 1
        
        logger.info(f"已清理 {removed} 个旧崩溃日志")
        return removed
    
    def get_exception_summary(self) -> Dict[str, Any]:
        """获取异常处理器摘要。"""
        return {
            "agent_id": self.agent_id,
            "current_phase": self.current_phase,
            "registered_handlers": list(self._exception_handlers.keys()),
            "notification_channels": [c.channel.value for c in self._notification_configs],
            "current_exception": {
                "type": self._current_exception.exception_type.value if self._current_exception else None,
                "message": self._current_exception.message if self._current_exception else None,
                "severity": self._current_exception.severity.name if self._current_exception else None
            } if self._current_exception else None,
            "retry_count": self._retry_count,
            "crash_logs_count": len(list(self.crash_log_dir.glob("*.json")))
        }
    
    def set_phase(self, phase: str) -> None:
        """设置当前阶段。"""
        self.current_phase = phase
    
    def reset(self) -> None:
        """重置异常处理器。"""
        self._current_exception = None
        self._retry_count = 0
    
    def __enter__(self):
        """上下文管理器入口。"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口。"""
        if exc_type:
            self.handle_exception(exc_val)
        return False
