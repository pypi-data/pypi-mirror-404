"""异常处理器单元测试。"""
import pytest
import sys
import os
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime


sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.exception_handler import (
    ExceptionHandler,
    ExceptionType,
    ExceptionSeverity,
    ExceptionInfo,
    CrashInfo,
    NotificationChannel,
    NotificationConfig,
    UnhandledExceptionError,
    RecoveryError,
)


class TestExceptionType:
    """异常类型测试类。"""

    def test_exception_type_values(self):
        """测试异常类型枚举值。"""
        assert ExceptionType.RETRYABLE.value == "retryable"
        assert ExceptionType.RECOVERABLE.value == "recoverable"
        assert ExceptionType.FATAL.value == "fatal"


class TestExceptionSeverity:
    """异常严重程度测试类。"""

    def test_severity_order(self):
        """测试严重程度顺序。"""
        assert ExceptionSeverity.LOW.value == 1
        assert ExceptionSeverity.MEDIUM.value == 2
        assert ExceptionSeverity.HIGH.value == 3
        assert ExceptionSeverity.CRITICAL.value == 4


class TestExceptionHandler:
    """异常处理器测试类。"""

    @pytest.fixture
    def handler(self, tmp_path):
        """创建异常处理器实例。"""
        handler = ExceptionHandler("test_agent", "test_phase")
        handler.crash_log_dir = tmp_path / "crash_logs"
        handler.recovery_dir = tmp_path / "recovery"
        handler.crash_log_dir.mkdir(parents=True, exist_ok=True)
        handler.recovery_dir.mkdir(parents=True, exist_ok=True)
        return handler

    def test_initialization(self, handler):
        """测试初始化。"""
        assert handler.agent_id == "test_agent"
        assert handler.current_phase == "test_phase"
        assert handler._current_exception is None
        assert handler._retry_count == 0

    def test_set_phase(self, handler):
        """测试设置阶段。"""
        handler.set_phase("new_phase")
        assert handler.current_phase == "new_phase"

    def test_reset(self, handler):
        """测试重置。"""
        handler._current_exception = MagicMock()
        handler._retry_count = 5
        handler.reset()
        assert handler._current_exception is None
        assert handler._retry_count == 0

    def test_get_exception_summary(self, handler):
        """测试获取摘要。"""
        summary = handler.get_exception_summary()
        assert summary["agent_id"] == "test_agent"
        assert summary["current_phase"] == "test_phase"
        assert "registered_handlers" in summary
        assert "notification_channels" in summary


class TestExceptionClassification:
    """异常分类测试类。"""

    @pytest.fixture
    def handler(self):
        """创建异常处理器实例。"""
        return ExceptionHandler("test_agent")

    def test_classify_network_error(self, handler):
        """测试分类网络错误。"""
        exc = Exception("network connection timeout")
        ex_type, severity = handler.classify_exception(exc)
        assert ex_type == ExceptionType.RETRYABLE
        assert severity == ExceptionSeverity.MEDIUM

    def test_classify_timeout_error(self, handler):
        """测试分类超时错误。"""
        exc = Exception("request timeout")
        ex_type, severity = handler.classify_exception(exc)
        assert ex_type == ExceptionType.RETRYABLE

    def test_classify_git_error(self, handler):
        """测试分类Git错误。"""
        exc = Exception("git fetch failed")
        ex_type, severity = handler.classify_exception(exc)
        assert ex_type == ExceptionType.RETRYABLE

    def test_classify_state_error(self, handler):
        """测试分类状态错误。"""
        exc = Exception("state version conflict")
        ex_type, severity = handler.classify_exception(exc)
        assert ex_type == ExceptionType.RECOVERABLE

    def test_classify_lock_error(self, handler):
        """测试分类锁错误。"""
        exc = Exception("lock acquisition failed")
        ex_type, severity = handler.classify_exception(exc)
        assert ex_type == ExceptionType.RECOVERABLE

    def test_classify_parse_error(self, handler):
        """测试分类解析错误。"""
        exc = Exception("yaml parse error")
        ex_type, severity = handler.classify_exception(exc)
        assert ex_type == ExceptionType.RECOVERABLE
        assert severity == ExceptionSeverity.HIGH

    def test_classify_permission_error(self, handler):
        """测试分类权限错误。"""
        exc = Exception("permission denied")
        ex_type, severity = handler.classify_exception(exc)
        assert ex_type == ExceptionType.FATAL

    def test_classify_disk_error(self, handler):
        """测试分类磁盘错误。"""
        exc = Exception("disk full")
        ex_type, severity = handler.classify_exception(exc)
        assert ex_type == ExceptionType.FATAL

    def test_classify_keyboard_interrupt(self, handler):
        """测试分类键盘中断。"""
        exc = KeyboardInterrupt()
        ex_type, severity = handler.classify_exception(exc)
        assert ex_type == ExceptionType.FATAL

    def test_classify_memory_error(self, handler):
        """测试分类内存错误。"""
        exc = Exception("memory allocation failed")
        ex_type, severity = handler.classify_exception(exc)
        assert ex_type == ExceptionType.FATAL

    def test_classify_unknown_error(self, handler):
        """测试分类未知错误。"""
        exc = Exception("some unknown error")
        ex_type, severity = handler.classify_exception(exc)
        assert ex_type == ExceptionType.RECOVERABLE
        assert severity == ExceptionSeverity.MEDIUM

    def test_classify_git_not_found(self, handler):
        """测试分类Git未找到。"""
        exc = Exception("git not found")
        ex_type, severity = handler.classify_exception(exc)
        assert ex_type == ExceptionType.FATAL


