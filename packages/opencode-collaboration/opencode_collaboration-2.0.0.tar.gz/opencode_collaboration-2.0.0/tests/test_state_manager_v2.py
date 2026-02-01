import pytest
"""状态管理器与状态机集成测试。"""
import tempfile
import os
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.state_manager import StateManager
from src.core.state_machine import StateMachine, State, EventType


class TestStateManagerPersistence:
    """状态持久化测试类。"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def state_manager(self, temp_dir):
        """创建状态管理器实例。"""
        sm = StateManager(temp_dir)
        sm.initialize_project("TestProject", "PYTHON")
        return sm
    
    def test_initialize_project(self, temp_dir):
        """测试项目初始化。"""
        sm = StateManager(temp_dir)
        state = sm.initialize_project("TestProject", "PYTHON")
        
        assert state["project"]["name"] == "TestProject"
        assert state["project"]["type"] == "PYTHON"
        assert state["phase"] == "project_init"
        assert state["state_version"] == 1
    
    def test_read_write_state(self, state_manager):
        """测试读写状态。"""
        state = state_manager.read_state()
        assert state["phase"] == "project_init"
        
        state["phase"] = "requirements_draft"
        state_manager.write_state(state, "test_write")
        
        new_state = state_manager.read_state()
        assert new_state["phase"] == "requirements_draft"
        assert new_state["state_version"] == 2
    
    def test_get_state_version(self, state_manager):
        """测试获取状态版本。"""
        version = state_manager.get_state_version()
        assert version == 1
        
        state = state_manager.read_state()
        state_manager.write_state(state)
        
        version = state_manager.get_state_version()
        assert version == 2
    
    def test_get_current_phase(self, state_manager):
        """测试获取当前阶段。"""
        phase = state_manager.get_current_phase()
        assert phase == "project_init"


class TestOptimisticLock:
    """乐观锁测试类。"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def sm1(self, temp_dir):
        """创建第一个状态管理器实例。"""
        return StateManager(temp_dir, lock_owner="agent1")
    
    @pytest.fixture
    def sm2(self, temp_dir):
        """创建第二个状态管理器实例。"""
        return StateManager(temp_dir, lock_owner="agent2")
    
    def test_acquire_lock(self, sm1):
        """测试获取锁。"""
        result = sm1.acquire_lock()
        assert result == True
        assert sm1.is_locked() == True
        
        sm1.release_lock()
        assert sm1.is_locked() == False
    
    def test_lock_contention(self, sm1, sm2):
        """测试锁竞争。"""
        result1 = sm1.acquire_lock()
        assert result1 == True
        
        result2 = sm2.acquire_lock()
        assert result2 == False
        
        sm1.release_lock()
        
        result2 = sm2.acquire_lock()
        assert result2 == True
        
        sm2.release_lock()
    
    def test_lock_timeout(self, temp_dir):
        """测试锁超时。"""
        sm = StateManager(temp_dir)
        sm.LOCK_TIMEOUT = 1
        sm.acquire_lock()
        
        import time
        time.sleep(2)
        
        assert sm.is_locked() == False
    
    def test_version_based_lock(self, temp_dir):
        """测试基于版本的锁。"""
        sm = StateManager(temp_dir)
        sm.initialize_project("Test", "PYTHON")
        
        version = sm.get_state_version()
        result = sm.acquire_lock(expected_version=version)
        assert result == True
        
        result = sm.acquire_lock(expected_version=version)
        assert result == False


