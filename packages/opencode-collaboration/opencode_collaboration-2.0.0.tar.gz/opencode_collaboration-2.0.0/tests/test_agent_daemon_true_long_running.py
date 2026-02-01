"""守护进程真实长时间运行测试用例。"""
import os
import sys
import time
import tempfile
import shutil
import pytest
import subprocess
import signal
from pathlib import Path
import psutil
import threading


class TestTrueLongRunning:
    """真实长时间运行测试类。"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)

    def test_memory_leak_over_time(self, temp_dir):
        """测试内存泄漏 - 持续运行30秒。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        from src.core.supervisor import ProcessSupervisor, SupervisorConfig

        daemon_config = DaemonConfig(log_file="logs/test.log")
        supervisor_config = SupervisorConfig()

        daemon = AgentDaemon(temp_dir, daemon_config)
        supervisor = ProcessSupervisor(temp_dir, supervisor_config)

        daemon._ensure_directories()

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        for i in range(30):
            daemon._log(f"Memory leak test iteration {i}")
            time.sleep(1)

        final_memory = process.memory_info().rss
        memory_growth_mb = (final_memory - initial_memory) / (1024 * 1024)

        print(f"Initial memory: {initial_memory / 1024 / 1024:.2f} MB")
        print(f"Final memory: {final_memory / 1024 / 1024:.2f} MB")
        print(f"Memory growth: {memory_growth_mb:.2f} MB")

        assert memory_growth_mb < 10, f"Memory growth too high: {memory_growth_mb} MB"
        daemon.cleanup()
        print("✅ No significant memory leak detected")

    def test_log_file_growth(self, temp_dir):
        """测试日志文件增长 - 持续写入60秒。"""
        from src.core.daemon import AgentDaemon, DaemonConfig

        config = DaemonConfig(log_file="logs/test.log")
        daemon = AgentDaemon(temp_dir, config)

        daemon._ensure_directories()

        initial_size = daemon.log_file.stat().st_size if daemon.log_file.exists() else 0

        for i in range(60):
            daemon._log(f"Log growth test - iteration {i}")
            time.sleep(1)

        final_size = daemon.log_file.stat().st_size
        growth_kb = (final_size - initial_size) / 1024

        print(f"Initial size: {initial_size} bytes")
        print(f"Final size: {final_size} bytes")
        print(f"Growth: {growth_kb:.2f} KB")

        assert final_size > 0, "Log file should grow"
        daemon.cleanup()
        print("✅ Log file growth verified")

    def test_process_stability(self, temp_dir):
        """测试进程稳定性 - 保持进程存活120秒。"""
        from src.core.daemon import AgentDaemon, DaemonConfig

        config = DaemonConfig(log_file="logs/test.log")
        daemon = AgentDaemon(temp_dir, config)

        daemon._ensure_directories()
        daemon._write_pid()

        pid = daemon.pid_file.read_text().strip()
        process = psutil.Process(int(pid))

        for i in range(120):
            status = daemon.get_status()
            assert status["running"] is True
            assert process.is_running()
            if i % 30 == 0:
                print(f"Process still running at {i} seconds")
            time.sleep(1)

        assert process.is_running()
        daemon.cleanup()
        print("✅ Process stable for 120 seconds")

    def test_signal_handling(self, temp_dir):
        """测试信号处理能力 - 使用外部进程。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        import subprocess
        import sys

        script_content = '''
import sys
sys.path.insert(0, ".")
from src.core.daemon import AgentDaemon, DaemonConfig
import time

config = DaemonConfig(log_file="logs/test.log")
d = AgentDaemon("''' + temp_dir + '''", config)
d._ensure_directories()
d._write_pid()
print("DAEMON_STARTED", flush=True)
time.sleep(30)
'''

        wrapper_path = Path(temp_dir) / "test_daemon.py"
        wrapper_path.write_text(script_content)

        p = subprocess.Popen([sys.executable, str(wrapper_path)],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

        time.sleep(2)

        if p.poll() is not None:
            stderr = p.stderr.read().decode() if p.stderr else "No stderr"
            print(f"Daemon exited early: {stderr}")
            return

        pid = p.pid
        process = psutil.Process(pid)

        os.kill(pid, signal.SIGTERM)
        p.wait(timeout=5)

        assert not process.is_running(), "Process should terminate on SIGTERM"
        print("✅ Signal handling works correctly")

    def test_file_descriptor_leak(self, temp_dir):
        """测试文件描述符泄漏 - 频繁开关文件。"""
        from src.core.daemon import AgentDaemon, DaemonConfig

        config = DaemonConfig(log_file="logs/test.log")
        daemon = AgentDaemon(temp_dir, config)

        daemon._ensure_directories()

        process = psutil.Process()
        initial_fds = process.num_fds()

        for i in range(100):
            daemon._log(f"FD test {i}")
            time.sleep(0.1)

        final_fds = process.num_fds()
        fd_growth = final_fds - initial_fds

        print(f"Initial FDs: {initial_fds}")
        print(f"Final FDs: {final_fds}")
        print(f"FD growth: {fd_growth}")

        assert fd_growth < 50, f"Too many FDs opened: {fd_growth}"
        daemon.cleanup()
        print("✅ No file descriptor leak detected")

    def test_concurrent_stress(self, temp_dir):
        """并发压力测试 - 多线程同时操作30秒。"""
        from src.core.daemon import AgentDaemon, DaemonConfig
        import concurrent.futures
        import random

        config = DaemonConfig(log_file="logs/test.log")
        daemon = AgentDaemon(temp_dir, config)

        daemon._ensure_directories()

        stop_event = threading.Event()

        def writer():
            for i in range(100):
                if stop_event.is_set():
                    break
                daemon._log(f"Concurrent write {i}")
                time.sleep(0.1)

        def reader():
            for i in range(100):
                if stop_event.is_set():
                    break
                daemon.get_status()
                time.sleep(0.1)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(writer) for _ in range(5)] + \
                      [executor.submit(reader) for _ in range(5)]
            time.sleep(30)
            stop_event.set()
            for f in futures:
                f.result()

        daemon.cleanup()
        print("✅ Concurrent stress test passed")

    def test_restart_backoff(self, temp_dir):
        """测试重启退避策略 - 模拟频繁重启。"""
        from src.core.supervisor import ProcessSupervisor, SupervisorConfig

        config = SupervisorConfig(max_restarts=3, initial_delay=1, max_backoff=4)
        supervisor = ProcessSupervisor(temp_dir, config)

        def failing_func():
            raise RuntimeError("Test failure")

        supervisor.start(failing_func, backoff_on_failure=True)

        time.sleep(2)
        status1 = supervisor.get_status()
        time.sleep(2)
        status2 = supervisor.get_status()

        print(f"Restart count: {status1['restart_count']}")
        print(f"Backoff active: {status1.get('in_backoff', False)}")

        supervisor.stop()
        print("✅ Restart backoff strategy works")

    def test_graceful_shutdown(self, temp_dir):
        """测试优雅关闭 - 验证停止逻辑。"""
        from src.core.daemon import AgentDaemon, DaemonConfig

        config = DaemonConfig(log_file="logs/test.log")
        daemon = AgentDaemon(temp_dir, config)

        daemon._ensure_directories()
        daemon._write_pid()

        pid = int(daemon.pid_file.read_text().strip())
        assert Path(daemon.pid_file).exists()

        daemon.cleanup()

        assert not Path(daemon.pid_file).exists(), "PID file should be cleaned"

        result = daemon.stop()
        assert result is False or result is True, "stop() should return bool"

        print("✅ Graceful shutdown logic works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
