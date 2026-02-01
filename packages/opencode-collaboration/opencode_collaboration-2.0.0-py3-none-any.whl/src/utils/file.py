"""文件操作工具模块。"""
import shutil
from pathlib import Path
from typing import List, Optional


def create_directory(path: str) -> None:
    """创建目录。"""
    Path(path).mkdir(parents=True, exist_ok=True)


def directory_exists(path: str) -> bool:
    """检查目录是否存在。"""
    return Path(path).is_dir()


def file_exists(path: str) -> bool:
    """检查文件是否存在。"""
    return Path(path).is_file()


def read_file(path: str) -> str:
    """读取文件内容。"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(path: str, content: str) -> None:
    """写入文件内容。"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def list_files(directory: str, extension: Optional[str] = None) -> List[str]:
    """列出目录中的文件。"""
    path = Path(directory)
    if extension:
        return [f.name for f in path.glob(f"*.{extension}")]
    return [f.name for f in path.glob("*") if f.is_file()]


def copy_file(src: str, dst: str) -> None:
    """复制文件。"""
    shutil.copy2(src, dst)


def remove_file(path: str) -> None:
    """删除文件。"""
    if Path(path).exists():
        Path(path).unlink()
