"""守护进程模块完整测试用例 - 优化版。"""
import os
import sys
import time
import tempfile
import shutil
import pytest
import subprocess
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestAgentDaemonComplete:
    """AgentDaemon 完整测试类。"""

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

    def test_daemon_is_running_false_when_process_dead(self, daemon):
        """测试进程死亡时不在运行。"""
        daemon.pid_file.write_text("99999")
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

    def test_daemon_cleanup_nonexistent_file(self, daemon):
        """测试清理不存在的 PID 文件。"""
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

    def test_daemon_daemonize_already_running(self, daemon):
        """测试进程已存在时处理。"""
        daemon.pid_file.parent.mkdir(parents=True, exist_ok=True)
        daemon.pid_file.write_text("99999")
        from src.core.daemon import ProcessExistsError
        with pytest.raises(ProcessExistsError):
            daemon.daemonize(lambda: None)

    def test_daemon_get_status_running(self, daemon, temp_dir):
        """测试获取运行状态。"""
        daemon._ensure_directories()
        daemon._write_pid()
        status = daemon.get_status()
        assert status["running"] is True
        assert status["pid"] == os.getpid()

    def test_daemon_get_status_with_log(self, daemon, temp_dir):
        """测试带日志的状态。"""
        daemon._ensure_directories()
        daemon._log("Test message")
        status = daemon.get_status()
        assert "log_lines" in status
        assert status["log_lines"] >= 1

    def test_daemon_pid_file_concurrent_access(self, temp_dir):
        """测试 PID 文件并发访问。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        config = DaemonConfig()
        daemon1 = AgentDaemon(temp_dir, config)
        daemon2 = AgentDaemon(temp_dir, config)
        
        daemon1._write_pid()
        assert daemon1.pid_file.exists()
        assert daemon2.get_running_pid() == os.getpid()

    def test_daemon_log_with_unicode(self, daemon, temp_dir):
        """测试日志记录特殊字符。"""
        daemon._ensure_directories()
        daemon._log("Test with unicode: 中文测试")
        content = daemon.log_file.read_text()
        assert "中文测试" in content


class TestProcessSupervisorComplete:
    """ProcessSupervisor 完整测试类。"""

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

    def test_supervisor_create_wrapper_script(self, temp_dir, supervisor):
        """测试 wrapper 脚本生成。"""
        def test_func():
            pass

        wrapper_path = supervisor._create_wrapper_script(test_func, (), {})
        
        assert Path(wrapper_path).exists()
        
        content = Path(wrapper_path).read_text()
        assert "oc-collab" in content
        assert "agent" in content

    def test_supervisor_create_wrapper_with_kwargs(self, temp_dir, supervisor):
        """测试带 kwargs 的 wrapper 生成。"""
        def test_func(path, interval):
            pass

        wrapper_path = supervisor._create_wrapper_script(
            test_func, (), {"interval": 60}
        )
        
        content = Path(wrapper_path).read_text()
        assert "--interval" in content
        assert "60" in content

    def test_supervisor_start_normal_exit(self, temp_dir):
        """测试正常退出的监管。"""
        from src.core.supervisor import ProcessSupervisor, SupervisorConfig
        
        config = SupervisorConfig(max_restarts=1, time_window=60, backoff_factor=1.0)
        supervisor = ProcessSupervisor(temp_dir, config)
        
        def test_func():
            return 0

        result = supervisor.start(test_func)
        assert result["success"] is True
        assert result["total_restarts"] == 0

    def test_supervisor_backoff_config(self, supervisor):
        """测试退避配置。"""
        assert supervisor.config.backoff_factor == 2.0
        assert supervisor.config.max_backoff == 60.0

    def test_supervisor_time_window_reset(self, supervisor):
        """测试时间窗口重置。"""
        supervisor.config.time_window = 1
        supervisor.restart_count = 5
        supervisor.last_restart = datetime.now()
        
        assert supervisor.should_start() is False
        
        time.sleep(1.1)
        assert supervisor.should_start() is True

    def test_supervisor_start_return_value(self, temp_dir):
        """测试 start 返回值完整验证。"""
        from src.core.supervisor import ProcessSupervisor, SupervisorConfig
        
        config = SupervisorConfig(max_restarts=1, time_window=60, backoff_factor=1.0)
        supervisor = ProcessSupervisor(temp_dir, config)
        
        def test_func():
            return 0

        result = supervisor.start(test_func)
        
        assert "success" in result
        assert "exits" in result
        assert "total_restarts" in result
        assert "uptime_seconds" in result
        assert "error" in result

    def test_supervisor_wrapper_execution(self, temp_dir):
        """测试 wrapper 脚本执行。"""
        from src.core.supervisor import ProcessSupervisor, SupervisorConfig
        
        config = SupervisorConfig(max_restarts=1, time_window=60, backoff_factor=1.0)
        supervisor = ProcessSupervisor(temp_dir, config)
        
        def test_func():
            print("Wrapper executed successfully")
            return 0

        wrapper_path = supervisor._create_wrapper_script(test_func, (), {})
        
        result = subprocess.run(
            [sys.executable, wrapper_path],
            capture_output=True,
            text=True,
            cwd=temp_dir,
            timeout=5
        )
        assert result.returncode == 0


class TestGitTimeoutComplete:
    """Git 超时控制完整测试类。"""

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

    def test_git_timeout_error_raising(self, temp_dir):
        """测试 GitTimeoutError 正确抛出。"""
        from src.core.git import GitHelper, GitTimeoutError
        
        helper = GitHelper(temp_dir)
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("git", 10)
            
            with pytest.raises(GitTimeoutError):
                helper._run_git_command("status", timeout=10)

    def test_git_timeouts_config_validation(self):
        """测试超时配置验证。"""
        from src.core.git import GitHelper
        
        custom_timeouts = {
            "status": 0.1,
            "add": 0.1,
            "commit": 0.1,
            "push": 0.1,
            "pull": 0.1
        }
        helper = GitHelper(".", timeouts=custom_timeouts)
        assert helper.timeouts["status"] == 0.1


class TestExceptionHandlingComplete:
    """异常处理完整测试类。"""

    def test_git_timeout_error_type(self):
        """测试 GitTimeoutError 类型。"""
        from src.core.git import GitTimeoutError, GitError
        
        assert issubclass(GitTimeoutError, GitError)
        error = GitTimeoutError("timeout")
        assert isinstance(error, Exception)

    def test_daemonize_error_type(self):
        """测试 DaemonizeError 类型。"""
        from src.core.daemon import DaemonizeError
        
        error = DaemonizeError("fork failed")
        assert isinstance(error, Exception)

    def test_process_exists_error_type(self):
        """测试 ProcessExistsError 类型。"""
        from src.core.daemon import ProcessExistsError
        
        error = ProcessExistsError("process exists")
        assert isinstance(error, Exception)

    def test_pid_file_write_failure(self, temp_dir):
        """测试 PID 文件写入失败处理。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        
        daemon = AgentDaemon(temp_dir, DaemonConfig(pid_file="/invalid/path/agent.pid"))
        
        with pytest.raises(Exception):
            daemon._write_pid()

    def test_git_not_installed_error(self):
        """测试 Git 未安装异常。"""
        from src.core.git import GitNotInstalledError, GitError
        
        assert issubclass(GitNotInstalledError, GitError)
        assert issubclass(GitNotInstalledError, Exception)


