"""状态机模块。"""
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class StateError(Exception):
    """状态机异常基类。"""
    pass


class InvalidStateError(StateError):
    """无效状态异常。"""
    pass


class InvalidTransitionError(StateError):
    """无效转换异常。"""
    pass


class TransitionBlockedError(StateError):
    """转换被阻止异常。"""
    pass


class State(Enum):
    """项目阶段状态枚举。"""
    PROJECT_INIT = "project_init"
    REQUIREMENTS_DRAFT = "requirements_draft"
    REQUIREMENTS_REVIEW = "requirements_review"
    REQUIREMENTS_APPROVED = "requirements_approved"
    DESIGN_DRAFT = "design_draft"
    DESIGN_REVIEW = "design_review"
    DESIGN_APPROVED = "design_approved"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    COMPLETED = "completed"
    PAUSED = "paused"


class EventType(Enum):
    """事件类型枚举。"""
    PHASE_CHANGE = "phase_change"
    SIGNOFF = "signoff"
    REVIEW_COMPLETE = "review_complete"
    CODE_COMMITTED = "code_committed"
    TEST_COMPLETE = "test_complete"
    DEPLOY_COMPLETE = "deploy_complete"
    ERROR = "error"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class TransitionCallback:
    """状态转换回调。"""
    on_enter: Optional[Callable[[State], None]] = None
    on_exit: Optional[Callable[[State], None]] = None
    on_transition: Optional[Callable[[State, State], None]] = None


@dataclass
class StateInfo:
    """状态信息。"""
    state: State
    name: str
    description: str
    is_terminal: bool = False
    callbacks: TransitionCallback = field(default_factory=TransitionCallback)


@dataclass
class Transition:
    """状态转换规则。"""
    from_state: State
    to_state: State
    event: EventType
    condition: Optional[Callable[[], bool]] = None
    action: Optional[Callable[[], None]] = None
    priority: int = 0


