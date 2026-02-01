"""项目检测器单元测试。"""
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.detector import ProjectDetector, detect_project_type


class TestProjectDetector:
    """项目检测器测试类。"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_detect_python_project(self, temp_dir):
        """测试Python项目检测。"""
        Path(temp_dir, "pyproject.toml").touch()
        
        detector = ProjectDetector(temp_dir)
        result = detector.detect()
        
        assert result == "PYTHON"
    
    def test_detect_typescript_project(self, temp_dir):
        """测试TypeScript项目检测。"""
        Path(temp_dir, "package.json").touch()
        Path(temp_dir, "tsconfig.json").touch()
        
        detector = ProjectDetector(temp_dir)
        result = detector.detect()
        
        assert result == "TYPESCRIPT"
    
    def test_detect_mixed_project(self, temp_dir):
        """测试混合项目检测。"""
        Path(temp_dir, "pyproject.toml").touch()
        Path(temp_dir, "package.json").touch()
        
        detector = ProjectDetector(temp_dir)
        result = detector.detect()
        
        assert result == "MIXED"
    
    def test_detect_auto_project(self, temp_dir):
        """测试自动检测（无特征文件）。"""
        detector = ProjectDetector(temp_dir)
        result = detector.detect()
        
        assert result == "AUTO"
    
    def test_is_python_project(self, temp_dir):
        """测试Python项目判断。"""
        Path(temp_dir, "requirements.txt").touch()
        
        detector = ProjectDetector(temp_dir)
        assert detector.is_python_project() == True
    
    def test_is_typescript_project(self, temp_dir):
        """测试TypeScript项目判断。"""
        Path(temp_dir, "tsconfig.json").touch()
        
        detector = ProjectDetector(temp_dir)
        assert detector.is_typescript_project() == True
    
    def test_get_detection_details(self, temp_dir):
        """测试获取检测详情。"""
        Path(temp_dir, "pyproject.toml").touch()
        
        detector = ProjectDetector(temp_dir)
        details = detector.get_detection_details()
        
        assert "python_score" in details
        assert "typescript_score" in details
