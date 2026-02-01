"""状态管理器单元测试。"""
import os
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.state_manager import StateManager, StateFileNotFoundError


class TestStateManager:
    """状态管理器测试类。"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def state_manager(self, temp_dir):
        """创建状态管理器实例。"""
        return StateManager(temp_dir)
    
    def test_init_state(self, state_manager):
        """测试初始化状态。"""
        state = state_manager.init_state("TestProject", "PYTHON")
        
        assert state["project"]["name"] == "TestProject"
        assert state["project"]["type"] == "PYTHON"
        assert state["phase"] == "project_init"
        assert state["agents"]["agent1"]["current"] == True
        assert state["agents"]["agent2"]["current"] == False
    
    def test_load_state(self, state_manager):
        """测试加载状态。"""
        state_manager.init_state("TestProject", "PYTHON")
        state = state_manager.load_state()
        
        assert state["project"]["name"] == "TestProject"
        assert state["project"]["type"] == "PYTHON"
    
    def test_load_state_file_not_found(self, temp_dir):
        """测试加载不存在的状态文件。"""
        state_manager = StateManager(temp_dir)
        with pytest.raises(StateFileNotFoundError):
            state_manager.load_state()
    
    def test_update_phase(self, state_manager):
        """测试更新阶段。"""
        state_manager.init_state("TestProject", "PYTHON")
        state = state_manager.update_phase("requirements_draft")
        
        assert state["phase"] == "requirements_draft"
    
    def test_update_signoff(self, state_manager):
        """测试更新签署状态。"""
        state_manager.init_state("TestProject", "PYTHON")
        state = state_manager.update_signoff("requirements", "pm", True, "确认需求")
        
        assert state["requirements"]["pm_signoff"] == True
    
    def test_get_current_phase(self, state_manager):
        """测试获取当前阶段。"""
        state_manager.init_state("TestProject", "PYTHON")
        phase = state_manager.get_current_phase()
        
        assert phase == "project_init"
    
    def test_get_signoff_status(self, state_manager):
        """测试获取签署状态。"""
        state_manager.init_state("TestProject", "PYTHON")
        status = state_manager.get_signoff_status("requirements")
        
        assert status["pm_signoff"] == False
        assert status["dev_signoff"] == False
    
    def test_set_active_agent(self, state_manager):
        """测试设置活跃Agent。"""
        state_manager.init_state("TestProject", "PYTHON")
        state = state_manager.set_active_agent("agent2")
        
        assert state["agents"]["agent2"]["current"] == True
        assert state["agents"]["agent1"]["current"] == False
    
    def test_add_history(self, state_manager):
        """测试添加历史记录。"""
        state_manager.init_state("TestProject", "PYTHON")
        state_manager.add_history("init", "agent1", "初始化项目")
        
        history = state_manager.get_history()
        assert len(history) == 1
        assert history[0]["action"] == "init"
    
    def test_increment_review_cycle(self, state_manager):
        """测试增加评审轮次。"""
        state_manager.init_state("TestProject", "PYTHON")
        state_manager.increment_review_cycle()
        
        state = state_manager.load_state()
        assert state["requirements"]["review_cycles"] == 1
    
    def test_can_proceed_to_next_phase(self, state_manager):
        """测试是否可以推进到下一阶段。"""
        state_manager.init_state("TestProject", "PYTHON")
        
        assert state_manager.can_proceed_to_next_phase() == False
