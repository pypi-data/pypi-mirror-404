"""状态机单元测试。"""
import pytest
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.state_machine import (
    StateMachine, State, EventType, StateInfo, Transition, TransitionCallback
)


class TestStateMachine:
    """状态机测试类。"""
    
    @pytest.fixture
    def state_machine(self):
        """创建状态机实例。"""
        return StateMachine(State.PROJECT_INIT)
    
    def test_initial_state(self, state_machine):
        """测试初始状态。"""
        assert state_machine.current_state == State.PROJECT_INIT
    
    def test_get_all_states(self, state_machine):
        """测试获取所有状态。"""
        states = state_machine.get_all_states()
        assert State.PROJECT_INIT in states
        assert State.COMPLETED in states
        assert len(states) == 12
    
    def test_get_state_index(self, state_machine):
        """测试获取状态索引。"""
        assert state_machine.get_state_index(State.PROJECT_INIT) == 0
        assert state_machine.get_state_index(State.COMPLETED) == 10
    
    def test_get_valid_transitions(self, state_machine):
        """测试获取有效转换。"""
        transitions = state_machine.get_valid_transitions(State.PROJECT_INIT)
        assert len(transitions) == 1
        assert transitions[0].to_state == State.REQUIREMENTS_DRAFT
    
    def test_can_transition_valid(self, state_machine):
        """测试合法状态转换。"""
        assert state_machine.can_transition(State.REQUIREMENTS_DRAFT, EventType.PHASE_CHANGE)
    
    def test_can_transition_invalid(self, state_machine):
        """测试非法状态转换。"""
        assert not state_machine.can_transition(State.DEVELOPMENT, EventType.PHASE_CHANGE)
    
    def test_transition_to(self, state_machine):
        """测试执行状态转换。"""
        result = state_machine.transition_to(State.REQUIREMENTS_DRAFT)
        
        assert result["success"]
        assert result["from"] == "project_init"
        assert result["to"] == "requirements_draft"
        assert state_machine.current_state == State.REQUIREMENTS_DRAFT
    
    def test_transition_to_invalid(self, state_machine):
        """测试非法状态转换。"""
        with pytest.raises(Exception):
            state_machine.transition_to(State.DEVELOPMENT)
    
    def test_get_next_state(self, state_machine):
        """测试获取下一状态。"""
        next_state = state_machine.get_next_state(EventType.PHASE_CHANGE)
        assert next_state == State.REQUIREMENTS_DRAFT
    
    def test_get_progress(self, state_machine):
        """测试获取进度。"""
        progress = state_machine.get_progress()
        assert progress == 0.0
        
        state_machine.transition_to(State.COMPLETED)
        progress = state_machine.get_progress()
        assert progress == 100.0
    
    def test_get_state_progress(self, state_machine):
        """测试获取状态进度信息。"""
        progress = state_machine.get_state_progress(State.PROJECT_INIT)
        
        assert progress["state"] == "project_init"
        assert progress["current_step"] == 1
        assert progress["total_steps"] == 11
        assert 0 <= progress["progress_percentage"] <= 100
    
    def test_is_terminal_state(self, state_machine):
        """测试终止状态。"""
        assert not state_machine.is_terminal_state()
        
        state_machine.transition_to(State.COMPLETED)
        assert state_machine.is_terminal_state()
    
    def test_is_completed(self, state_machine):
        """测试完成状态。"""
        assert not state_machine.is_completed()
        
        state_machine.transition_to(State.COMPLETED)
        assert state_machine.is_completed()
    
    def test_history(self, state_machine):
        """测试状态历史。"""
        assert len(state_machine.history) == 0
        
        state_machine.transition_to(State.REQUIREMENTS_DRAFT)
        
        assert len(state_machine.history) == 1
        history_item = state_machine.history[0]
        assert "from" in history_item
        assert "to" in history_item
        assert "timestamp" in history_item
    
    def test_register_callback(self, state_machine):
        """测试注册回调。"""
        callback = TransitionCallback(
            on_enter=lambda s: None,
            on_exit=lambda s: None
        )
        state_machine.register_callback(State.REQUIREMENTS_DRAFT, callback)
        
        assert State.REQUIREMENTS_DRAFT in state_machine._callbacks
    
    def test_force_transition(self, state_machine):
        """测试强制转换。"""
        result = state_machine.force_transition(State.COMPLETED, "测试强制转换")
        
        assert result["success"]
        assert result["forced"]
        assert state_machine.current_state == State.COMPLETED
    
    def test_get_summary(self, state_machine):
        """测试获取摘要。"""
        summary = state_machine.get_summary()
        
        assert "current_state" in summary
        assert "progress" in summary
        assert "is_terminal" in summary
        assert "valid_transitions" in summary
    
    def test_reset(self, state_machine):
        """测试重置。"""
        state_machine.transition_to(State.REQUIREMENTS_DRAFT)
        state_machine.reset()
        
        assert state_machine.current_state == State.PROJECT_INIT
        assert len(state_machine.history) == 0
    
    def test_get_state_by_name(self, state_machine):
        """测试根据名称获取状态。"""
        state = state_machine.get_state_by_name("project_init")
        assert state == State.PROJECT_INIT
        
        state = state_machine.get_state_by_name("unknown")
        assert state is None
    
    def test_complete_workflow(self, state_machine):
        """测试完整工作流程。"""
        state_machine.transition_to(State.REQUIREMENTS_DRAFT)
        state_machine.transition_to(State.REQUIREMENTS_REVIEW)
        state_machine.transition_to(State.REQUIREMENTS_APPROVED)
        state_machine.transition_to(State.DESIGN_DRAFT)
        state_machine.transition_to(State.DESIGN_REVIEW)
        state_machine.transition_to(State.DESIGN_APPROVED)
        state_machine.transition_to(State.DEVELOPMENT)
        state_machine.transition_to(State.TESTING)
        state_machine.transition_to(State.DEPLOYMENT)
        state_machine.transition_to(State.COMPLETED)
        
        assert state_machine.current_state == State.COMPLETED
        assert state_machine.is_completed()
        assert len(state_machine.history) == 10
    
    def test_state_info(self, state_machine):
        """测试状态信息。"""
        info = state_machine.STATE_INFO[State.PROJECT_INIT]
        
        assert info.state == State.PROJECT_INIT
        assert info.name == "项目初始化"
        assert info.is_terminal == False
        
        info = state_machine.STATE_INFO[State.COMPLETED]
        assert info.is_terminal == True


