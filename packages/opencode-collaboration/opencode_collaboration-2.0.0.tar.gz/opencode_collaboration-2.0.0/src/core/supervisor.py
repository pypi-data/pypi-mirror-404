"""进程监管模块 - 实现自动重启机制。"""
import sys
import time
import signal
import subprocess
from pathlib import Path
from typing import Optional, Callable, Any, Dict
from datetime import datetime
from dataclasses import dataclass, field
import logging


logger = logging.getLogger(__name__)


@dataclass
class SupervisorConfig:
    """进程监管配置。"""
    max_restarts: int = 5
    time_window: int = 3600
    backoff_factor: float = 2.0
    max_backoff: float = 60.0
    initial_delay: float = 1.0


class ProcessSupervisor:
    """进程监管器 - 实现自动重启机制。"""

    def __init__(
        self,
        project_path: str,
        config: Optional[SupervisorConfig] = None
    ):
        """
        初始化进程监管器。

        Args:
            project_path: 项目路径
            config: 监管配置
        """
        self.project_path = Path(project_path)
        self.config = config or SupervisorConfig()

        self.restart_count: int = 0
        self.last_restart: Optional[datetime] = None
        self.process: Optional[subprocess.Popen] = None
        self.is_running: bool = False
        self.start_time: Optional[datetime] = None

    def start(
        self,
        main_func: Callable,
        *args: Any,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        启动监管进程。

        Args:
            main_func: 主函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Dict: 执行结果
        """
        self.is_running = True
        self.start_time = datetime.now()
        backoff = self.config.initial_delay
        total_restarts = 0

        result = {
            "success": False,
            "exits": 0,
            "total_restarts": 0,
            "uptime_seconds": 0,
            "error": None
        }

        self._log("监管进程启动")

        while self.is_running:
            if not self._should_start():
                self._log("超过最大重启次数，停止监管")
                result["error"] = "超过最大重启次数"
                break

            try:
                self._log(f"启动进程 (重试次数: {self.restart_count}, 退避: {backoff}s)")

                exit_code = self._run_process(main_func, args, kwargs)

                if exit_code == 0:
                    self._log("进程正常退出")
                    result["success"] = True
                    break
                else:
                    self._log(f"进程异常退出 (返回码: {exit_code})")
                    result["exits"] += 1

            except Exception as e:
                self._log(f"进程启动失败: {e}")
                result["error"] = str(e)

            if self._should_start():
                self._record_restart()
                time.sleep(backoff)
                backoff = min(
                    backoff * self.config.backoff_factor,
                    self.config.max_backoff
                )
                self.restart_count += 1
                total_restarts += 1
            else:
                self._log("超过最大重启次数，停止监管")
                result["error"] = "超过最大重启次数"
                break

        self.is_running = False
        if self.start_time:
            result["uptime_seconds"] = (datetime.now() - self.start_time).total_seconds()
        result["total_restarts"] = total_restarts

        self._log(f"监管进程退出 - 成功: {result['success']}, 重启: {total_restarts}")

        return result

    def stop(self, timeout: float = 10.0) -> bool:
        """停止监管。"""
        self.is_running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=timeout)
                return True
            except subprocess.TimeoutExpired:
                self.process.kill()
                return True
            except Exception:
                return False
        return True

    def should_start(self) -> bool:
        """检查是否应该启动进程。"""
        return self._should_start()

    def get_status(self) -> Dict[str, Any]:
        """获取监管状态。"""
        return {
            "is_running": self.is_running,
            "restart_count": self.restart_count,
            "last_restart": self.last_restart.isoformat() if self.last_restart else None,
            "uptime_seconds": (
                (datetime.now() - self.start_time).total_seconds()
                if self.start_time else 0
            ),
            "config": {
                "max_restarts": self.config.max_restarts,
                "time_window": self.config.time_window,
                "backoff_factor": self.config.backoff_factor
            }
        }

    def _should_start(self) -> bool:
        """检查是否应该启动进程。"""
        if self.last_restart:
            elapsed = (datetime.now() - self.last_restart).total_seconds()
            if elapsed > self.config.time_window:
                self.restart_count = 0

        return self.restart_count < self.config.max_restarts

    def _record_restart(self) -> None:
        """记录重启。"""
        self.last_restart = datetime.now()

    def _run_process(
        self,
        main_func: Callable,
        args: tuple,
        kwargs: dict
    ) -> int:
        """运行进程。"""
        script = self._create_wrapper_script(main_func, args, kwargs)

        self.process = subprocess.Popen(
            [sys.executable, script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(self.project_path)
        )

        stdout, stderr = self.process.communicate()

        if stderr:
            try:
                stderr_text = stderr.decode('utf-8', errors='replace')
                if stderr_text.strip():
                    self._log(f"进程stderr: {stderr_text[:200]}")
            except Exception:
                pass

        return self.process.returncode

    def _create_wrapper_script(
        self,
        main_func: Callable,
        args: tuple,
        kwargs: dict
    ) -> str:
        """创建进程包装脚本。"""
        arg_list = ['oc-collab', 'agent']

        for k, v in kwargs.items():
            opt_name = f'--{k.replace("_", "-")}'
            arg_list.append(opt_name)
            if not isinstance(v, bool):
                arg_list.append(str(v))

        for a in args:
            arg_list.append(str(a))

        arg_lines = '\n'.join(f'args.append({repr(a)})' for a in arg_list)

        wrapper = f'''#!/usr/bin/env python3
import sys
import subprocess

args = []
{arg_lines}

sys.exit(subprocess.run(args).returncode)
'''
        wrapper_file = self.project_path / ".supervisor_wrapper.py"
        wrapper_file.write_text(wrapper)
        return str(wrapper_file)

    def _log(self, message: str) -> None:
        """记录日志。"""
        timestamp = datetime.now().isoformat()
        log_line = f"[{timestamp}] [Supervisor] {message}"
        logger.info(log_line)


def create_supervisor(project_path: str) -> ProcessSupervisor:
    """创建进程监管器实例的工厂函数。"""
    return ProcessSupervisor(project_path)
