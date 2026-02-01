"""Git监控器单元测试。"""
import pytest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock


sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.git_monitor import (
    GitMonitor, GitConfig, GitMonitorError, GitNotInstalledError,
    NotRepositoryError, ChangeType, CommitInfo, ChangeInfo, GitEvent
)


class TestGitConfig:
    """Git配置测试类。"""
    
    def test_default_config(self):
        """测试默认配置。"""
        config = GitConfig()
        
        assert config.polling_interval == 30
        assert config.max_polling_interval == 300
        assert config.enable_exponential_backoff == True
        assert config.enable_webhook == False
    
    def test_custom_config(self):
        """测试自定义配置。"""
        config = GitConfig(
            polling_interval=60,
            max_polling_interval=600,
            enable_webhook=True,
            webhook_url="http://example.com/webhook"
        )
        
        assert config.polling_interval == 60
        assert config.max_polling_interval == 600
        assert config.enable_webhook == True
        assert config.webhook_url == "http://example.com/webhook"
    
    def test_polling_interval_bounds(self):
        """测试轮询间隔边界。"""
        config = GitConfig(polling_interval=5)
        assert config.polling_interval == 10
        
        config = GitConfig(polling_interval=1000)
        assert config.polling_interval == 1000


class TestGitMonitor:
    """Git监控器测试类。"""
    
    @pytest.fixture
    def temp_git_repo(self):
        """创建临时Git仓库。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            os.system("git init")
            os.system("git config user.email 'test@example.com'")
            os.system("git config user.name 'Test User'")
            
            yield tmpdir
    
    @pytest.fixture
    def git_monitor(self, temp_git_repo):
        """创建Git监控器实例。"""
        config = GitConfig(polling_interval=30)
        return GitMonitor(temp_git_repo, config)
    
    def test_initialization(self, git_monitor):
        """测试初始化。"""
        assert git_monitor._running == False
        assert git_monitor._current_poll_interval == 30
        assert isinstance(git_monitor.config, GitConfig)
    
    def test_get_current_branch(self, git_monitor):
        """测试获取当前分支。"""
        branch = git_monitor.get_current_branch()
        assert branch == "master" or branch == "main"
    
    def test_get_commit_hash(self, git_monitor):
        """测试获取提交哈希。"""
        commit_hash = git_monitor.get_commit_hash()
        assert commit_hash is not None
        assert len(commit_hash) == 40
    
    def test_get_commit_info(self, git_monitor):
        """测试获取提交信息。"""
        commit_hash = git_monitor.get_commit_hash()
        commit_info = git_monitor.get_commit_info(commit_hash)
        
        assert commit_info is not None
        assert commit_info.hash == commit_hash
        assert len(commit_info.short_hash) == 7
    
    def test_get_new_commits_empty(self, git_monitor):
        """测试获取新提交（无新提交）。"""
        commits = git_monitor.get_new_commits()
        assert len(commits) == 0
    
    def test_detect_changes_empty(self, git_monitor):
        """测试检测变更（无变更）。"""
        events = git_monitor.detect_changes()
        assert len(events) == 0
    
    def test_detect_state_file_changes_no_file(self, git_monitor):
        """测试检测状态文件变更（文件不存在）。"""
        result = git_monitor.detect_state_file_changes()
        assert result["has_changes"] == False
        assert result["reason"] == "状态文件不存在"
    
    def test_get_status_summary(self, git_monitor):
        """测试获取监控状态摘要。"""
        summary = git_monitor.get_status_summary()
        
        assert "project_path" in summary
        assert "current_branch" in summary
        assert "polling_interval" in summary
        assert "is_running" in summary
        assert "config" in summary
    
    def test_reset_processed_commits(self, git_monitor):
        """测试重置已处理提交。"""
        git_monitor._processed_commits.add("abc123")
        git_monitor._last_commit = "abc123"
        
        git_monitor.reset_processed_commits()
        
        assert len(git_monitor._processed_commits) == 0
        assert git_monitor._last_commit is None
    
    def test_add_callback(self, git_monitor):
        """测试添加回调函数。"""
        callback = MagicMock()
        git_monitor.add_callback(callback)
        
        assert callback in git_monitor._callbacks
    
    def test_get_status_summary_remote_url(self, git_monitor):
        """测试获取远程URL（可能为None）。"""
        summary = git_monitor.get_status_summary()
        assert "remote_url" in summary


class TestGitMonitorEdgeCases:
    """Git监控器边界情况测试类。"""
    
    def test_not_git_repository(self):
        """测试非Git仓库。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(NotRepositoryError):
                GitMonitor(tmpdir)
    
    @patch('subprocess.run')
    def test_git_not_installed(self, mock_run):
        """测试Git未安装。"""
        mock_run.side_effect = FileNotFoundError()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(GitNotInstalledError):
                GitMonitor(tmpdir)


class TestCommitInfo:
    """提交信息测试类。"""
    
    def test_commit_info_creation(self):
        """测试提交信息创建。"""
        commit = CommitInfo(
            hash="abc123def456",
            short_hash="abc123d",
            message="Test commit",
            author="Test User",
            timestamp="2024-01-01 00:00:00"
        )
        
        assert commit.hash == "abc123def456"
        assert commit.short_hash == "abc123d"
        assert commit.message == "Test commit"
        assert len(commit.files) == 0


class TestChangeInfo:
    """变更信息测试类。"""
    
    def test_change_info_added(self):
        """测试新增文件变更。"""
        change = ChangeInfo(
            file_path="src/main.py",
            change_type=ChangeType.ADDED
        )
        
        assert change.file_path == "src/main.py"
        assert change.change_type == ChangeType.ADDED
    
    def test_change_info_modified(self):
        """测试修改文件变更。"""
        change = ChangeInfo(
            file_path="src/main.py",
            change_type=ChangeType.MODIFIED
        )
        
        assert change.change_type == ChangeType.MODIFIED
    
    def test_change_info_deleted(self):
        """测试删除文件变更。"""
        change = ChangeInfo(
            file_path="src/main.py",
            change_type=ChangeType.DELETED
        )
        
        assert change.change_type == ChangeType.DELETED


class TestGitEvent:
    """Git事件测试类。"""
    
    def test_git_event_creation(self):
        """测试Git事件创建。"""
        commit = CommitInfo(
            hash="abc123",
            short_hash="abc123",
            message="Test",
            author="Test",
            timestamp="2024-01-01"
        )
        
        event = GitEvent(
            event_type="new_commit",
            commit=commit,
            branch="main"
        )
        
        assert event.event_type == "new_commit"
        assert event.commit == commit
        assert event.branch == "main"
        assert len(event.changes) == 0


class TestChangeType:
    """变更类型测试类。"""
    
    def test_change_type_values(self):
        """测试变更类型枚举值。"""
        assert ChangeType.ADDED.value == "added"
        assert ChangeType.MODIFIED.value == "modified"
        assert ChangeType.DELETED.value == "deleted"
        assert ChangeType.RENAMED.value == "renamed"
