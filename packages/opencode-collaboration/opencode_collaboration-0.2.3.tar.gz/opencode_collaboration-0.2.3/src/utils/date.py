"""日期时间工具模块。"""
from datetime import datetime
from typing import List


def get_current_time() -> str:
    """获取当前时间（ISO 8601格式）。"""
    return datetime.now().isoformat()


def get_current_date() -> str:
    """获取当前日期（YYYY-MM-DD格式）。"""
    return datetime.now().strftime("%Y-%m-%d")


def format_time(timestamp: str) -> str:
    """格式化时间字符串。"""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return timestamp
