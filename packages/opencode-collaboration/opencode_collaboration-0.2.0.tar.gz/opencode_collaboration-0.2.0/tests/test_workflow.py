"""工作流引擎单元测试。"""
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.state_manager import StateManager
from src.core.workflow import WorkflowEngine, IllegalPhaseTransitionError


class TestWorkflowEngine:
    """工作流引擎测试类。"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def state_manager(self, temp_dir):
        """创建状态管理器实例。"""
        sm = StateManager(temp_dir)
        sm.init_state("TestProject", "PYTHON")
        return sm
    
    @pytest.fixture
    def workflow_engine(self, state_manager):
        """创建工作流引擎实例。"""
        return WorkflowEngine(state_manager)
    
    def test_can_transition_valid(self, workflow_engine):
        """测试合法状态转换。"""
        assert workflow_engine.can_transition("project_init", "requirements_draft") == True
    
    def test_can_transition_invalid(self, workflow_engine):
        """测试非法状态转换。"""
        assert workflow_engine.can_transition("project_init", "development") == False
    
    def test_get_valid_next_phases(self, workflow_engine):
        """测试获取合法下一阶段。"""
        valid = workflow_engine.get_valid_next_phases("project_init")
        assert "requirements_draft" in valid
    
    def test_transition_to(self, workflow_engine):
        """测试执行状态转换。"""
        result = workflow_engine.transition_to("requirements_draft")
        
        assert result["from"] == "project_init"
        assert result["to"] == "requirements_draft"
    
    def test_transition_to_invalid(self, workflow_engine):
        """测试执行非法状态转换。"""
        with pytest.raises(IllegalPhaseTransitionError):
            workflow_engine.transition_to("development")
    
    def test_start_review(self, workflow_engine):
        """测试发起评审。"""
        workflow_engine.start_review("requirements")
        
        phase = workflow_engine.state_manager.get_current_phase()
        assert phase == "requirements_review"
    
    def test_get_phase_progress(self, workflow_engine):
        """测试获取阶段进度。"""
        progress = workflow_engine.get_phase_progress("project_init")
        
        assert "current_phase" in progress
        assert "progress_percentage" in progress
    
    def test_is_phase_completed(self, workflow_engine):
        """测试阶段是否完成。"""
        assert workflow_engine.is_phase_completed("project_init") == False
    
    def test_get_workflow_summary(self, workflow_engine):
        """测试获取工作流摘要。"""
        summary = workflow_engine.get_workflow_summary()
        
        assert "current_phase" in summary
        assert "phase_progress" in summary