class TestPhaseTransition:
    """阶段转换测试类。"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def state_manager(self, temp_dir):
        """创建状态管理器实例。"""
        sm = StateManager(temp_dir)
        sm.initialize_project("TestProject", "PYTHON")
        return sm
    
    def test_transition_phase(self, state_manager):
        """测试阶段转换。"""
        success, new_state = state_manager.transition_phase(
            from_phase="project_init",
            to_phase="requirements_draft",
            agent_id="agent1",
            details="创建需求文档"
        )
        
        assert success == True
        assert new_state["phase"] == "requirements_draft"
        assert new_state["state_version"] == 2
    
    def test_transition_with_history(self, state_manager):
        """测试转换历史记录。"""
        state_manager.transition_phase(
            from_phase="project_init",
            to_phase="requirements_draft",
            agent_id="agent1"
        )
        
        history = state_manager.get_history()
        assert len(history) >= 1
        assert history[0]["action"] == "phase_transition"
        assert history[0]["phase_from"] == "project_init"
        assert history[0]["phase_to"] == "requirements_draft"
    
    def test_invalid_transition(self, state_manager):
        """测试无效转换。"""
        success, result = state_manager.transition_phase(
            from_phase="requirements_draft",
            to_phase="development",
            agent_id="agent1"
        )
        
        assert success == False
        assert "error" in result
    
    def test_complete_workflow(self, state_manager):
        """测试完整工作流程。"""
        transitions = [
            ("project_init", "requirements_draft", "agent1"),
            ("requirements_draft", "requirements_review", "agent1"),
            ("requirements_review", "requirements_approved", "agent1"),
            ("requirements_approved", "design_draft", "agent2"),
            ("design_draft", "design_review", "agent2"),
            ("design_review", "design_approved", "agent2"),
            ("design_approved", "development", "agent2"),
            ("development", "testing", "agent2"),
            ("testing", "deployment", "agent1"),
            ("deployment", "completed", "agent1")
        ]
        
        for from_phase, to_phase, agent_id in transitions:
            success, state = state_manager.transition_phase(
                from_phase=from_phase,
                to_phase=to_phase,
                agent_id=agent_id
            )
            assert success == True, f"转换 {from_phase} -> {to_phase} 失败"
        
        final_phase = state_manager.get_current_phase()
        assert final_phase == "completed"
        
        history = state_manager.get_history()
        assert len(history) == 10


class TestStateMachineIntegration:
    """状态机集成测试类。"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def state_manager(self, temp_dir):
        """创建状态管理器实例。"""
        sm = StateManager(temp_dir)
        sm.initialize_project("TestProject", "PYTHON")
        return sm
    
    @pytest.fixture
    def state_machine(self):
        """创建状态机实例。"""
        return StateMachine(State.PROJECT_INIT)
    
    def test_sync_state_machine_and_manager(self, state_machine, state_manager):
        """测试同步状态机和状态管理器。"""
        state_machine.transition_to(State.REQUIREMENTS_DRAFT)
        
        phase = state_machine.current_state.value
        success, _ = state_manager.transition_phase(
            from_phase="project_init",
            to_phase=phase,
            agent_id="agent1"
        )
        
        assert success == True
        
        manager_phase = state_manager.get_current_phase()
        assert manager_phase == phase
    
    def test_state_version_on_transition(self, state_machine, state_manager):
        """测试转换时版本号递增。"""
        initial_version = state_manager.get_state_version()
        
        state_machine.transition_to(State.REQUIREMENTS_DRAFT)
        phase = state_machine.current_state.value
        
        state_manager.transition_phase(
            from_phase="project_init",
            to_phase=phase,
            agent_id="agent1"
        )
        
        new_version = state_manager.get_state_version()
        assert new_version == initial_version + 1


class TestStateHistory:
    """状态历史测试类。"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def state_manager(self, temp_dir):
        """创建状态管理器实例。"""
        sm = StateManager(temp_dir)
        sm.initialize_project("TestProject", "PYTHON")
        return sm
    
    def test_add_history_entry(self, state_manager):
        """测试添加历史记录。"""
        state_manager.add_history_entry(
            action="test_action",
            agent_id="agent1",
            details="测试详情"
        )
        
        history = state_manager.get_history()
        assert len(history) >= 1
        assert history[0]["action"] == "test_action"
        assert history[0]["agent_id"] == "agent1"
    
    def test_history_limit(self, state_manager):
        """测试历史记录限制。"""
        for i in range(60):
            state_manager.add_history_entry(
                action=f"action_{i}",
                agent_id="agent1"
            )
        
        history = state_manager.get_history()
        assert len(history) <= 50
    
    def test_history_with_transition(self, state_manager):
        """测试转换生成的历史记录。"""
        state_manager.transition_phase(
            from_phase="project_init",
            to_phase="requirements_draft",
            agent_id="agent1"
        )
        
        history = state_manager.get_history()
        transition_entry = None
        for entry in history:
            if entry["action"] == "phase_transition":
                transition_entry = entry
                break
        
        assert transition_entry is not None
        assert transition_entry["phase_from"] == "project_init"
        assert transition_entry["phase_to"] == "requirements_draft"
        assert transition_entry["agent_id"] == "agent1"


class TestBackwardsCompatibility:
    """向后兼容性测试类。"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_compatible_methods(self, temp_dir):
        """测试兼容方法。"""
        sm = StateManager(temp_dir)
        sm.init_state("TestProject", "PYTHON")
        
        assert sm.get_current_phase() == "project_init"
        
        state = sm.load_state()
        assert state["phase"] == "project_init"
        
        sm.save_state(state)
        
        active_agent = sm.get_active_agent()
        assert active_agent == "agent1"
        
        sm.set_active_agent("agent2")
        active_agent = sm.get_active_agent()
        assert active_agent == "agent2"