class TestRetryableExceptionHandling:
    """可重试异常处理测试类。"""

    @pytest.fixture
    def handler(self, tmp_path):
        """创建异常处理器实例。"""
        handler = ExceptionHandler("test_agent", "test_phase")
        handler.crash_log_dir = tmp_path / "crash_logs"
        handler.recovery_dir = tmp_path / "recovery"
        handler.crash_log_dir.mkdir(parents=True, exist_ok=True)
        handler.recovery_dir.mkdir(parents=True, exist_ok=True)
        return handler

    @patch('time.sleep')
    def test_retryable_first_attempt(self, mock_sleep, handler):
        """测试可重试异常首次尝试。"""
        exc = Exception("network connection timeout")
        handler._retry_count = 0

        with patch.object(handler, '_notify_exception'):
            success, message = handler._handle_retryable(
                ExceptionInfo(
                    exception_type=ExceptionType.RETRYABLE,
                    severity=ExceptionSeverity.MEDIUM,
                    message="network connection timeout",
                    timestamp=datetime.now().isoformat(),
                    agent_id="test_agent",
                    phase="test_phase",
                    context={},
                    recovery_attempts=1
                )
            )

        assert success
        assert "准备重试" in message
        mock_sleep.assert_called_once_with(5)

    @patch('time.sleep')
    def test_retryable_exponential_backoff(self, mock_sleep, handler):
        """测试可重试异常指数退避。"""
        with patch.object(handler, '_notify_exception'):
            for attempt in range(1, 4):
                success, message = handler._handle_retryable(
                    ExceptionInfo(
                        exception_type=ExceptionType.RETRYABLE,
                        severity=ExceptionSeverity.MEDIUM,
                        message="network error",
                        timestamp=datetime.now().isoformat(),
                        agent_id="test_agent",
                        phase="test_phase",
                        context={},
                        recovery_attempts=attempt
                    )
                )
                expected_delay = 5 * (2 ** (attempt - 1))
                mock_sleep.assert_called_with(expected_delay)

    @patch('time.sleep')
    def test_retryable_max_retries_exceeded(self, mock_sleep, handler):
        """测试可重试异常超过最大重试次数。"""
        with patch.object(handler, '_save_crash_log') as mock_save:
            mock_save.return_value = "crash_id_123"
            success, message = handler._handle_retryable(
                ExceptionInfo(
                    exception_type=ExceptionType.RETRYABLE,
                    severity=ExceptionSeverity.MEDIUM,
                    message="network error",
                    timestamp=datetime.now().isoformat(),
                    agent_id="test_agent",
                    phase="test_phase",
                    context={},
                    recovery_attempts=3
                )
            )

        assert not success
        assert "达到最大重试次数" in message
        mock_save.assert_called_once()


