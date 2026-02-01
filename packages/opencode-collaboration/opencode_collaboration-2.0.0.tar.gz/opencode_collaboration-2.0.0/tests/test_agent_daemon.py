"""守护进程模块单元测试。"""
import os
import sys
import time
import tempfile
import shutil
import pytest
from pathlib import Path
from datetime import datetime


class TestAgentDaemon:
    """AgentDaemon 单元测试类。"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def daemon(self, temp_dir):
        """创建 AgentDaemon 实例。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        config = DaemonConfig(
            pid_file="test_agent.pid",
            log_file="logs/test_daemon.log"
        )
        return AgentDaemon(temp_dir, config)

    def test_daemon_init(self, temp_dir, daemon):
        """测试初始化。"""
        assert daemon.project_path == Path(temp_dir)
        assert daemon.pid_file.name == "test_agent.pid"
        assert daemon.log_file.name == "test_daemon.log"

    def test_daemon_is_running_false_when_no_pid_file(self, daemon):
        """测试无 PID 文件时不在运行。"""
        assert daemon.is_running() is False

    def test_daemon_is_running_false_when_process_dead(self, daemon, temp_dir):
        """测试进程死亡时不在运行。"""
        pid_file = daemon.pid_file
        pid_file.write_text("99999")
        assert daemon.is_running() is False

    def test_daemon_get_running_pid_no_file(self, daemon):
        """测试无 PID 文件时返回 None。"""
        assert daemon.get_running_pid() is None

    def test_daemon_get_running_pid_invalid_content(self, daemon):
        """测试无效 PID 内容时返回 None。"""
        daemon.pid_file.write_text("not_a_number")
        assert daemon.get_running_pid() is None

    def test_daemon_write_pid(self, daemon):
        """测试写入 PID。"""
        daemon._write_pid()
        assert daemon.pid_file.exists()
        content = daemon.pid_file.read_text().strip()
        assert content == str(os.getpid())

    def test_daemon_cleanup(self, daemon):
        """测试清理。"""
        daemon._write_pid()
        assert daemon.pid_file.exists()
        daemon.cleanup()
        assert not daemon.pid_file.exists()

    def test_daemon_get_status_not_running(self, daemon):
        """测试获取状态（未运行）。"""
        status = daemon.get_status()
        assert status["running"] is False
        assert status["pid"] is None

    def test_daemon_log(self, daemon, temp_dir):
        """测试日志记录。"""
        daemon._ensure_directories()
        daemon._log("Test message")
        assert daemon.log_file.exists()
        content = daemon.log_file.read_text()
        assert "Test message" in content

    def test_daemon_stop_not_running(self, daemon):
        """测试停止未运行的守护进程。"""
        result = daemon.stop()
        assert result is False

    def test_daemon_config_defaults(self):
        """测试默认配置。"""
        from src.core.daemon import DaemonConfig
        config = DaemonConfig()
        assert config.pid_file == "state/agent.pid"
        assert config.log_file == "logs/agent_daemon.log"
        assert config.umask == 0o022

    def test_daemon_config_custom(self):
        """测试自定义配置。"""
        from src.core.daemon import DaemonConfig
        config = DaemonConfig(
            pid_file="custom.pid",
            log_file="custom.log",
            umask=0o077
        )
        assert config.pid_file == "custom.pid"
        assert config.log_file == "custom.log"
        assert config.umask == 0o077


class TestProcessSupervisor:
    """ProcessSupervisor 单元测试类。"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def supervisor(self, temp_dir):
        """创建 ProcessSupervisor 实例。"""
        from src.core.supervisor import ProcessSupervisor, SupervisorConfig
        config = SupervisorConfig(
            max_restarts=3,
            time_window=60,
            backoff_factor=2.0
        )
        return ProcessSupervisor(temp_dir, config)

    def test_supervisor_init(self, temp_dir, supervisor):
        """测试初始化。"""
        assert supervisor.project_path == Path(temp_dir)
        assert supervisor.config.max_restarts == 3
        assert supervisor.config.backoff_factor == 2.0
        assert supervisor.restart_count == 0
        assert supervisor.is_running is False

    def test_supervisor_should_start_true_when_no_restarts(self, supervisor):
        """测试无重启时可以启动。"""
        assert supervisor.should_start() is True

    def test_supervisor_should_start_false_when_exceeds_limit(self, supervisor):
        """测试超过限制时不能启动。"""
        supervisor.restart_count = 5
        assert supervisor.should_start() is False

    def test_supervisor_record_restart(self, supervisor):
        """测试记录重启。"""
        assert supervisor.last_restart is None
        supervisor._record_restart()
        assert supervisor.last_restart is not None

    def test_supervisor_get_status(self, supervisor):
        """测试获取状态。"""
        status = supervisor.get_status()
        assert "is_running" in status
        assert "restart_count" in status
        assert "config" in status
        assert status["config"]["max_restarts"] == 3

    def test_supervisor_stop_not_started(self, supervisor):
        """测试停止未启动的监管器。"""
        result = supervisor.stop()
        assert result is True

    def test_supervisor_config_defaults(self):
        """测试默认配置。"""
        from src.core.supervisor import SupervisorConfig
        config = SupervisorConfig()
        assert config.max_restarts == 5
        assert config.time_window == 3600
        assert config.backoff_factor == 2.0
        assert config.max_backoff == 60.0

    def test_supervisor_config_custom(self):
        """测试自定义配置。"""
        from src.core.supervisor import SupervisorConfig
        config = SupervisorConfig(
            max_restarts=10,
            time_window=7200,
            backoff_factor=1.5
        )
        assert config.max_restarts == 10
        assert config.time_window == 7200
        assert config.backoff_factor == 1.5


class TestGitTimeout:
    """Git 超时控制单元测试类。"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)

    def test_git_init_default_timeouts(self, temp_dir):
        """测试默认超时配置。"""
        from src.core.git import GitHelper
        helper = GitHelper(temp_dir)
        assert helper.timeouts["status"] == 10.0
        assert helper.timeouts["add"] == 5.0
        assert helper.timeouts["commit"] == 10.0
        assert helper.timeouts["push"] == 60.0
        assert helper.timeouts["pull"] == 30.0

    def test_git_init_custom_timeouts(self, temp_dir):
        """测试自定义超时配置。"""
        from src.core.git import GitHelper
        custom_timeouts = {
            "status": 5.0,
            "add": 2.0,
            "commit": 5.0,
            "push": 30.0,
            "pull": 15.0
        }
        helper = GitHelper(temp_dir, timeouts=custom_timeouts)
        assert helper.timeouts["status"] == 5.0
        assert helper.timeouts["add"] == 2.0

    def test_git_timeout_config_defaults(self):
        """测试默认超时配置类。"""
        from src.core.git import GitTimeoutConfig
        config = GitTimeoutConfig()
        assert config.status == 10.0
        assert config.add == 5.0
        assert config.commit == 10.0
        assert config.push == 60.0
        assert config.pull == 30.0

    def test_git_timeout_error_exists(self):
        """测试 GitTimeoutError 异常类存在。"""
        from src.core.git import GitTimeoutError
        error = GitTimeoutError("Test timeout error")
        assert str(error) == "Test timeout error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
