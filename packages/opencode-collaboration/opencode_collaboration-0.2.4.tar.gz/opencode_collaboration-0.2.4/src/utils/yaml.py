"""YAML 读写工具模块。"""
import yaml
from pathlib import Path
from typing import Any, Dict


def load_yaml(file_path: str) -> Dict[str, Any]:
    """加载YAML文件。"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML解析失败: {e}")


def save_yaml(file_path: str, data: Dict[str, Any]) -> None:
    """保存YAML文件。"""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
