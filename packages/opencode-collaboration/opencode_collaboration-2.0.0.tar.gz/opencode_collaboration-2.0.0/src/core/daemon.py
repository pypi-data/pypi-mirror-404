"""守护进程模块 - 实现后台运行模式。"""
import os
import sys
import signal
import time
from pathlib import Path
from typing import Optional, Callable, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass
class DaemonConfig:
    """守护进程配置。"""
    pid_file: str = "state/agent.pid"
    log_file: str = "logs/agent_daemon.log"
    work_dir: str = "."
    umask: int = 0o022


class DaemonizeError(Exception):
    """守护进程化异常。"""
    pass


class ProcessExistsError(Exception):
    """进程已存在异常。"""
    pass


class AgentDaemon:
    """守护进程管理器 - 实现后台运行模式。"""

    def __init__(self, project_path: str, config: Optional[DaemonConfig] = None):
        """
        初始化守护进程管理器。

        Args:
            project_path: 项目路径
            config: 守护进程配置
        """
        self.project_path = Path(project_path)
        self.config = config or DaemonConfig()
        self.config.work_dir = str(self.project_path)

        self.pid_file = self.project_path / self.config.pid_file
        self.log_file = self.project_path / self.config.log_file

    def daemonize(self, main_func: Callable, *args: Any, **kwargs: Any) -> int:
        """
        将进程转换为守护进程。

        Args:
            main_func: 主函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            int: 父进程返回子进程PID，子进程不返回

        Raises:
            ProcessExistsError: 进程已存在
            DaemonizeError: 守护进程化失败
        """
        if self.is_running():
            pid = self.get_running_pid()
            raise ProcessExistsError(f"Agent 已在运行 (PID: {pid})")

        self._ensure_directories()

        try:
            pid = os.fork()
            if pid > 0:
                return pid
        except OSError as e:
            raise DaemonizeError(f"Fork 失败: {e}")

        self._become_daemon()

        self._setup_signal_handlers()

        self._write_pid()

        self._run_main(main_func, args, kwargs)

    def is_running(self) -> bool:
        """检查是否正在运行。"""
        if not self.pid_file.exists():
            return False
        try:
            pid = self.get_running_pid()
            if pid is None:
                return False
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False

    def get_running_pid(self) -> Optional[int]:
        """获取运行中的 PID。"""
        if self.pid_file.exists():
            try:
                return int(self.pid_file.read_text().strip())
            except (ValueError, IOError):
                return None
        return None

    def stop(self, timeout: float = 10.0) -> bool:
        """停止守护进程。"""
        pid = self.get_running_pid()
        if pid is None:
            return False
        try:
            os.kill(pid, signal.SIGTERM)
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    os.kill(pid, 0)
                    time.sleep(0.1)
                except ProcessLookupError:
                    return True
            os.kill(pid, signal.SIGKILL)
            return True
        except ProcessLookupError:
            return True
        except PermissionError:
            return False

    def cleanup(self) -> None:
        """清理资源。"""
        if self.pid_file.exists():
            try:
                self.pid_file.unlink()
            except OSError:
                pass

    def get_status(self) -> dict:
        """获取守护进程状态。"""
        pid = self.get_running_pid()
        running = self.is_running()

        status = {
            "running": running,
            "pid": pid,
        }

        if running and self.log_file.exists():
            try:
                log_content = self.log_file.read_text()
                lines = log_content.strip().split('\n')
                status["last_log"] = lines[-1] if lines else None
                status["log_lines"] = len(lines)
            except OSError:
                pass

        return status

    def _ensure_directories(self) -> None:
        """确保必要的目录存在。"""
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _become_daemon(self) -> None:
        """成为守护进程。"""
        os.setsid()

        os.chdir(self.config.work_dir)

        os.umask(self.config.umask)

        sys.stdout.flush()
        sys.stderr.flush()

        with open('/dev/null', 'r') as devnull:
            os.dup2(devnull.fileno(), sys.stdin.fileno())
        with open(self.log_file, 'a+') as log_file:
            os.dup2(log_file.fileno(), sys.stdout.fileno())
            os.dup2(log_file.fileno(), sys.stderr.fileno())

    def _setup_signal_handlers(self) -> None:
        """设置信号处理器。"""
        signal.signal(signal.SIGTERM, self._handle_terminate)
        signal.signal(signal.SIGINT, self._handle_terminate)
        signal.signal(signal.SIGHUP, self._handle_terminate)

    def _handle_terminate(self, signum: int, frame) -> None:
        """处理终止信号。"""
        self._log(f"收到信号 {signum}，正在停止...")
        self.cleanup()
        sys.exit(0)

    def _write_pid(self) -> None:
        """写入 PID 文件。"""
        self.pid_file.write_text(str(os.getpid()))

    def _run_main(self, main_func: Callable, args: tuple, kwargs: dict) -> None:
        """运行主函数。"""
        try:
            self._log("守护进程启动")
            main_func(*args, **kwargs)
        except Exception as e:
            self._log(f"守护进程异常: {e}")
            raise
        finally:
            self._log("守护进程退出")
            self.cleanup()

    def _log(self, message: str) -> None:
        """写入日志。"""
        timestamp = datetime.now().isoformat()
        log_line = f"[{timestamp}] {message}\n"
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_line)
        except OSError:
            pass


def create_daemon(project_path: str) -> AgentDaemon:
    """创建守护进程实例的工厂函数。"""
    return AgentDaemon(project_path)
