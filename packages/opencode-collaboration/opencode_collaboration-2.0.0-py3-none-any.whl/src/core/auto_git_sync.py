"""Git自动同步引擎"""
from pathlib import Path
from typing import Dict, Any, List
import subprocess
import logging

logger = logging.getLogger(__name__)

class AutoGitSyncEngine:
    """自动同步 Git 变更"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
    
    def detect_changes(self) -> List[str]:
        """检测变更文件"""
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True,
            cwd=self.project_path
        )
        lines = result.stdout.strip().split('\n')
        return [line[3:] for line in lines if line]
    
    def auto_add(self) -> Dict[str, Any]:
        """自动 git add"""
        changes = self.detect_changes()
        if not changes:
            return {"added": [], "message": "无变更"}
        
        for f in changes:
            subprocess.run(['git', 'add', f], cwd=self.project_path, capture_output=True)
        
        return {"added": changes, "message": f"已添加 {len(changes)} 个文件"}
    
    def auto_commit(self, message: str = "自动提交") -> Dict[str, Any]:
        """自动 commit"""
        result = subprocess.run(
            ['git', 'commit', '-m', message], 
            capture_output=True, 
            text=True,
            cwd=self.project_path
        )
        return {"success": result.returncode == 0, "message": result.stdout}
    
    def auto_push(self) -> Dict[str, Any]:
        """自动 push 到所有远程"""
        result = subprocess.run(
            ['git', 'push'], 
            capture_output=True, 
            text=True,
            cwd=self.project_path
        )
        return {"success": result.returncode == 0, "message": result.stdout}
    
    def sync_all(self) -> Dict[str, Any]:
        """完整同步流程"""
        add_result = self.auto_add()
        commit_result = self.auto_commit("自动同步变更")
        push_result = self.auto_push()
        return {"add": add_result, "commit": commit_result, "push": push_result}
