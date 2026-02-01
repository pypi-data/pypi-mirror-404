"""Agent主模块。"""
import signal
import sys
import threading
import time
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


logger = logging.getLogger(__name__)


class AgentMode(Enum):
    """Agent运行模式。"""
    MANUAL = "manual"
    AUTO = "auto"


class AgentStatus(Enum):
    """Agent状态枚举。"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class AgentConfig:
    """Agent配置。"""
    agent_id: str = "agent1"
    agent_type: str = "产品经理"
    mode: AgentMode = AgentMode.AUTO
    polling_interval: int = 30
    max_retries: int = 3
    auto_retry: bool = True
    enable_webhook: bool = False


class Agent:
    """Agent主类。"""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化Agent。"""
        self.config = config or AgentConfig()
        self.state_machine = None
        self.brain_engine = None
        self.task_executor = None
        self.git_monitor = None
        
        self.status = AgentStatus.IDLE
        self.current_phase: str = "project_init"
        self._running = False
        self._paused = False
        self._main_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def initialize(self, project_path: str, state_manager=None) -> None:
        """初始化Agent组件。"""
        from ..core.state_machine import StateMachine, State
        from ..core.brain_engine import BrainEngine
        from ..core.task_executor import TaskExecutor
        from ..core.git_monitor import GitMonitor, GitConfig
        
        self.state_machine = StateMachine(State.PROJECT_INIT)
        self.brain_engine = BrainEngine()
        self.task_executor = TaskExecutor()
        
        try:
            git_config = GitConfig(polling_interval=self.config.polling_interval)
            self.git_monitor = GitMonitor(project_path, git_config)
        except Exception as e:
            logger.warning(f"Git监控器初始化失败: {e}")
            self.git_monitor = None
        
        self.current_phase = "project_init"
        logger.info(f"Agent {self.config.agent_id} 初始化完成")
    
    def start(self) -> None:
        """启动Agent。"""
        if self.status == AgentStatus.RUNNING:
            logger.warning("Agent已在运行中")
            return
        
        with self._lock:
            self._running = True
            self.status = AgentStatus.RUNNING
        
        self._main_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._main_thread.start()
        
        logger.info(f"Agent {self.config.agent_id} 已启动")
    
    def stop(self) -> None:
        """停止Agent。"""
        with self._lock:
            if not self._running:
                return
            self._running = False
        
        if self.git_monitor:
            self.git_monitor.stop_monitoring()
        
        if self._main_thread:
            self._main_thread.join(timeout=5)
        
        self.status = AgentStatus.STOPPED
        logger.info(f"Agent {self.config.agent_id} 已停止")
    
    def pause(self) -> None:
        """暂停Agent。"""
        with self._lock:
            self._paused = True
            self.status = AgentStatus.PAUSED
        
        if self.git_monitor:
            self.git_monitor.stop_monitoring()
        
        logger.info(f"Agent {self.config.agent_id} 已暂停")
    
    def resume(self) -> None:
        """恢复Agent。"""
        with self._lock:
            self._paused = False
            self.status = AgentStatus.RUNNING
        
        if self.git_monitor:
            self.git_monitor.start_monitoring()
        
        logger.info(f"Agent {self.config.agent_id} 已恢复")
    
    def _run_loop(self) -> None:
        """主循环。"""
        while self._running:
            try:
                if self._paused:
                    time.sleep(1)
                    continue
                
                self._execute_cycle()
                
                time.sleep(1)
            except Exception as e:
                logger.error(f"执行循环错误: {e}")
                self.status = AgentStatus.ERROR
                self._notify_event("error", {"error": str(e)})
    
    def _execute_cycle(self) -> None:
        """执行一个工作周期。"""
        phase = self.state_machine.current_state.value if self.state_machine else self.current_phase
        
        context = {
            "agent_id": self.config.agent_id,
            "agent_type": self.config.agent_type,
            "phase": phase,
            "project_path": getattr(self, '_project_path', '.')
        }
        
        action, rule = self.brain_engine.get_action(
            agent_type=self.config.agent_type.lower().replace(" ", "_"),
            phase=phase
        )
        
        if action and action.value != "wait":
            self._execute_action(action, context)
        
        self._notify_event("cycle_complete", {"phase": phase, "action": action.value if action else None})
    
    def _execute_action(self, action, context: Dict[str, Any]) -> None:
        """执行动作。"""
        logger.info(f"Agent {self.config.agent_id} 执行动作: {action.value}")
        
        result = self.task_executor.execute_action(action.value, context)
        
        if result.success:
            logger.info(f"动作执行成功: {result.message}")
            self._notify_event("action_success", {"action": action.value, "result": result})
        else:
            logger.error(f"动作执行失败: {result.message}")
            self._notify_event("action_failed", {"action": action.value, "result": result})
    
    def _handle_shutdown(self, signum, frame) -> None:
        """处理关闭信号。"""
        logger.info(f"收到关闭信号: {signum}")
        self.stop()
        sys.exit(0)
    
    def on_event(self, event_type: str, handler: Callable) -> None:
        """注册事件处理器。"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def _notify_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """通知事件。"""
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"事件处理器执行失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态。"""
        phase = self.state_machine.current_state.value if self.state_machine else self.current_phase
        
        return {
            "agent_id": self.config.agent_id,
            "agent_type": self.config.agent_type,
            "status": self.status.value,
            "phase": phase,
            "mode": self.config.mode.value,
            "running": self._running,
            "paused": self._paused
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取Agent摘要。"""
        return {
            "config": {
                "agent_id": self.config.agent_id,
                "agent_type": self.config.agent_type,
                "mode": self.config.mode.value,
                "polling_interval": self.config.polling_interval
            },
            "status": self.get_status(),
            "brain_engine": self.brain_engine.get_summary() if self.brain_engine else None,
            "task_executor": self.task_executor.get_summary() if self.task_executor else None,
            "git_monitor": self.git_monitor.get_status_summary() if self.git_monitor else None
        }
    
    def switch_mode(self, mode: AgentMode) -> None:
        """切换运行模式。"""
        self.config.mode = mode
        logger.info(f"Agent {self.config.agent_id} 模式切换为: {mode.value}")
    
    def manual_action(self, action_name: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """手动执行动作。"""
        if self.config.mode != AgentMode.MANUAL:
            return {
                "success": False,
                "message": "当前不是手动模式，请先切换到手动模式"
            }
        
        context = {
            "agent_id": self.config.agent_id,
            "agent_type": self.config.agent_type,
            "phase": self.state_machine.current_state.value if self.state_machine else self.current_phase,
            "params": params or {}
        }
        
        result = self.task_executor.execute_action(action_name, context)
        
        return {
            "success": result.success,
            "message": result.message,
            "duration": result.duration,
            "files_created": result.files_created
        }
    
    def trigger_action(self, action_name: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """触发动作（自动模式下可用）。"""
        context = {
            "agent_id": self.config.agent_id,
            "agent_type": self.config.agent_type,
            "phase": self.state_machine.current_state.value if self.state_machine else self.current_phase,
            "params": params or {}
        }
        
        result = self.task_executor.execute_action(action_name, context)
        
        return {
            "success": result.success,
            "message": result.message,
            "duration": result.duration
        }