class TestRecoverableExceptionHandling:
    """可恢复异常处理测试类。"""

    @pytest.fixture
    def handler(self, tmp_path):
        """创建异常处理器实例。"""
        handler = ExceptionHandler("test_agent", "test_phase")
        handler.crash_log_dir = tmp_path / "crash_logs"
        handler.recovery_dir = tmp_path / "recovery"
        handler.crash_log_dir.mkdir(parents=True, exist_ok=True)
        handler.recovery_dir.mkdir(parents=True, exist_ok=True)
        return handler

    def test_recoverable_saves_crash_log(self, handler):
        """测试可恢复异常保存崩溃日志。"""
        with patch.object(handler, '_save_crash_log') as mock_save:
            mock_save.return_value = "crash_id_123"
            with patch.object(handler, '_attempt_recovery') as mock_recover:
                mock_recover.return_value = True
                with patch.object(handler, '_notify_exception'):
                    success, message = handler._handle_recoverable(
                        ExceptionInfo(
                            exception_type=ExceptionType.RECOVERABLE,
                            severity=ExceptionSeverity.HIGH,
                            message="state version conflict",
                            timestamp=datetime.now().isoformat(),
                            agent_id="test_agent",
                            phase="test_phase",
                            context={},
                            recovery_attempts=0
                        )
                    )

        mock_save.assert_called_once()
        mock_recover.assert_called_once()

    def test_recoverable_success(self, handler):
        """测试可恢复异常恢复成功。"""
        with patch.object(handler, '_save_crash_log'):
            with patch.object(handler, '_attempt_recovery') as mock_recover:
                mock_recover.return_value = True
                with patch.object(handler, '_notify_exception'):
                    success, message = handler._handle_recoverable(
                        ExceptionInfo(
                            exception_type=ExceptionType.RECOVERABLE,
                            severity=ExceptionSeverity.HIGH,
                            message="state error",
                            timestamp=datetime.now().isoformat(),
                            agent_id="test_agent",
                            phase="test_phase",
                            context={},
                            recovery_attempts=0
                        )
                    )

        assert success
        assert "已恢复" in message

    def test_recoverable_failure(self, handler):
        """测试可恢复异常恢复失败。"""
        with patch.object(handler, '_save_crash_log'):
            with patch.object(handler, '_attempt_recovery') as mock_recover:
                mock_recover.return_value = False
                success, message = handler._handle_recoverable(
                    ExceptionInfo(
                        exception_type=ExceptionType.RECOVERABLE,
                        severity=ExceptionSeverity.HIGH,
                        message="state error",
                        timestamp=datetime.now().isoformat(),
                        agent_id="test_agent",
                        phase="test_phase",
                        context={},
                        recovery_attempts=0
                    )
                )

        assert not success
        assert "恢复失败" in message


class TestFatalExceptionHandling:
    """致命异常处理测试类。"""

    @pytest.fixture
    def handler(self, tmp_path):
        """创建异常处理器实例。"""
        handler = ExceptionHandler("test_agent", "test_phase")
        handler.crash_log_dir = tmp_path / "crash_logs"
        handler.recovery_dir = tmp_path / "recovery"
        handler.crash_log_dir.mkdir(parents=True, exist_ok=True)
        handler.recovery_dir.mkdir(parents=True, exist_ok=True)
        return handler

    def test_fatal_saves_crash_log_and_recovery_info(self, handler):
        """测试致命异常保存崩溃日志和恢复信息。"""
        with patch.object(handler, '_save_crash_log') as mock_crash:
            with patch.object(handler, '_save_recovery_info') as mock_recovery:
                with patch.object(handler, '_notify_exception'):
                    success, message = handler._handle_fatal(
                        ExceptionInfo(
                            exception_type=ExceptionType.FATAL,
                            severity=ExceptionSeverity.CRITICAL,
                            message="permission denied",
                            timestamp=datetime.now().isoformat(),
                            agent_id="test_agent",
                            phase="test_phase",
                            context={},
                            recovery_attempts=0
                        )
                    )

        mock_crash.assert_called_once()
        mock_recovery.assert_called_once()

    def test_fatal_returns_failure(self, handler):
        """测试致命异常返回失败。"""
        with patch.object(handler, '_save_crash_log'):
            with patch.object(handler, '_save_recovery_info'):
                with patch.object(handler, '_notify_exception'):
                    success, message = handler._handle_fatal(
                        ExceptionInfo(
                            exception_type=ExceptionType.FATAL,
                            severity=ExceptionSeverity.CRITICAL,
                            message="disk full",
                            timestamp=datetime.now().isoformat(),
                            agent_id="test_agent",
                            phase="test_phase",
                            context={},
                            recovery_attempts=0
                        )
                    )

        assert not success
        assert "致命异常" in message