class TestIntegrationComplete:
    """集成测试完整测试类。"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)

    def test_full_supervise_workflow(self, temp_dir):
        """测试完整监管模式流程。"""
        from src.core.supervisor import ProcessSupervisor, SupervisorConfig
        
        config = SupervisorConfig(max_restarts=1, time_window=60, backoff_factor=1.0)
        supervisor = ProcessSupervisor(temp_dir, config)
        
        def test_func():
            return 0

        result = supervisor.start(test_func)
        
        assert result["success"] is True
        assert result["total_restarts"] == 0

    def test_daemon_and_supervisor_combination(self, temp_dir):
        """测试守护进程 + supervisor 组合。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        from src.core.supervisor import ProcessSupervisor, SupervisorConfig
        
        daemon_config = DaemonConfig(
            pid_file="test.pid",
            log_file="logs/test.log"
        )
        daemon = AgentDaemon(temp_dir, daemon_config)
        
        supervisor_config = SupervisorConfig(max_restarts=1, time_window=60)
        supervisor = ProcessSupervisor(temp_dir, supervisor_config)
        
        daemon._ensure_directories()
        
        assert not daemon.is_running()
        
        result = supervisor.start(lambda: 0)
        assert "total_restarts" in result


class TestLoggingComplete:
    """日志测试完整测试类。"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)

    def test_daemon_log_format(self, temp_dir):
        """测试日志格式正确性。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        
        config = DaemonConfig(log_file="logs/test.log")
        daemon = AgentDaemon(temp_dir, config)
        
        daemon._ensure_directories()
        daemon._log("Test message")
        
        content = daemon.log_file.read_text()
        lines = content.strip().split('\n')
        assert len(lines) == 1
        
        log_line = lines[0]
        assert "Test message" in log_line

    def test_daemon_log_multiline(self, temp_dir):
        """测试多行日志。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        
        config = DaemonConfig(log_file="logs/test.log")
        daemon = AgentDaemon(temp_dir, config)
        
        daemon._ensure_directories()
        for i in range(3):
            daemon._log(f"Message {i}")
        
        content = daemon.log_file.read_text()
        lines = content.strip().split('\n')
        assert len(lines) == 3

    def test_supervisor_log_output(self, temp_dir):
        """测试 Supervisor 日志输出。"""
        from src.core.supervisor import ProcessSupervisor, SupervisorConfig
        
        config = SupervisorConfig(max_restarts=1, time_window=60, backoff_factor=1.0)
        supervisor = ProcessSupervisor(temp_dir, config)
        
        supervisor._log("Test log message")
        
        assert supervisor.is_running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
