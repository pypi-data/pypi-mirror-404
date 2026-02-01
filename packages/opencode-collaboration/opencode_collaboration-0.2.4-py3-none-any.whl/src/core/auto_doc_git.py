"""文档自动添加git引擎"""
from pathlib import Path
from typing import Dict, Any, List
import subprocess
import logging

logger = logging.getLogger(__name__)

class AutoDocGitAddEngine:
    """自动添加新文档到 git"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.docs_dir = self.project_path / 'docs'
        self.tracked_file = self.project_path / 'state' / 'tracked_docs.txt'
    
    def detect_new_docs(self) -> List[str]:
        """检测新文档"""
        result = subprocess.run(
            ['git', 'ls-files', '--others', '--exclude-standard'],
            capture_output=True, text=True,
            cwd=self.project_path
        )
        new_files = [f for f in result.stdout.strip().split('
') if f and f.startswith('docs/')]
        return new_files
    
    def auto_add_docs(self) -> Dict[str, Any]:
        """自动添加新文档"""
        new_docs = self.detect_new_docs()
        if not new_docs:
            return {"added": [], "message": "无新文档"}
        
        for doc in new_docs:
            subprocess.run(['git', 'add', doc], cwd=self.project_path, capture_output=True)
        
        return {"added": new_docs, "message": f"已添加 {len(new_docs)} 个新文档"}
    
    def sync(self) -> Dict[str, Any]:
        """同步新文档"""
        return self.auto_add_docs()