class TestCrashLogSaving:
    """崩溃日志保存测试类。"""

    @pytest.fixture
    def handler(self, tmp_path):
        """创建异常处理器实例。"""
        handler = ExceptionHandler("test_agent", "test_phase")
        handler.crash_log_dir = tmp_path / "crash_logs"
        handler.recovery_dir = tmp_path / "recovery"
        handler.crash_log_dir.mkdir(parents=True, exist_ok=True)
        handler.recovery_dir.mkdir(parents=True, exist_ok=True)
        return handler

    def test_save_crash_log(self, handler, tmp_path):
        """测试保存崩溃日志。"""
        handler.crash_log_dir = tmp_path / "crash_logs"
        handler.crash_log_dir.mkdir(parents=True, exist_ok=True)

        exc_info = ExceptionInfo(
            exception_type=ExceptionType.RETRYABLE,
            severity=ExceptionSeverity.MEDIUM,
            message="network error",
            timestamp="2024-01-31T10:00:00",
            agent_id="test_agent",
            phase="test_phase",
            context={"state_version": 1, "pending_tasks": ["task1"]},
            stack_trace="traceback...",
            exception_class="NetworkError",
            recovery_attempts=2
        )

        crash_id = handler._save_crash_log(exc_info)

        assert crash_id.startswith("test_agent_")
        crash_file = handler.crash_log_dir / f"{crash_id}.json"
        assert crash_file.exists()

        with open(crash_file, 'r', encoding='utf-8') as f:
            crash_data = json.load(f)

        assert crash_data["agent_id"] == "test_agent"
        assert crash_data["phase"] == "test_phase"
        assert crash_data["exception"]["type"] == "retryable"
        assert crash_data["exception"]["message"] == "network error"
        assert crash_data["exception"]["recovery_attempts"] == 2


class TestRecoveryInfoSaving:
    """恢复信息保存测试类。"""

    @pytest.fixture
    def handler(self, tmp_path):
        """创建异常处理器实例。"""
        handler = ExceptionHandler("test_agent", "test_phase")
        handler.crash_log_dir = tmp_path / "crash_logs"
        handler.recovery_dir = tmp_path / "recovery"
        handler.crash_log_dir.mkdir(parents=True, exist_ok=True)
        handler.recovery_dir.mkdir(parents=True, exist_ok=True)
        return handler

    def test_save_recovery_info(self, handler, tmp_path):
        """测试保存恢复信息。"""
        handler.recovery_dir = tmp_path / "recovery"
        handler.recovery_dir.mkdir(parents=True, exist_ok=True)

        exc_info = ExceptionInfo(
            exception_type=ExceptionType.FATAL,
            severity=ExceptionSeverity.CRITICAL,
            message="permission denied",
            timestamp="2024-01-31T10:00:00",
            agent_id="test_agent",
            phase="test_phase",
            context={"state": {"version": 1}},
            recovery_attempts=0
        )

        handler._save_recovery_info(exc_info)

        recovery_file = handler.recovery_dir / "test_agent_recovery.json"
        assert recovery_file.exists()

        with open(recovery_file, 'r', encoding='utf-8') as f:
            recovery_data = json.load(f)

        assert recovery_data["agent_id"] == "test_agent"
        assert recovery_data["required_action"] == "manual_intervention"


