"""文档自动同步模块。"""
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import logging

from ..utils.yaml import load_yaml, save_yaml
from ..utils.date import get_current_time

logger = logging.getLogger(__name__)


@dataclass
class AutoDocsConfig:
    """文档自动同步配置"""
    enabled: bool = True
    update_changelog: bool = True
    update_manual: bool = True
    update_tests: bool = False
    require_confirm: bool = True
    auto_commit: bool = False


class AutoDocs:
    """文档自动同步器"""
    
    CHANGE_TYPE_MAP = {
        "feat": "新功能",
        "fix": "缺陷修复",
        "docs": "文档更新",
        "test": "测试更新",
        "refactor": "重构",
        "perf": "性能优化",
        "chore": "构建/工具",
    }
    
    DOC_IMPACT_MAP = {
        "src/cli/main.py": {
            "docs": ["docs/使用手册.md"],
            "tests": ["tests/test_e2e.py"],
            "changelog": True,
        },
        "src/core/git.py": {
            "docs": ["docs/使用手册.md"],
            "tests": [],
            "changelog": True,
        },
        "src/core/auto_retry.py": {
            "docs": ["docs/使用手册.md"],
            "tests": [],
            "changelog": True,
        },
        "src/core/": {
            "docs": [],
            "tests": [],
            "changelog": True,
        },
        "docs/04-changelog/": {
            "docs": [],
            "tests": [],
            "changelog": True,
        },
    }
    
    def __init__(self, project_path: str, config: Optional[AutoDocsConfig] = None):
        """初始化文档自动同步器"""
        self.project_path = Path(project_path)
        self.config = config or AutoDocsConfig()
        self.state_file = self.project_path / "state" / "project_state.yaml"
        self.changelog_file = self.project_path / "docs" / "04-changelog" / "change_log.md"
        self.manual_file = self.project_path / "docs" / "使用手册.md"
    
    def _load_state(self) -> Dict[str, Any]:
        """加载状态"""
        if self.state_file.exists():
            return load_yaml(str(self.state_file))
        return {}
    
    def _save_state(self, state: Dict[str, Any]) -> None:
        """保存状态"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        save_yaml(str(self.state_file), state)
    
    def _detect_change_type(self, message: str) -> str:
        """检测变更类型"""
        message_lower = message.lower()
        for prefix, name in self.CHANGE_TYPE_MAP.items():
            if message_lower.startswith(prefix):
                return name
        return "其他更新"
    
    def _extract_scope(self, message: str) -> str:
        """提取影响范围"""
        match = re.search(r'\((.*?)\)', message)
        if match:
            return match.group(1)
        return "系统"
    
    def detect_changes(self, last_commit: Optional[str] = None) -> Dict[str, Any]:
        """
        检测代码变更影响
        
        Args:
            last_commit: 上次检测的提交（可选）
        
        Returns:
            {
                "changed_files": [...],
                "impacted_docs": [...],
                "impacted_commands": [...],
                "change_type": str,
            }
        """
        import subprocess
        
        changed_files = []
        impacted_docs = []
        impacted_commands = []
        
        try:
            if last_commit:
                result = subprocess.run(
                    ["git", "diff", "--name-only", last_commit, "HEAD"],
                    cwd=str(self.project_path),
                    capture_output=True,
                    text=True
                )
            else:
                result = subprocess.run(
                    ["git", "diff", "--cached", "--name-only"],
                    cwd=str(self.project_path),
                    capture_output=True,
                    text=True
                )
                if not result.stdout.strip():
                    result = subprocess.run(
                        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                        cwd=str(self.project_path),
                        capture_output=True,
                        text=True
                    )
            
            changed_files = [f for f in result.stdout.strip().split('\n') if f]
            
        except Exception as e:
            logger.warning(f"检测变更失败: {e}")
        
        for file_path in changed_files:
            for pattern, impact in self.DOC_IMPACT_MAP.items():
                if file_path.startswith(pattern):
                    impacted_docs.extend(impact.get("docs", []))
                    if "cli/main.py" in file_path:
                        impacted_commands.extend(self._extract_commands_from_diff(file_path))
                    break
        
        return {
            "changed_files": list(set(changed_files)),
            "impacted_docs": list(set(impacted_docs)),
            "impacted_commands": list(set(impacted_commands)),
            "change_type": "代码更新",
        }
    
    def _extract_commands_from_diff(self, file_path: str) -> List[str]:
        """从 diff 中提取新增的命令"""
        import subprocess
        
        commands = []
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD~1", file_path],
                cwd=str(self.project_path),
                capture_output=True,
                text=True
            )
            
            new_commands = re.findall(r'@main\.command\(["\'](.+?)["\']\)', result.stdout)
            commands = list(set(new_commands))
            
        except Exception as e:
            logger.warning(f"提取命令失败: {e}")
        
        return commands
    
    def update_changelog(self, change_type: str, message: str) -> bool:
        """更新变更记录"""
        if not self.changelog_file.exists():
            logger.warning(f"变更记录文件不存在: {self.changelog_file}")
            return False
        
        try:
            with open(self.changelog_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            today = datetime.now().strftime("%Y-%m-%d")
            scope = self._extract_scope(message)
            
            new_entry = f"""