class StateMachine:
    """状态机。"""
    
    STATE_ORDER = [
        State.PROJECT_INIT,
        State.REQUIREMENTS_DRAFT,
        State.REQUIREMENTS_REVIEW,
        State.REQUIREMENTS_APPROVED,
        State.DESIGN_DRAFT,
        State.DESIGN_REVIEW,
        State.DESIGN_APPROVED,
        State.DEVELOPMENT,
        State.TESTING,
        State.DEPLOYMENT,
        State.COMPLETED
    ]
    
    TRANSITIONS = [
        Transition(State.PROJECT_INIT, State.REQUIREMENTS_DRAFT, EventType.PHASE_CHANGE),
        Transition(State.REQUIREMENTS_DRAFT, State.REQUIREMENTS_REVIEW, EventType.PHASE_CHANGE),
        Transition(State.REQUIREMENTS_REVIEW, State.REQUIREMENTS_APPROVED, EventType.SIGNOFF),
        Transition(State.REQUIREMENTS_REVIEW, State.REQUIREMENTS_DRAFT, EventType.REVIEW_COMPLETE),
        Transition(State.REQUIREMENTS_APPROVED, State.DESIGN_DRAFT, EventType.PHASE_CHANGE),
        Transition(State.DESIGN_DRAFT, State.DESIGN_REVIEW, EventType.PHASE_CHANGE),
        Transition(State.DESIGN_REVIEW, State.DESIGN_APPROVED, EventType.SIGNOFF),
        Transition(State.DESIGN_REVIEW, State.DESIGN_DRAFT, EventType.REVIEW_COMPLETE),
        Transition(State.DESIGN_APPROVED, State.DEVELOPMENT, EventType.PHASE_CHANGE),
        Transition(State.DEVELOPMENT, State.TESTING, EventType.CODE_COMMITTED),
        Transition(State.TESTING, State.DEPLOYMENT, EventType.TEST_COMPLETE),
        Transition(State.TESTING, State.DEVELOPMENT, EventType.ERROR),
        Transition(State.DEPLOYMENT, State.COMPLETED, EventType.DEPLOY_COMPLETE),
    ]
    
    STATE_INFO = {
        State.PROJECT_INIT: StateInfo(
            state=State.PROJECT_INIT,
            name="项目初始化",
            description="项目刚初始化，尚未开始任何工作",
            is_terminal=False
        ),
        State.REQUIREMENTS_DRAFT: StateInfo(
            state=State.REQUIREMENTS_DRAFT,
            name="需求草稿",
            description="正在编写需求文档",
            is_terminal=False
        ),
        State.REQUIREMENTS_REVIEW: StateInfo(
            state=State.REQUIREMENTS_REVIEW,
            name="需求评审",
            description="需求文档正在评审中",
            is_terminal=False
        ),
        State.REQUIREMENTS_APPROVED: StateInfo(
            state=State.REQUIREMENTS_APPROVED,
            name="需求已批准",
            description="需求文档已通过评审并批准",
            is_terminal=False
        ),
        State.DESIGN_DRAFT: StateInfo(
            state=State.DESIGN_DRAFT,
            name="设计草稿",
            description="正在编写详细设计文档",
            is_terminal=False
        ),
        State.DESIGN_REVIEW: StateInfo(
            state=State.DESIGN_REVIEW,
            name="设计评审",
            description="设计文档正在评审中",
            is_terminal=False
        ),
        State.DESIGN_APPROVED: StateInfo(
            state=State.DESIGN_APPROVED,
            name="设计已批准",
            description="设计文档已通过评审并批准",
            is_terminal=False
        ),
        State.DEVELOPMENT: StateInfo(
            state=State.DEVELOPMENT,
            name="开发中",
            description="正在进行代码开发",
            is_terminal=False
        ),
        State.TESTING: StateInfo(
            state=State.TESTING,
            name="测试中",
            description="正在进行测试",
            is_terminal=False
        ),
        State.DEPLOYMENT: StateInfo(
            state=State.DEPLOYMENT,
            name="部署中",
            description="正在进行部署",
            is_terminal=False
        ),
        State.COMPLETED: StateInfo(
            state=State.COMPLETED,
            name="已完成",
            description="项目已完成",
            is_terminal=True
        ),
        State.PAUSED: StateInfo(
            state=State.PAUSED,
            name="已暂停",
            description="项目已暂停",
            is_terminal=False
        )
    }
    
    def __init__(self, initial_state: State = State.PROJECT_INIT):
        """初始化状态机。"""
        self._current_state = initial_state
        self._history: List[Dict[str, Any]] = []
        self._callbacks: Dict[State, TransitionCallback] = {}
        self._transition_lock = False
        self._version = 1
    
    @property
    def current_state(self) -> State:
        """获取当前状态。"""
        return self._current_state
    
    @property
    def current_state_info(self) -> StateInfo:
        """获取当前状态信息。"""
        return self.STATE_INFO.get(self._current_state, StateInfo(
            state=self._current_state,
            name="未知",
            description="未知状态",
            is_terminal=False
        ))
    
    @property
    def history(self) -> List[Dict[str, Any]]:
        """获取状态历史。"""
        return self._history.copy()
    
    def get_state_index(self, state: State) -> int:
        """获取状态在顺序中的索引。"""
        try:
            return self.STATE_ORDER.index(state)
        except ValueError:
            return -1
    
    def get_progress(self) -> float:
        """获取项目进度（百分比）。"""
        current_index = self.get_state_index(self._current_state)
        if current_index < 0:
            return 0.0
        total = len(self.STATE_ORDER) - 1
        return (current_index / total) * 100 if total > 0 else 0.0
    
    def get_state_progress(self, state: State) -> Dict[str, Any]:
        """获取指定状态的进度信息。"""
        try:
            current_index = self.STATE_ORDER.index(state)
        except ValueError:
            return {"error": "未知的阶段"}
        
        total_phases = len(self.STATE_ORDER)
        completed_count = 0
        for s in self.STATE_ORDER[:current_index + 1]:
            if s == state:
                break
            completed_count += 1
        
        return {
            "state": state.value,
            "name": self.STATE_INFO[state].name,
            "progress_percentage": (current_index / (total_phases - 1)) * 100 if total_phases > 1 else 100,
            "current_step": current_index + 1,
            "total_steps": total_phases,
            "remaining_states": [s.value for s in self.STATE_ORDER[current_index + 1:]]
        }
    
    def get_all_states(self) -> List[State]:
        """获取所有状态。"""
        return list(State)
    
    def get_valid_transitions(self, state: Optional[State] = None) -> List[Transition]:
        """获取指定状态的所有有效转换。"""
        target_state = state or self._current_state
        return [t for t in self.TRANSITIONS if t.from_state == target_state]
    
    def can_transition(self, to_state: State, event: EventType = EventType.PHASE_CHANGE) -> bool:
        """检查是否可以从当前状态转换到目标状态。"""
        valid_transitions = self.get_valid_transitions()
        for t in valid_transitions:
            if t.to_state == to_state and t.event == event:
                if t.condition is None or t.condition():
                    return True
        return False
    
    def get_next_state(self, event: EventType = EventType.PHASE_CHANGE) -> Optional[State]:
        """获取给定事件下的下一个状态。"""
        valid_transitions = self.get_valid_transitions()
        matching_transitions = [t for t in valid_transitions if t.event == event]
        
        if not matching_transitions:
            return None
        
        for t in sorted(matching_transitions, key=lambda x: -x.priority):
            if t.condition is None or t.condition():
                return t.to_state
        
        return None
    
    def register_callback(self, state: State, callback: TransitionCallback) -> None:
        """注册状态转换回调。"""
        self._callbacks[state] = callback
    
    def _execute_callback(self, state: State, callback_type: str) -> None:
        """执行回调函数。"""
        callback = self._callbacks.get(state)
        if callback:
            if callback_type == "on_enter" and callback.on_enter:
                callback.on_enter(state)
            elif callback_type == "on_exit" and callback.on_exit:
                callback.on_exit(state)
            elif callback_type == "on_transition" and callback.on_transition:
                callback.on_transition(self._current_state, state)
    
    def transition_to(self, to_state: State, event: EventType = EventType.PHASE_CHANGE,
                      auto: bool = False) -> Dict[str, Any]:
        """执行状态转换。"""
        if self._transition_lock:
            raise TransitionBlockedError("状态转换被阻止：当前正在执行其他转换")
        
        if self._current_state == to_state:
            return {
                "success": True,
                "from": self._current_state.value,
                "to": to_state.value,
                "message": "已经是目标状态"
            }
        
        if not self.can_transition(to_state, event):
            valid_transitions = self.get_valid_transitions()
            valid_targets = [t.to_state.value for t in valid_transitions]
            raise InvalidTransitionError(
                f"无法从 {self._current_state.value} 转换到 {to_state.value}，"
                f"有效转换目标: {valid_targets}"
            )
        
        self._transition_lock = True
        try:
            from_state = self._current_state
            
            self._execute_callback(from_state, "on_exit")
            
            transition = next(
                (t for t in self.TRANSITIONS
                 if t.from_state == from_state and t.to_state == to_state),
                None
            )
            if transition and transition.action:
                transition.action()
            
            self._current_state = to_state
            self._version += 1
            
            self._execute_callback(to_state, "on_enter")
            self._execute_callback(to_state, "on_transition")
            
            self._history.append({
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "from": from_state.value,
                "to": to_state.value,
                "event": event.value,
                "version": self._version
            })
            
            return {
                "success": True,
                "from": from_state.value,
                "to": to_state.value,
                "event": event.value,
                "version": self._version
            }
        finally:
            self._transition_lock = False
    
    def force_transition(self, to_state: State, reason: str = "强制转换") -> Dict[str, Any]:
        """强制执行状态转换（绕过有效性检查）。"""
        from_state = self._current_state
        
        self._history.append({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "from": from_state.value,
            "to": to_state.value,
            "event": "force_transition",
            "reason": reason,
            "version": self._version + 1
        })
        
        self._current_state = to_state
        self._version += 1
        
        return {
            "success": True,
            "from": from_state.value,
            "to": to_state.value,
            "forced": True,
            "reason": reason
        }
    
    def is_terminal_state(self) -> bool:
        """检查当前状态是否为终止状态。"""
        return self.current_state_info.is_terminal
    
    def is_completed(self) -> bool:
        """检查是否已完成。"""
        return self._current_state == State.COMPLETED
    
    def get_summary(self) -> Dict[str, Any]:
        """获取状态机摘要。"""
        return {
            "current_state": self._current_state.value,
            "current_state_name": self.current_state_info.name,
            "progress": self.get_progress(),
            "is_terminal": self.is_terminal_state(),
            "is_completed": self.is_completed(),
            "history_count": len(self._history),
            "version": self._version,
            "valid_transitions": [t.to_state.value for t in self.get_valid_transitions()]
        }
    
    def reset(self, state: State = State.PROJECT_INIT) -> None:
        """重置状态机。"""
        self._current_state = state
        self._history = []
        self._version = 1
    
    def get_state_by_name(self, name: str) -> Optional[State]:
        """根据状态名称获取状态枚举。"""
        for state in State:
            if state.value == name:
                return state
        return None
