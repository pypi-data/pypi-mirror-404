"""项目检测器模块。"""
from pathlib import Path
from typing import Dict


PROJECT_TYPE_PYTHON = "PYTHON"
PROJECT_TYPE_TYPESCRIPT = "TYPESCRIPT"
PROJECT_TYPE_MIXED = "MIXED"
PROJECT_TYPE_AUTO = "AUTO"


class ProjectDetector:
    """项目类型检测器。"""
    
    PYTHON_INDICATORS = ["pyproject.toml", "setup.py", "requirements.txt", "setup.cfg", "Pipfile"]
    TYPESCRIPT_INDICATORS = ["package.json", "tsconfig.json"]
    
    def __init__(self, project_path: str):
        """初始化检测器。"""
        self.project_path = Path(project_path)
    
    def detect(self) -> str:
        """检测项目类型。"""
        python_score = self._count_python_indicators()
        typescript_score = self._count_typescript_indicators()
        
        if python_score > 0 and typescript_score > 0:
            return PROJECT_TYPE_MIXED
        elif python_score > 0:
            return PROJECT_TYPE_PYTHON
        elif typescript_score > 0:
            return PROJECT_TYPE_TYPESCRIPT
        else:
            return PROJECT_TYPE_AUTO
    
    def _count_python_indicators(self) -> int:
        """统计Python项目特征文件数量。"""
        count = 0
        for indicator in self.PYTHON_INDICATORS:
            if (self.project_path / indicator).exists():
                count += 1
        return count
    
    def _count_typescript_indicators(self) -> int:
        """统计TypeScript项目特征文件数量。"""
        count = 0
        for indicator in self.TYPESCRIPT_INDICATORS:
            if (self.project_path / indicator).exists():
                count += 1
        return count
    
    def is_python_project(self) -> bool:
        """检查是否为Python项目。"""
        return self._count_python_indicators() > 0
    
    def is_typescript_project(self) -> bool:
        """检查是否为TypeScript项目。"""
        return self._count_typescript_indicators() > 0
    
    def get_detection_details(self) -> Dict[str, int]:
        """获取检测详情。"""
        return {
            "python_score": self._count_python_indicators(),
            "typescript_score": self._count_typescript_indicators()
        }


def detect_project_type(project_path: str) -> str:
    """检测项目类型。"""
    detector = ProjectDetector(project_path)
    return detector.detect()
