"""Git集成模块。"""
import subprocess
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass


class GitError(Exception):
    """Git操作异常基类。"""
    pass


class GitNotInstalledError(GitError):
    """Git未安装异常。"""
    pass


class GitRepositoryError(GitError):
    """Git仓库异常。"""
    pass


class GitOperationError(GitError):
    """Git操作失败异常。"""
    pass


class GitConflictError(GitError):
    """Git合并冲突异常。"""
    pass


class GitTimeoutError(GitError):
    """Git操作超时异常。"""
    pass


@dataclass
class GitTimeoutConfig:
    """Git超时配置。"""
    status: float = 10.0
    add: float = 5.0
    commit: float = 10.0
    push: float = 60.0
    pull: float = 30.0
    log: float = 10.0
    diff: float = 10.0
    default: float = 10.0


class GitHelper:
    """Git操作助手。"""

    DEFAULT_TIMEOUTS = {
        'status': 10.0,
        'add': 5.0,
        'commit': 10.0,
        'push': 60.0,
        'pull': 30.0,
        'log': 10.0,
        'diff': 10.0
    }

    def __init__(
        self,
        project_path: str,
        timeouts: Optional[Dict[str, float]] = None
    ):
        """初始化Git助手。

        Args:
            project_path: 项目路径
            timeouts: 超时配置（可选）
        """
        self.project_path = Path(project_path)
        self.timeouts = {**self.DEFAULT_TIMEOUTS, **(timeouts or {})}
        self._ensure_git_installed()

    def _ensure_git_installed(self) -> None:
        """检查Git是否已安装。"""
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise GitNotInstalledError("Git未安装或无法访问")

    def _run_git_command(
        self,
        *args,
        check: bool = True,
        timeout: Optional[float] = None
    ) -> subprocess.CompletedProcess:
        """运行Git命令。

        Args:
            *args: Git命令参数
            check: 是否检查返回码
            timeout: 超时时间（秒）

        Returns:
            subprocess.CompletedProcess: 命令执行结果

        Raises:
            GitTimeoutError: 命令超时
            GitOperationError: 命令执行失败
        """
        if timeout is None:
            timeout = self.timeouts.get('default', 10.0)

        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                check=check,
                timeout=timeout
            )
            return result
        except subprocess.TimeoutExpired:
            raise GitTimeoutError(f"Git命令超时 ({timeout}s): git {' '.join(args)}")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            if "conflict" in error_msg.lower():
                raise GitConflictError(error_msg)
            raise GitOperationError(f"Git命令执行失败: {error_msg}")
    
    def is_repository(self) -> bool:
        """检查是否为Git仓库。"""
        try:
            self._run_git_command("rev-parse", "--is-inside-work-tree", check=False)
            return True
        except GitOperationError:
            return False
    
    def init_repository(self) -> None:
        """初始化Git仓库。"""
        if not self.is_repository():
            self._run_git_command("init")
    
    def pull(self) -> bool:
        """拉取远程变更（带超时）。"""
        try:
            self._run_git_command("pull", timeout=self.timeouts.get('pull', 30.0))
            return True
        except GitConflictError:
            raise
        except GitTimeoutError:
            raise
        except GitOperationError:
            return False

    def push(self, message: str, push_all: bool = False) -> None:
        """提交并推送（带超时）。"""
        self._run_git_command("add", "-A", timeout=self.timeouts.get('add', 5.0))
        self._run_git_command("commit", "-m", message, timeout=self.timeouts.get('commit', 10.0))
        if push_all:
            self._run_git_command("push", "--all", timeout=self.timeouts.get('push', 60.0))
            self._run_git_command("push", "--tags", timeout=self.timeouts.get('push', 60.0))
        else:
            self._run_git_command("push", timeout=self.timeouts.get('push', 60.0))

    def push_to_remote(self, remote: str, branches: bool = True, tags: bool = True) -> None:
        """推送到指定远程仓库（带超时）。"""
        if branches:
            self._run_git_command("push", remote, "--all", timeout=self.timeouts.get('push', 60.0))
        if tags:
            self._run_git_command("push", remote, "--tags", timeout=self.timeouts.get('push', 60.0))

    def push_all_remotes(self, message: str) -> None:
        """提交并推送到所有远程仓库（带超时）。"""
        self._run_git_command("add", "-A", timeout=self.timeouts.get('add', 5.0))
        self._run_git_command("commit", "-m", message, timeout=self.timeouts.get('commit', 10.0))
        for remote in self.get_all_remotes():
            self.push_to_remote(remote)

    def add_remote(self, name: str, url: str) -> None:
        """添加远程仓库。"""
        self._run_git_command("remote", "add", name, url)

    def get_all_remotes(self) -> List[str]:
        """获取所有远程仓库名称。"""
        result = self._run_git_command("remote", "-v")
        remote_names = set()
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = line.split()
                if parts:
                    remote_names.add(parts[0])
        return list(remote_names)
    
    def create_branch(self, branch_name: str) -> None:
        """创建分支。"""
        self._run_git_command("checkout", "-b", branch_name)
    
    def switch_branch(self, branch_name: str) -> None:
        """切换分支。"""
        self._run_git_command("checkout", branch_name)
    
    def branch_exists(self, branch_name: str) -> bool:
        """检查分支是否存在。"""
        try:
            self._run_git_command("rev-parse", "--verify", f"refs/heads/{branch_name}", check=False)
            return True
        except GitOperationError:
            return False
    
    def create_tag(self, tag_name: str, message: str = "") -> None:
        """创建标签。"""
        if message:
            self._run_git_command("tag", "-a", tag_name, "-m", message)
        else:
            self._run_git_command("tag", tag_name)
    
    def get_current_branch(self) -> str:
        """获取当前分支名称。"""
        result = self._run_git_command("rev-parse", "--abbrev-ref", "HEAD")
        return result.stdout.strip()
    
    def get_remote_url(self) -> Optional[str]:
        """获取远程仓库URL。"""
        try:
            result = self._run_git_command("remote", "get-url", "origin", check=False)
            return result.stdout.strip() if result.stdout else None
        except GitOperationError:
            return None
    
    def has_local_changes(self) -> bool:
        """检查是否有未提交的本地修改（带超时）。"""
        result = self._run_git_command("status", "--porcelain", check=False, timeout=self.timeouts.get('status', 10.0))
        return bool(result.stdout.strip())

    def get_commit_hash(self, branch: str = "HEAD") -> str:
        """获取提交哈希（带超时）。"""
        result = self._run_git_command("rev-parse", branch, timeout=self.timeouts.get('log', 10.0))
        return result.stdout.strip()

    def get_commit_message(self, commit_hash: str = "HEAD") -> str:
        """获取提交信息（带超时）。"""
        result = self._run_git_command("log", "-1", "--format=%s", commit_hash, timeout=self.timeouts.get('log', 10.0))
        return result.stdout.strip()

    def get_all_branches(self) -> List[str]:
        """获取所有本地分支（带超时）。"""
        result = self._run_git_command("branch", "--list", timeout=self.timeouts.get('log', 10.0))
        return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

    def get_all_tags(self) -> List[str]:
        """获取所有标签（带超时）。"""
        result = self._run_git_command("tag", "-l", timeout=self.timeouts.get('log', 10.0))
        return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
    
    def delete_branch(self, branch_name: str) -> None:
        """删除分支。"""
        self._run_git_command("branch", "-d", branch_name)
    
    def delete_tag(self, tag_name: str) -> None:
        """删除标签。"""
        self._run_git_command("tag", "-d", tag_name)