| v.next | {today} | {change_type} | {message[:50]}... | {scope} | 系统 |
"""
            
            change_type_section = f"### {change_type}"
            if change_type_section in content:
                content = content.replace(
                    change_type_section,
                    f"{change_type_section}\n{new_entry.strip()}"
                )
            else:
                sections = content.split("## ")
                for i, section in enumerate(sections):
                    if "变更历史" in section or "变更类型" in section:
                        continue
                
                new_section = f"## 变更历史\n\n| 版本 | 日期 | 变更类型 | 变更内容 | 变更原因 | 决策人 |\n|-----|------|---------|---------|---------|--------|\n{new_entry}\n"
                content = new_section + "\n".join(sections[1:])
            
            with open(self.changelog_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✓ 已更新变更记录")
            return True
            
        except Exception as e:
            logger.error(f"更新变更记录失败: {e}")
            return False
    
    def update_manual(self, command: str, description: str = "") -> bool:
        """更新使用手册"""
        if not self.manual_file.exists():
            logger.warning(f"使用手册不存在: {self.manual_file}")
            return False
        
        try:
            with open(self.manual_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_section = f"""
### 4.X {command}

```bash
oc-collab {command}
```

**功能**：
- {description if description else "自动化执行"}

"""
            
            section_pattern = r'(### 4\.\d+ help - 帮助信息)'
            if re.search(section_pattern, content):
                content = re.sub(
                    section_pattern,
                    f"{new_section.strip()}\n\n\\1",
                    content,
                    count=1
                )
                
                with open(self.manual_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"✓ 已更新使用手册（新增 {command}）")
                return True
            else:
                logger.warning("未找到帮助信息章节，无法插入")
                return False
                
        except Exception as e:
            logger.error(f"更新使用手册失败: {e}")
            return False
    
    def preview_updates(self) -> str:
        """预览待更新内容"""
        changes = self.detect_changes()
        
        preview = []
        preview.append("=== 文档更新预览 ===\n")
        preview.append(f"变更文件: {len(changes['changed_files'])}")
        
        if changes['changed_files']:
            preview.append("\n受影响的文件：")
            for f in changes['changed_files'][:10]:
                preview.append(f"  - {f}")
        
        if changes['impacted_docs']:
            preview.append("\n需要更新的文档：")
            for d in changes['impacted_docs']:
                preview.append(f"  - {d}")
        
        preview.append(f"\n变更类型: {changes['change_type']}")
        
        return '\n'.join(preview)
    
    def apply_updates(self, message: str, confirmed: bool = False) -> Dict[str, bool]:
        """
        应用文档更新
        
        Args:
            message: 提交信息
            confirmed: 是否已确认
        
        Returns:
            {
                "changelog": bool,
                "manual": bool,
            }
        """
        if not self.config.enabled:
            logger.info("文档自动同步已禁用")
            return {"changelog": False, "manual": False}
        
        if self.config.require_confirm and not confirmed:
            preview = self.preview_updates()
            logger.info(f"\n{preview}")
            logger.info("\n请使用 --apply 选项确认应用更新")
            return {"changelog": False, "manual": False}
        
        results = {}
        
        if self.config.update_changelog:
            change_type = self._detect_change_type(message)
            results["changelog"] = self.update_changelog(change_type, message)
        
        if self.config.update_manual:
            commands = self.detect_changes().get("impacted_commands", [])
            for cmd in commands:
                results["manual"] = self.update_manual(cmd)
        
        return results