class TestRecoveryMechanism:
    """恢复机制测试类。"""

    @pytest.fixture
    def handler(self, tmp_path):
        """创建异常处理器实例。"""
        handler = ExceptionHandler("test_agent", "test_phase")
        handler.crash_log_dir = tmp_path / "crash_logs"
        handler.recovery_dir = tmp_path / "recovery"
        handler.crash_log_dir.mkdir(parents=True, exist_ok=True)
        handler.recovery_dir.mkdir(parents=True, exist_ok=True)
        return handler

    def test_attempt_recovery_with_state_file(self, handler, tmp_path):
        """测试有状态文件时的恢复。"""
        import yaml

        state_file = tmp_path / "project_state.yaml"
        state_file.write_text(yaml.dump({"state_version": 5}))

        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', side_effect=lambda *args: open(state_file, *args)):
                with patch('yaml.safe_load', return_value={"state_version": 5}):
                    with patch('yaml.dump', return_value=""):
                        result = handler._attempt_recovery(
                            ExceptionInfo(
                                exception_type=ExceptionType.RECOVERABLE,
                                severity=ExceptionSeverity.HIGH,
                                message="state error",
                                timestamp=datetime.now().isoformat(),
                                agent_id="test_agent",
                                phase="test_phase",
                                context={},
                                recovery_attempts=0
                            )
                        )

    def test_attempt_recovery_no_state_file(self, handler, tmp_path):
        """测试无状态文件时的恢复。"""
        handler.crash_log_dir = tmp_path / "crash_logs"
        handler.recovery_dir = tmp_path / "recovery"
        handler.crash_log_dir.mkdir(parents=True, exist_ok=True)
        handler.recovery_dir.mkdir(parents=True, exist_ok=True)

        result = handler._attempt_recovery(
            ExceptionInfo(
                exception_type=ExceptionType.RECOVERABLE,
                severity=ExceptionSeverity.HIGH,
                message="state error",
                timestamp=datetime.now().isoformat(),
                agent_id="test_agent",
                phase="test_phase",
                context={},
                recovery_attempts=0
            )
        )


class TestNotificationSystem:
    """通知系统测试类。"""

    @pytest.fixture
    def handler(self, tmp_path):
        """创建异常处理器实例。"""
        handler = ExceptionHandler("test_agent", "test_phase")
        handler.crash_log_dir = tmp_path / "crash_logs"
        handler.recovery_dir = tmp_path / "recovery"
        handler.crash_log_dir.mkdir(parents=True, exist_ok=True)
        handler.recovery_dir.mkdir(parents=True, exist_ok=True)
        return handler

    def test_add_notification_config(self, handler):
        """测试添加通知配置。"""
        config = NotificationConfig(
            channel=NotificationChannel.LOG,
            enabled=True,
            min_severity=ExceptionSeverity.MEDIUM
        )
        handler.add_notification_config(config)

        assert len(handler._notification_configs) == 1
        assert handler._notification_configs[0].channel == NotificationChannel.LOG

    def test_notify_log(self, handler, caplog):
        """测试日志通知。"""
        handler.add_notification_config(
            NotificationConfig(
                channel=NotificationChannel.LOG,
                enabled=True,
                min_severity=ExceptionSeverity.LOW
            )
        )

        exc_info = ExceptionInfo(
            exception_type=ExceptionType.RETRYABLE,
            severity=ExceptionSeverity.MEDIUM,
            message="test error",
            timestamp=datetime.now().isoformat(),
            agent_id="test_agent",
            phase="test_phase",
            context={}
        )

        handler._notify_log(exc_info)

    def test_notify_file(self, handler, tmp_path):
        """测试文件通知。"""
        notification_file = tmp_path / "notifications.log"

        handler.add_notification_config(
            NotificationConfig(
                channel=NotificationChannel.FILE,
                enabled=True,
                min_severity=ExceptionSeverity.LOW
            )
        )

        exc_info = ExceptionInfo(
            exception_type=ExceptionType.RETRYABLE,
            severity=ExceptionSeverity.MEDIUM,
            message="test error",
            timestamp="2024-01-31T10:00:00",
            agent_id="test_agent",
            phase="test_phase",
            context={}
        )

        with patch('builtins.open', side_effect=lambda *args: open(notification_file, *args)):
            handler._notify_file(exc_info, handler._notification_configs[0])

    def test_severity_filter(self, handler):
        """测试严重程度过滤。"""
        handler.add_notification_config(
            NotificationConfig(
                channel=NotificationChannel.LOG,
                enabled=True,
                min_severity=ExceptionSeverity.CRITICAL
            )
        )

        low_severity_exc = ExceptionInfo(
            exception_type=ExceptionType.RETRYABLE,
            severity=ExceptionSeverity.LOW,
            message="low severity error",
            timestamp=datetime.now().isoformat(),
            agent_id="test_agent",
            phase="test_phase",
            context={}
        )

        handler._notify_exception(low_severity_exc)

    def test_disabled_notification(self, handler):
        """测试禁用通知。"""
        handler.add_notification_config(
            NotificationConfig(
                channel=NotificationChannel.LOG,
                enabled=False
            )
        )

        exc_info = ExceptionInfo(
            exception_type=ExceptionType.RETRYABLE,
            severity=ExceptionSeverity.MEDIUM,
            message="test error",
            timestamp=datetime.now().isoformat(),
            agent_id="test_agent",
            phase="test_phase",
            context={}
        )

        handler._notify_exception(exc_info)


