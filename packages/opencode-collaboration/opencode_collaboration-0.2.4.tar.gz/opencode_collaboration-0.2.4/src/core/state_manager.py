"""状态管理器模块。"""
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import time
import logging


logger = logging.getLogger(__name__)

from ..utils.yaml import load_yaml, save_yaml
from ..utils.date import get_current_time


class StateManagerError(Exception):
    """状态管理器异常基类。"""
    pass


class StateFileNotFoundError(StateManagerError):
    """状态文件不存在异常。"""
    pass


class StateValidationError(StateManagerError):
    """状态验证异常。"""
    pass


class StateConflictError(StateManagerError):
    """状态冲突异常。"""
    pass


class StateLockError(StateManagerError):
    """状态锁异常。"""
    pass


@dataclass
class StateLockInfo:
    """状态锁信息。"""
    lock_id: str
    version: int
    created_at: float
    owner: str = ""


class StateManager:
    """状态管理器。"""
    
    STATE_FILE = "state/project_state.yaml"
    STATE_LOCK_FILE = "state/.state_lock"
    STATE_HISTORY_DIR = "state/history"
    LOCK_TIMEOUT = 300
    
    def __init__(self, project_path: str, lock_owner: str = "system"):
        """初始化状态管理器。"""
        self.project_path = Path(project_path)
        self.state_file = self.project_path / self.STATE_FILE
        self.lock_file = self.project_path / self.STATE_LOCK_FILE
        self.history_dir = self.project_path / self.STATE_HISTORY_DIR
        self.lock_owner = lock_owner
        self._current_lock: Optional[StateLockInfo] = None
    
    def initialize_project(self, project_name: str, project_type: str) -> Dict[str, Any]:
        """初始化项目状态。"""
        state = {
            "version": "2.0.0",
            "project": {
                "name": project_name,
                "type": project_type,
                "created_at": get_current_time(),
                "updated_at": get_current_time()
            },
            "phase": "project_init",
            "state_version": 1,
            "agents": {
                "agent1": {"role": "产品经理", "current": True},
                "agent2": {"role": "开发", "current": False}
            },
            "requirements": {
                "version": "",
                "status": "pending",
                "pm_signoff": False,
                "dev_signoff": False,
                "review_cycles": 0
            },
            "design": {
                "version": "",
                "status": "pending",
                "pm_signoff": False,
                "dev_signoff": False
            },
            "test": {
                "version": "",
                "status": "pending",
                "blackbox_cases": 0,
                "whitebox_passed": 0,
                "blackbox_passed": 0
            },
            "development": {
                "status": "not_started",
                "branch": "",
                "last_updated": ""
            },
            "deployment": {
                "status": "pending",
                "version": "",
                "last_updated": ""
            },
            "history": [],
            "metadata": {
                "created_from": "project_init",
                "last_action": "",
                "error_count": 0
            }
        }
        self._write_state_file(state)
        self._ensure_history_dir()
        return state
    
    def _ensure_history_dir(self) -> None:
        """确保历史目录存在。"""
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def _read_lock_file(self) -> Optional[StateLockInfo]:
        """读取锁文件。"""
        if not self.lock_file.exists():
            return None
        
        try:
            lock_data = load_yaml(str(self.lock_file))
            return StateLockInfo(
                lock_id=lock_data.get("lock_id", ""),
                version=lock_data.get("version", 0),
                created_at=float(lock_data.get("created_at", 0)),
                owner=lock_data.get("owner", "")
            )
        except Exception:
            return None
    
    def _write_lock_file(self, lock_info: StateLockInfo) -> None:
        """写入锁文件。"""
        lock_data = {
            "lock_id": lock_info.lock_id,
            "version": lock_info.version,
            "created_at": lock_info.created_at,
            "owner": lock_info.owner
        }
        save_yaml(str(self.lock_file), lock_data)
    
    def acquire_lock(self, expected_version: Optional[int] = None) -> bool:
        """获取状态锁。"""
        current_lock = self._read_lock_file()
        
        if current_lock:
            if time.time() - current_lock.created_at > self.LOCK_TIMEOUT:
                logger.warning("锁已过期，强制释放")
                self._clear_lock()
            else:
                if expected_version is None or current_lock.version != expected_version:
                    return False
        
        lock_id = str(uuid.uuid4())
        version = self._get_state_version()
        
        new_lock = StateLockInfo(
            lock_id=lock_id,
            version=version,
            created_at=time.time(),
            owner=self.lock_owner
        )
        
        self._write_lock_file(new_lock)
        self._current_lock = new_lock
        return True
    
    def release_lock(self) -> bool:
        """释放状态锁。"""
        if self._current_lock:
            current_lock = self._read_lock_file()
            if current_lock and current_lock.lock_id == self._current_lock.lock_id:
                self._clear_lock()
                self._current_lock = None
                return True
        return False
    
    def _clear_lock(self) -> None:
        """清除锁文件。"""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except Exception as e:
            logger.warning(f"清除锁文件失败: {e}")
    
    def is_locked(self) -> bool:
        """检查是否被锁定。"""
        lock = self._read_lock_file()
        if not lock:
            return False
        if time.time() - lock.created_at > self.LOCK_TIMEOUT:
            self._clear_lock()
            return False
        return True
    
    def _get_state_version(self) -> int:
        """获取状态版本号。"""
        try:
            state = self._read_state_file()
            return state.get("state_version", 1)
        except StateFileNotFoundError:
            return 0
    
    def _increment_version(self) -> int:
        """递增状态版本号。"""
        state = self._read_state_file()
        current_version = state.get("state_version", 1)
        state["state_version"] = current_version + 1
        self._write_state_file(state)
        return state["state_version"]
    
    def _read_state_file(self) -> Dict[str, Any]:
        """读取状态文件。"""
        if not self.state_file.exists():
            raise StateFileNotFoundError(f"状态文件不存在: {self.state_file}")
        
        state = load_yaml(str(self.state_file))
        if not isinstance(state, dict):
            raise StateValidationError("状态文件格式错误")
        
        return state
    
    def _write_state_file(self, state: Dict[str, Any]) -> None:
        """写入状态文件。"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        save_yaml(str(self.state_file), state)
    
    def read_state(self) -> Dict[str, Any]:
        """读取状态。"""
        return self._read_state_file()
    
    def write_state(self, state: Dict[str, Any], action: str = "") -> bool:
        """写入状态（带版本检查）。"""
        try:
            current_state = self._read_state_file()
            current_version = current_state.get("state_version", 1)
            
            state["state_version"] = current_version + 1
            state["updated_at"] = get_current_time()
            if action:
                state["metadata"]["last_action"] = action
            
            self._write_state_file(state)
            return True
        except Exception as e:
            logger.error(f"写入状态失败: {e}")
            return False
    
    def transition_phase(self, from_phase: str, to_phase: str, agent_id: str, 
                        details: str = "") -> Tuple[bool, Dict[str, Any]]:
        """执行阶段转换（带乐观锁）。"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                state = self._read_state_file()
                
                if state.get("phase") != from_phase:
                    return False, {"error": f"当前阶段不是 {from_phase}"}
                
                version = state.get("state_version", 1)
                if not self.acquire_lock(version):
                    retry_count += 1
                    continue
                
                state["phase"] = to_phase
                state["state_version"] = version + 1
                state["updated_at"] = get_current_time()
                
                history_entry = {
                    "id": str(uuid.uuid4())[:8],
                    "timestamp": get_current_time(),
                    "action": "phase_transition",
                    "phase_from": from_phase,
                    "phase_to": to_phase,
                    "agent_id": agent_id,
                    "details": details or f"从 {from_phase} 转换到 {to_phase}"
                }
                
                history = state.get("history", [])
                history.insert(0, history_entry)
                state["history"] = history[:50]
                
                self._write_state_file(state)
                self.release_lock()
                
                return True, state
                
            except StateConflictError:
                retry_count += 1
                continue
            except Exception as e:
                self.release_lock()
                return False, {"error": str(e)}
        
        return False, {"error": "状态转换失败：多次版本冲突"}
    
    def add_history_entry(self, action: str, agent_id: str, details: str) -> None:
        """添加历史记录。"""
        try:
            state = self._read_state_file()
            
            history = state.get("history", [])
            history.insert(0, {
                "id": str(uuid.uuid4())[:8],
                "timestamp": get_current_time(),
                "action": action,
                "agent_id": agent_id,
                "details": details
            })
            
            state["history"] = history[:100]
            state["updated_at"] = get_current_time()
            
            self._write_state_file(state)
        except Exception as e:
            logger.error(f"添加历史记录失败: {e}")
    
    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取历史记录。"""
        try:
            state = self._read_state_file()
            return state.get("history", [])[:limit]
        except StateFileNotFoundError:
            return []
    
    def get_state_version(self) -> int:
        """获取当前状态版本。"""
        return self._get_state_version()
    
    def get_current_phase(self) -> str:
        """获取当前阶段。"""
        try:
            state = self._read_state_file()
            return state.get("phase", "unknown")
        except StateFileNotFoundError:
            return "not_initialized"
    
    def update_phase(self, phase: str) -> Dict[str, Any]:
        """更新当前阶段（兼容旧接口）。"""
        state = self._read_state_file()
        old_phase = state.get("phase", "")
        state["phase"] = phase
        state["updated_at"] = get_current_time()
        self._write_state_file(state)
        
        if old_phase != phase:
            self.add_history_entry(
                action="phase_update",
                agent_id="system",
                details=f"阶段从 {old_phase} 更新为 {phase}"
            )
        
        return state

    def init_state(self, project_name: str, project_type: str) -> Dict[str, Any]:
        """初始化状态文件（兼容旧接口）。"""
        return self.initialize_project(project_name, project_type)
    
    def load_state(self) -> Dict[str, Any]:
        """加载状态文件（兼容旧接口）。"""
        return self._read_state_file()
    
    def save_state(self, state: Dict[str, Any]) -> None:
        """保存状态文件（兼容旧接口）。"""
        self._write_state_file(state)
    
    def get_signoff_status(self, stage: str) -> Dict[str, Any]:
        """获取签署状态（兼容旧接口）。"""
        try:
            state = self._read_state_file()
            stage_data = state.get(stage, {})
            return {
                "pm_signoff": stage_data.get("pm_signoff", False),
                "dev_signoff": stage_data.get("dev_signoff", False)
            }
        except StateFileNotFoundError:
            return {"pm_signoff": False, "dev_signoff": False}
    
    def get_active_agent(self) -> str:
        """获取活跃Agent（兼容旧接口）。"""
        try:
            state = self._read_state_file()
            for agent_id, agent_data in state.get("agents", {}).items():
                if agent_data.get("current", False):
                    return agent_id
            return "unknown"
        except StateFileNotFoundError:
            return "unknown"
    
    def set_active_agent(self, agent_id: str) -> Dict[str, Any]:
        """设置活跃Agent（兼容旧接口）。"""
        state = self._read_state_file()
        for id in state.get("agents", {}):
            state["agents"][id]["current"] = (id == agent_id)
        state["updated_at"] = get_current_time()
        self._write_state_file(state)
        return state
    
    def update_signoff(self, stage: str, agent: str, signed: bool, comment: str = "") -> Dict[str, Any]:
        """更新签署状态（兼容旧接口）。"""
        state = self._read_state_file()
        stage_data = state.get(stage, {})
        
        signoff_key = f"{agent}_signoff"
        date_key = f"{agent}_signoff_date"
        
        if signoff_key in stage_data:
            stage_data[signoff_key] = signed
        if date_key in stage_data:
            stage_data[date_key] = get_current_time() if signed else ""
        
        state["updated_at"] = get_current_time()
        self._write_state_file(state)
        return state
    
    def add_history(self, action: str, agent: str, details: str) -> None:
        """添加协作历史记录（兼容旧接口）。"""
        self.add_history_entry(action, agent, details)
    
    def increment_review_cycle(self) -> None:
        """增加评审轮次（兼容旧接口）。"""
        state = self._read_state_file()
        current = state.get("requirements", {}).get("review_cycles", 0)
        state["requirements"]["review_cycles"] = current + 1
        state["updated_at"] = get_current_time()
        self._write_state_file(state)
    
    def can_proceed_to_next_phase(self) -> bool:
        """检查是否可以推进到下一阶段（兼容旧接口）。"""
        try:
            state = self._read_state_file()
            phase = state.get("phase", "")
            
            if phase == "requirements_review":
                req = state.get("requirements", {})
                return req.get("pm_signoff", False) and req.get("dev_signoff", False)
            elif phase == "design_review":
                design = state.get("design", {})
                return design.get("pm_signoff", False) and design.get("dev_signoff", False)
            
            return False
        except StateFileNotFoundError:
            return False
    
    def update_requirements_version(self, version: str) -> None:
        """更新需求版本号（兼容旧接口）。"""
        state = self._read_state_file()
        state["requirements"]["version"] = version
        state["requirements"]["status"] = "draft"
        state["updated_at"] = get_current_time()
        self._write_state_file(state)
    
    def update_design_version(self, version: str) -> None:
        """更新设计版本号（兼容旧接口）。"""
        state = self._read_state_file()
        state["design"]["version"] = version
        state["design"]["status"] = "draft"
        state["updated_at"] = get_current_time()
        self._write_state_file(state)