"""测试 state 数据结构兼容性。

覆盖问题：
1. design 字段为列表 vs 字典
2. phase 在 project 下 vs 根级
"""
import pytest
import tempfile
import os
from pathlib import Path

from src.core.state_manager import StateManager
from src.core.signoff import SignoffEngine


class TestDesignListCompatibility:
    """测试 design 字段为列表时的兼容性。"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目目录。"""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()
        (project_path / "state").mkdir()
        yield project_path
        import shutil
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def state_manager(self, temp_project):
        """创建 StateManager。"""
        return StateManager(temp_project)

    def test_signoff_with_design_list(self, temp_project):
        """测试 design 为列表时的签署功能。"""
        state_file = temp_project / "state" / "project_state.yaml"
        state_file.write_text("""
version: 2.0.0
project:
  name: Test Project
  phase: design
design:
  - version: TD-001
    status: review    # ← 改为 review 才能签署
    pm_signoff: false
    dev_signoff: false
    document: docs/design.md
    review_document: ""
requirements:
  version: ''
  status: approved
  pm_signoff: true
  dev_signoff: true
test:
  version: v1
  status: pending
  blackbox_cases: 0
  blackbox_passed: 0
  pm_signoff: false
  dev_signoff: false
development:
  status: pending
  branch: ''
deployment:
  status: pending
metadata:
  project_name: Test Project
  project_type: PYTHON
""")
        
        state_manager = StateManager(temp_project)
        signoff_engine = SignoffEngine(state_manager, None)
        
        # 应该能正常获取 stage_data 而不是报错
        can_sign, msg = signoff_engine.can_sign("design", "agent1")
        assert can_sign is True, f"应该可以签署，错误: {msg}"

    def test_signoff_with_design_dict(self, temp_project):
        """测试 design 为字典时的签署功能。"""
        state_file = temp_project / "state" / "project_state.yaml"
        state_file.write_text("""
version: 2.0.0
project:
  name: Test Project
  phase: design
design:
  status: review    # ← 改为 review 才能签署
  pm_signoff: false
  dev_signoff: false
requirements:
  version: ''
  status: approved
  pm_signoff: true
  dev_signoff: true
test:
  version: v1
  status: pending
  blackbox_cases: 0
  blackbox_passed: 0
development:
  status: pending
deployment:
  status: pending
metadata:
  project_name: Test Project
  project_type: PYTHON
""")
        
        state_manager = StateManager(temp_project)
        signoff_engine = SignoffEngine(state_manager, None)
        
        can_sign, msg = signoff_engine.can_sign("design", "agent1")
        assert can_sign is True, f"应该可以签署，错误: {msg}"

    def test_signoff_with_empty_design_list(self, temp_project):
        """测试空 design 列表的边界情况。"""
        state_file = temp_project / "state" / "project_state.yaml"
        state_file.write_text("""
version: 2.0.0
project:
  name: Test Project
  phase: design
design: []
requirements:
  version: ''
  status: approved
  pm_signoff: true
  dev_signoff: true
test:
  version: v1
  status: pending
  blackbox_cases: 0
  blackbox_passed: 0
development:
  status: pending
deployment:
  status: pending
metadata:
  project_name: Test Project
  project_type: PYTHON
""")
        
        state_manager = StateManager(temp_project)
        signoff_engine = SignoffEngine(state_manager, None)
        
        # 空列表应该返回空字典，不报错
        can_sign, msg = signoff_engine.can_sign("design", "agent1")
        # 空列表时不应该签署
        assert can_sign is False


class TestPhaseStructureCompatibility:
    """测试 phase 位置兼容性。"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目目录。"""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()
        (project_path / "state").mkdir()
        yield project_path
        import shutil
        shutil.rmtree(temp_dir)

    def test_phase_in_project(self, temp_project):
        """测试 phase 在 project 下。"""
        state_file = temp_project / "state" / "project_state.yaml"
        state_file.write_text("""
version: 2.0.0
project:
  name: Test Project
  phase: development
design:
  status: completed
  pm_signoff: true
  dev_signoff: true
requirements:
  version: ''
  status: approved
  pm_signoff: true
  dev_signoff: true
test:
  version: v1
  status: pending
  blackbox_cases: 0
  blackbox_passed: 0
development:
  status: in_progress
deployment:
  status: pending
metadata:
  project_name: Test Project
  project_type: PYTHON
""")
        
        state_manager = StateManager(temp_project)
        state = state_manager.load_state()
        
        # 应该能正确读取 project.phase
        project_info = state.get("project", {})
        phase = project_info.get("phase")
        assert phase == "development", f"应该读取到 development，实际: {phase}"

    def test_phase_at_root(self, temp_project):
        """测试 phase 在根级。"""
        state_file = temp_project / "state" / "project_state.yaml"
        state_file.write_text("""
version: 2.0.0
project:
  name: Test Project
phase: testing
design:
  status: completed
  pm_signoff: true
  dev_signoff: true
requirements:
  version: ''
  status: approved
  pm_signoff: true
  dev_signoff: true
test:
  version: v1
  status: passed
  blackbox_cases: 10
  blackbox_passed: 10
development:
  status: completed
deployment:
  status: pending
metadata:
  project_name: Test Project
  project_type: PYTHON
""")
        
        state_manager = StateManager(temp_project)
        state = state_manager.load_state()
        
        # 应该能正确读取根级 phase
        phase = state.get("phase")
        assert phase == "testing", f"应该读取到 testing，实际: {phase}"


class TestSignoffSummaryWithDesignList:
    """测试获取签署摘要时 design 为列表的情况。"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目目录。"""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()
        (project_path / "state").mkdir()
        yield project_path
        import shutil
        shutil.rmtree(temp_dir)

    def test_get_signoff_summary_design_list(self, temp_project):
        """测试 design 为列表时获取签署摘要。"""
        state_file = temp_project / "state" / "project_state.yaml"
        state_file.write_text("""
version: 2.0.0
project:
  name: Test Project
  phase: design
design:
  - version: TD-001
    status: approved
    pm_signoff: true
    dev_signoff: true
    document: docs/design.md
  - version: TD-002
    status: in_progress
    pm_signoff: false
    dev_signoff: false
    document: docs/design_v2.md
requirements:
  version: ''
  status: approved
  pm_signoff: true
  dev_signoff: true
test:
  version: v1
  status: pending
  blackbox_cases: 0
  blackbox_passed: 0
development:
  status: pending
deployment:
  status: pending
metadata:
  project_name: Test Project
  project_type: PYTHON
""")
        
        state_manager = StateManager(temp_project)
        signoff_engine = SignoffEngine(state_manager, None)
        
        # 应该返回签署摘要而不报错
        summary = signoff_engine.get_signoff_summary("design")
        assert "error" not in summary, f"不应该返回错误: {summary}"
        assert summary.get("pm_signoff") is True
        assert summary.get("dev_signoff") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