class TestCrashHistory:
    """崩溃历史测试类。"""

    @pytest.fixture
    def handler(self, tmp_path):
        """创建异常处理器实例。"""
        handler = ExceptionHandler("test_agent", "test_phase")
        handler.crash_log_dir = tmp_path / "crash_logs"
        handler.recovery_dir = tmp_path / "recovery"
        handler.crash_log_dir.mkdir(parents=True, exist_ok=True)
        handler.recovery_dir.mkdir(parents=True, exist_ok=True)
        return handler

    def test_get_crash_history(self, handler, tmp_path):
        """测试获取崩溃历史。"""
        handler.crash_log_dir = tmp_path / "crash_logs"
        handler.crash_log_dir.mkdir(parents=True, exist_ok=True)

        for i in range(3):
            crash_file = handler.crash_log_dir / f"test_agent_20240131_{i}.json"
            with open(crash_file, 'w', encoding='utf-8') as f:
                json.dump({"crash_id": f"crash_{i}", "message": f"error {i}"}, f)

        history = handler.get_crash_history(limit=10)

        assert len(history) == 3

    def test_get_crash_history_with_limit(self, handler, tmp_path):
        """测试获取崩溃历史带限制。"""
        handler.crash_log_dir = tmp_path / "crash_logs"
        handler.crash_log_dir.mkdir(parents=True, exist_ok=True)

        for i in range(5):
            crash_file = handler.crash_log_dir / f"test_agent_20240131_{i}.json"
            with open(crash_file, 'w', encoding='utf-8') as f:
                json.dump({"crash_id": f"crash_{i}", "message": f"error {i}"}, f)

        history = handler.get_crash_history(limit=2)

        assert len(history) == 2

    def test_clear_old_crashes(self, handler, tmp_path):
        """测试清理旧崩溃日志。"""
        handler.crash_log_dir = tmp_path / "crash_logs"
        handler.crash_log_dir.mkdir(parents=True, exist_ok=True)

        old_crash = handler.crash_log_dir / "old_crash.json"
        with open(old_crash, 'w', encoding='utf-8') as f:
            json.dump({"crash_id": "old"}, f)

        removed = handler.clear_old_crashes(days=0)

        assert not old_crash.exists()


class TestContextManager:
    """上下文管理器测试类。"""

    def test_context_manager_success(self):
        """测试上下文管理器成功执行。"""
        with ExceptionHandler("test_agent") as handler:
            assert handler.agent_id == "test_agent"

    def test_context_manager_exception(self):
        """测试上下文管理器捕获异常。"""
        with ExceptionHandler("test_agent") as handler:
            raise ValueError("test error")

    def test_context_manager_no_exception(self):
        """测试上下文管理器无异常。"""
        with ExceptionHandler("test_agent") as handler:
            pass