class TestStateTransitions:
    """状态转换测试类。"""
    
    @pytest.fixture
    def sm(self):
        """创建状态机实例。"""
        return StateMachine()
    
    def test_project_init_to_requirements_draft(self, sm):
        """测试项目初始化到需求草稿。"""
        result = sm.transition_to(State.REQUIREMENTS_DRAFT)
        assert result["success"]
        assert sm.current_state == State.REQUIREMENTS_DRAFT
    
    def test_requirements_flow(self, sm):
        """测试需求阶段流程。"""
        sm.transition_to(State.REQUIREMENTS_DRAFT)
        sm.transition_to(State.REQUIREMENTS_REVIEW)
        sm.transition_to(State.REQUIREMENTS_APPROVED)
        
        assert sm.current_state == State.REQUIREMENTS_APPROVED
    
    def test_design_flow(self, sm):
        """测试设计阶段流程。"""
        sm.transition_to(State.REQUIREMENTS_APPROVED)
        sm.transition_to(State.DESIGN_DRAFT)
        sm.transition_to(State.DESIGN_REVIEW)
        sm.transition_to(State.DESIGN_APPROVED)
        
        assert sm.current_state == State.DESIGN_APPROVED
    
    def test_development_to_testing(self, sm):
        """测试开发到测试阶段。"""
        sm.transition_to(State.DESIGN_APPROVED)
        sm.transition_to(State.DEVELOPMENT)
        sm.transition_to(State.TESTING, EventType.CODE_COMMITTED)
        
        assert sm.current_state == State.TESTING
    
    def test_testing_to_deployment(self, sm):
        """测试测试到部署阶段。"""
        sm.transition_to(State.TESTING)
        sm.transition_to(State.DEPLOYMENT, EventType.TEST_COMPLETE)
        
        assert sm.current_state == State.DEPLOYMENT
    
    def test_deployment_to_completed(self, sm):
        """测试部署到完成阶段。"""
        sm.transition_to(State.DEPLOYMENT)
        sm.transition_to(State.COMPLETED, EventType.DEPLOY_COMPLETE)
        
        assert sm.current_state == State.COMPLETED
        assert sm.is_completed()


class TestStateMachineEdgeCases:
    """状态机边界情况测试类。"""
    
    def test_same_state_transition(self):
        """测试相同状态转换。"""
        sm = StateMachine()
        result = sm.transition_to(State.PROJECT_INIT)
        
        assert result["success"]
        assert "已经是目标状态" in result["message"]
    
    def test_invalid_state_transition(self):
        """测试无效状态转换。"""
        sm = StateMachine()
        
        with pytest.raises(Exception):
            sm.transition_to(State.DEVELOPMENT)
    
    def test_version_increment(self):
        """测试版本号递增。"""
        sm = StateMachine()
        
        assert sm._version == 1
        sm.transition_to(State.REQUIREMENTS_DRAFT)
        assert sm._version == 2
