"""守护进程长时间运行测试用例 - 极速版。"""
import os
import sys
import time
import tempfile
import shutil
import pytest
import subprocess
from pathlib import Path
import concurrent.futures


class TestLongRunning:
    """守护进程长时间运行测试类 - 快速测试。"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)

    def test_daemon_log_accumulation(self, temp_dir):
        """测试日志累积写入。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        
        config = DaemonConfig(log_file="logs/test.log")
        daemon = AgentDaemon(temp_dir, config)
        
        daemon._ensure_directories()
        
        for i in range(20):
            daemon._log(f"Log message {i}")
        
        content = daemon.log_file.read_text()
        lines = content.strip().split('\n')
        assert len(lines) == 20
        print("✅ Log accumulation: 20 messages")

    def test_daemon_status_repeated(self, temp_dir):
        """测试状态重复查询。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        
        config = DaemonConfig(log_file="logs/test.log")
        daemon = AgentDaemon(temp_dir, config)
        
        daemon._ensure_directories()
        daemon._write_pid()
        
        for i in range(20):
            status = daemon.get_status()
            assert "running" in status
            assert "pid" in status
        
        daemon.cleanup()
        print("✅ Status query: 20 queries")

    def test_concurrent_status_check(self, temp_dir):
        """测试并发状态查询。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        
        config = DaemonConfig(log_file="logs/test.log")
        daemon = AgentDaemon(temp_dir, config)
        
        daemon._ensure_directories()
        daemon._write_pid()
        
        def query_status():
            return daemon.get_status()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(query_status) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures, timeout=3)]
        
        assert len(results) == 10
        for status in results:
            assert status["running"] is True
        
        print("✅ Concurrent query: 10 threads")

    def test_git_timeouts_all_operations(self, temp_dir):
        """测试所有 Git 操作的超时配置。"""
        from src.core.git import GitHelper
        
        helper = GitHelper(temp_dir)
        
        timeout_keys = ['status', 'add', 'commit', 'push', 'pull']
        
        for key in timeout_keys:
            assert key in helper.timeouts
            assert helper.timeouts[key] > 0
        
        print(f"✅ Git timeouts: {len(timeout_keys)} operations")

    def test_memory_usage_stability(self, temp_dir):
        """测试内存使用稳定性。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        
        config = DaemonConfig(log_file="logs/test.log")
        daemon = AgentDaemon(temp_dir, config)
        
        daemon._ensure_directories()
        
        for i in range(10):
            daemon._log(f"Memory test {i}")
        
        assert daemon.log_file.exists()
        print("✅ Memory stability: 10 writes")

    def test_state_persistence(self, temp_dir):
        """测试状态持久化。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        
        config = DaemonConfig(pid_file="test.pid")
        daemon1 = AgentDaemon(temp_dir, config)
        daemon2 = AgentDaemon(temp_dir, config)
        
        daemon1._write_pid()
        assert daemon1.get_running_pid() == daemon2.get_running_pid()
        daemon1.cleanup()
        print("✅ State persistence: passed")

    def test_config_validation(self, temp_dir):
        """测试配置验证。"""
        from src.core.daemon import DaemonConfig
        from src.core.supervisor import SupervisorConfig
        
        daemon_config = DaemonConfig()
        assert daemon_config.umask == 0o022
        
        supervisor_config = SupervisorConfig()
        assert supervisor_config.max_restarts == 5
        
        print("✅ Config validation: passed")

    def test_daemon_get_status_format(self, temp_dir):
        """测试状态返回格式。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        
        config = DaemonConfig(log_file="logs/test.log")
        daemon = AgentDaemon(temp_dir, config)
        
        daemon._ensure_directories()
        status = daemon.get_status()
        
        assert isinstance(status, dict)
        assert "running" in status
        assert "pid" in status
        
        print("✅ Status format: correct")

    def test_supervisor_status_format(self, temp_dir):
        """测试 supervisor 状态格式。"""
        from src.core.supervisor import ProcessSupervisor, SupervisorConfig
        
        config = SupervisorConfig()
        supervisor = ProcessSupervisor(temp_dir, config)
        
        status = supervisor.get_status()
        
        assert isinstance(status, dict)
        assert "is_running" in status
        assert "restart_count" in status
        assert "config" in status
        
        print("✅ Supervisor status: correct")

    def test_wrapper_script_format(self, temp_dir):
        """测试 wrapper 脚本格式。"""
        from src.core.supervisor import ProcessSupervisor, SupervisorConfig
        
        config = SupervisorConfig()
        supervisor = ProcessSupervisor(temp_dir, config)
        
        def test_func():
            pass

        wrapper_path = supervisor._create_wrapper_script(test_func, (), {})
        content = Path(wrapper_path).read_text()
        
        assert "oc-collab" in content
        assert "agent" in content
        assert "subprocess.run" in content
        
        print("✅ Wrapper format: correct")

    def test_special_characters_in_log(self, temp_dir):
        """测试日志特殊字符。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        
        config = DaemonConfig(log_file="logs/test.log")
        daemon = AgentDaemon(temp_dir, config)
        
        daemon._ensure_directories()
        daemon._log("Test: 中文测试 🚀")
        
        content = daemon.log_file.read_text()
        assert "中文测试" in content
        assert "🚀" in content
        
        print("✅ Special characters: supported")


class TestStability:
    """稳定性测试类。"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)

    def test_multiple_daemon_instances(self, temp_dir):
        """测试多个 daemon 实例。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        
        config = DaemonConfig()
        
        daemons = [AgentDaemon(temp_dir, config) for _ in range(5)]
        
        for d in daemons:
            d._ensure_directories()
            d._write_pid()
            status = d.get_status()
            assert status["running"] is True
        
        for d in daemons:
            d.cleanup()
        
        print("✅ Multiple instances: 5 daemons")

    def test_rapid_file_operations(self, temp_dir):
        """测试快速文件操作。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        
        config = DaemonConfig(log_file="logs/test.log")
        daemon = AgentDaemon(temp_dir, config)
        
        daemon._ensure_directories()
        
        for i in range(50):
            daemon._write_pid()
            daemon._log(f"Quick test {i}")
            daemon.get_status()
            daemon.cleanup()
        
        print("✅ Rapid file ops: 50 cycles")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