class TestHandleException:
    """处理异常测试类。"""

    @pytest.fixture
    def handler(self, tmp_path):
        """创建异常处理器实例。"""
        handler = ExceptionHandler("test_agent", "test_phase")
        handler.crash_log_dir = tmp_path / "crash_logs"
        handler.recovery_dir = tmp_path / "recovery"
        handler.crash_log_dir.mkdir(parents=True, exist_ok=True)
        handler.recovery_dir.mkdir(parents=True, exist_ok=True)
        return handler

    def test_handle_exception_retryable(self, handler):
        """测试处理可重试异常。"""
        exc = Exception("network timeout")

        with patch.object(handler, '_handle_retryable') as mock_handle:
            mock_handle.return_value = (True, "retrying")
            success, message = handler.handle_exception(exc)

        mock_handle.assert_called_once()

    def test_handle_exception_recoverable(self, handler):
        """测试处理可恢复异常。"""
        exc = Exception("state version conflict")

        with patch.object(handler, '_handle_recoverable') as mock_handle:
            mock_handle.return_value = (True, "recovered")
            success, message = handler.handle_exception(exc)

        mock_handle.assert_called_once()

    def test_handle_exception_fatal(self, handler):
        """测试处理致命异常。"""
        exc = Exception("permission denied")

        with patch.object(handler, '_handle_fatal') as mock_handle:
            mock_handle.return_value = (False, "fatal error")
            success, message = handler.handle_exception(exc)

        mock_handle.assert_called_once()

    def test_handle_exception_with_context(self, handler):
        """测试处理异常时传递上下文。"""
        exc = Exception("network error")
        context = {"state_version": 5, "pending_tasks": ["task1"]}

        with patch.object(handler, '_handle_retryable') as mock_handle:
            mock_handle.return_value = (True, "retrying")
            handler.handle_exception(exc, context=context, phase="custom_phase")

        call_args = mock_handle.call_args[0][0]
        assert call_args.context == context
        assert call_info.phase == "custom_phase"

    def test_global_exception_handler(self, handler):
        """测试全局异常处理器。"""
        global_handler = MagicMock()
        handler.set_global_exception_handler(global_handler)

        exc = Exception("test error")
        handler.handle_exception(exc)

        global_handler.assert_called_once()


class TestSaveCrashContext:
    """保存崩溃上下文测试类。"""

    @pytest.fixture
    def handler(self, tmp_path):
        """创建异常处理器实例。"""
        handler = ExceptionHandler("test_agent", "test_phase")
        handler.crash_log_dir = tmp_path / "crash_logs"
        handler.recovery_dir = tmp_path / "recovery"
        handler.crash_log_dir.mkdir(parents=True, exist_ok=True)
        handler.recovery_dir.mkdir(parents=True, exist_ok=True)
        return handler

    def test_save_crash_context(self, handler):
        """测试保存崩溃上下文。"""
        handler._current_exception = ExceptionInfo(
            exception_type=ExceptionType.RETRYABLE,
            severity=ExceptionSeverity.MEDIUM,
            message="test",
            timestamp=datetime.now().isoformat(),
            agent_id="test_agent",
            phase="test_phase",
            context={},
            recovery_attempts=0
        )

        handler.save_crash_context(5, ["task1", "task2"])

        assert handler._current_exception.context["state_version"] == 5
        assert handler._current_exception.context["pending_tasks"] == ["task1", "task2"]

    def test_save_crash_context_no_current_exception(self, handler):
        """测试无当前异常时保存上下文。"""
        handler._current_exception = None
        handler.save_crash_context(5, ["task1"])


class TestExceptionHandlerRegistration:
    """异常处理器注册测试类。"""

    @pytest.fixture
    def handler(self, tmp_path):
        """创建异常处理器实例。"""
        handler = ExceptionHandler("test_agent", "test_phase")
        handler.crash_log_dir = tmp_path / "crash_logs"
        handler.recovery_dir = tmp_path / "recovery"
        handler.crash_log_dir.mkdir(parents=True, exist_ok=True)
        handler.recovery_dir.mkdir(parents=True, exist_ok=True)
        return handler

    def test_register_exception_handler(self, handler):
        """测试注册异常处理器。"""
        custom_handler = MagicMock(return_value=(True, "handled"))
        handler.register_exception_handler(ExceptionType.RETRYABLE, custom_handler)

        assert handler._exception_handlers[ExceptionType.RETRYABLE] == custom_handler

    def test_set_global_exception_handler(self, handler):
        """测试设置全局异常处理器。"""
        global_handler = MagicMock()
        handler.set_global_exception_handler(global_handler)

        assert handler._global_exception_handler == global_handler
