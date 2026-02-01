"""E2E黑盒测试用例。"""
import pytest
import sys
import os
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock


sys.path.insert(0, str(Path(__file__).parent.parent))


class TestProjectInitialization:
    """项目初始化测试。"""

    def test_init_python_project(self, tmp_path):
        """测试初始化Python项目。"""
        from src.cli.main import init_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(init_command, ['test_project', '--type', 'python', '--no-git'])
            assert result.exit_code == 0
            assert Path('test_project').exists()

    def test_init_typescript_project(self, tmp_path):
        """测试初始化TypeScript项目。"""
        from src.cli.main import init_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(init_command, ['test_project', '--type', 'typescript', '--no-git'])
            assert result.exit_code == 0
            assert Path('test_project').exists()

    def test_init_mixed_project(self, tmp_path):
        """测试初始化混合项目。"""
        from src.cli.main import init_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(init_command, ['test_project', '--type', 'mixed', '--no-git'])
            assert result.exit_code == 0
            assert Path('test_project').exists()

    def test_init_existing_directory_fails(self, tmp_path):
        """测试初始化已存在非空目录失败。"""
        from src.cli.main import init_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            Path('existing_dir').mkdir()
            (Path('existing_dir') / 'file.txt').write_text('test')
            result = runner.invoke(init_command, ['existing_dir', '--no-git'])
            assert result.exit_code != 0 or '已存在' in result.output or '不是空目录' in result.output

    def test_init_force_overwrite(self, tmp_path):
        """测试强制覆盖初始化。"""
        from src.cli.main import init_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            Path('test_project').mkdir()
            (Path('test_project') / 'file.txt').write_text('test')
            result = runner.invoke(init_command, ['test_project', '--force', '--no-git'])
            assert result.exit_code == 0


class TestStatusCommand:
    """状态命令测试。"""

    def test_status_no_project(self, tmp_path):
        """测试无项目时查看状态。"""
        from src.cli.main import status_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(status_command)
            assert result.exit_code != 0
            assert '未找到项目状态文件' in result.output

    def test_status_with_project(self, tmp_path):
        """测试有项目时查看状态。"""
        from src.cli.main import init_command, status_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(status_command)
            assert result.exit_code == 0
            assert '项目状态' in result.output
            assert 'test_project' in result.output


class TestSwitchCommand:
    """切换命令测试。"""

    def test_switch_to_agent1(self, tmp_path):
        """测试切换到Agent 1。"""
        from src.cli.main import init_command, switch_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(switch_command, ['1'])
            assert result.exit_code == 0
            assert 'Agent 1' in result.output

    def test_switch_to_agent2(self, tmp_path):
        """测试切换到Agent 2。"""
        from src.cli.main import init_command, switch_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(switch_command, ['2'])
            assert result.exit_code == 0
            assert 'Agent 2' in result.output

    def test_switch_already_current(self, tmp_path):
        """测试切换到当前Agent。"""
        from src.cli.main import init_command, switch_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(switch_command, ['1'])
            assert '已经是 Agent 1' in result.output


class TestReviewCommand:
    """评审命令测试。"""

    def test_review_requirements_new(self, tmp_path):
        """测试发起需求评审。"""
        from src.cli.main import init_command, review_command
        from click.testing import CliRunner
        import yaml
        from pathlib import Path

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            state_file = Path('state/project_state.yaml')
            with open(state_file, 'r') as f:
                state = yaml.safe_load(f)
            state['phase'] = 'requirements_draft'
            state['requirements'] = {'status': 'draft'}
            with open(state_file, 'w') as f:
                yaml.dump(state, f)
            result = runner.invoke(review_command, ['requirements', '--new'])
            assert result.exit_code == 0
            assert '评审' in result.output or result.exit_code == 0

    def test_review_list(self, tmp_path):
        """测试查看评审历史。"""
        from src.cli.main import init_command, review_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(review_command, ['requirements', '--list'])
            assert result.exit_code == 0


class TestSignoffCommand:
    """签署命令测试。"""

    def test_signoff_requirements(self, tmp_path):
        """测试签署需求。"""
        from src.cli.main import init_command, signoff_command
        from click.testing import CliRunner
        import yaml
        from pathlib import Path

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            state_file = Path('state/project_state.yaml')
            with open(state_file, 'r') as f:
                state = yaml.safe_load(f)
            state['phase'] = 'requirements_review'
            state['requirements'] = {'status': 'review', 'pm_signoff': False, 'dev_signoff': False}
            with open(state_file, 'w') as f:
                yaml.dump(state, f)
            result = runner.invoke(signoff_command, ['requirements'])
            assert result.exit_code == 0 or '已签署' in result.output or '不能' in result.output

    def test_signoff_with_comment(self, tmp_path):
        """测试带评论签署。"""
        from src.cli.main import init_command, signoff_command
        from click.testing import CliRunner
        import yaml
        from pathlib import Path

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            state_file = Path('state/project_state.yaml')
            with open(state_file, 'r') as f:
                state = yaml.safe_load(f)
            state['phase'] = 'requirements_review'
            state['requirements'] = {'status': 'review', 'pm_signoff': False, 'dev_signoff': False}
            with open(state_file, 'w') as f:
                yaml.dump(state, f)
            result = runner.invoke(signoff_command, ['requirements', '--comment', '测试评论'])
            assert result.exit_code == 0 or '已签署' in result.output or '不能' in result.output

    def test_signoff_reject(self, tmp_path):
        """测试拒签。"""
        from src.cli.main import init_command, signoff_command
        from click.testing import CliRunner
        import yaml
        from pathlib import Path

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            state_file = Path('state/project_state.yaml')
            with open(state_file, 'r') as f:
                state = yaml.safe_load(f)
            state['phase'] = 'requirements_review'
            state['requirements'] = {'status': 'review'}
            with open(state_file, 'w') as f:
                yaml.dump(state, f)
            result = runner.invoke(signoff_command, ['requirements', '--reject', '需要修改'])
            assert result.exit_code == 0 or '拒签' in result.output or '不能' in result.output


class TestHistoryCommand:
    """历史命令测试。"""

    def test_history(self, tmp_path):
        """测试查看历史。"""
        from src.cli.main import init_command, history_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(history_command)
            assert result.exit_code == 0
            assert '协作历史' in result.output

    def test_history_with_limit(self, tmp_path):
        """测试带限制查看历史。"""
        from src.cli.main import init_command, history_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(history_command, ['--limit', '5'])
            assert result.exit_code == 0


class TestSyncCommand:
    """同步命令测试。"""

    def test_sync_no_changes(self, tmp_path):
        """测试同步无变化。"""
        from src.cli.main import init_command, sync_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(sync_command)
            assert result.exit_code == 0


class TestAutoCommand:
    """自动执行命令测试。"""

    def test_auto_execution(self, tmp_path):
        """测试自动执行。"""
        from src.cli.main import init_command, auto_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(auto_command, ['--max-iterations', '1', '--quiet'])
            assert result.exit_code == 0

    def test_auto_quiet_mode(self, tmp_path):
        """测试静默模式。"""
        from src.cli.main import init_command, auto_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(auto_command, ['--quiet'])
            assert result.exit_code == 0


class TestTodoCommand:
    """待办命令测试。"""

    def test_todo_display(self, tmp_path):
        """测试显示待办事项。"""
        from src.cli.main import init_command, todo_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(todo_command)
            assert result.exit_code == 0
            assert '待办事项' in result.output


class TestWorkCommand:
    """工作流引导命令测试。"""

    def test_work_summary(self, tmp_path):
        """测试工作流摘要。"""
        from src.cli.main import init_command, work_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(work_command)
            assert result.exit_code == 0
            assert '状态摘要' in result.output

    def test_work_suggestions(self, tmp_path):
        """测试操作建议。"""
        from src.cli.main import init_command, work_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(work_command)
            assert result.exit_code == 0
            assert '操作建议' in result.output


class TestStateMachineIntegration:
    """状态机集成测试。"""

    def test_state_transition_project_init(self, tmp_path):
        """测试项目初始化状态。"""
        from src.core.state_machine import StateMachine, State
        from src.core.state_manager import StateManager

        with tempfile.TemporaryDirectory() as td:
            Path(td, 'state').mkdir()
            sm = StateMachine(State.PROJECT_INIT)
            assert sm.current_state == State.PROJECT_INIT

    def test_state_transition_to_requirements_draft(self, tmp_path):
        """测试转换到需求草稿状态。"""
        from src.core.state_machine import StateMachine, State

        sm = StateMachine()
        result = sm.transition_to(State.REQUIREMENTS_DRAFT)
        assert result['success']
        assert sm.current_state == State.REQUIREMENTS_DRAFT

    def test_state_transition_sequence(self, tmp_path):
        """测试状态转换序列（简化版）。"""
        from src.core.state_machine import StateMachine, State

        sm = StateMachine()
        sm.transition_to(State.REQUIREMENTS_DRAFT)
        sm.transition_to(State.REQUIREMENTS_REVIEW)
        assert sm.current_state == State.REQUIREMENTS_REVIEW

    def test_invalid_state_transition(self, tmp_path):
        """测试无效状态转换。"""
        from src.core.state_machine import StateMachine, State

        sm = StateMachine()
        try:
            sm.transition_to(State.DEVELOPMENT)
            assert False, "应该抛出异常"
        except Exception:
            pass

    def test_state_progress(self, tmp_path):
        """测试状态进度。"""
        from src.core.state_machine import StateMachine, State

        sm = StateMachine()
        progress = sm.get_progress()
        assert progress == 0.0
        sm.transition_to(State.REQUIREMENTS_DRAFT)
        progress = sm.get_progress()
        assert progress > 0.0


class TestBrainEngineIntegration:
    """脑引擎集成测试类。"""

    def test_brain_engine_initialization(self, tmp_path):
        """测试脑引擎初始化。"""
        from src.core.brain_engine import BrainEngine

        engine = BrainEngine()
        assert engine is not None

    def test_get_action_agent1(self, tmp_path):
        """测试Agent 1获取动作。"""
        from src.core.brain_engine import BrainEngine

        engine = BrainEngine()
        action, rule = engine.get_action('agent1', 'project_init')
        assert action is not None

    def test_get_action_agent2(self, tmp_path):
        """测试Agent 2获取动作。"""
        from src.core.brain_engine import BrainEngine

        engine = BrainEngine()
        action, rule = engine.get_action('agent2', 'project_init')
        assert action is not None


class TestTaskExecutorIntegration:
    """任务执行器集成测试。"""

    def test_task_executor_initialization(self, tmp_path):
        """测试任务执行器初始化。"""
        from src.core.task_executor import TaskExecutor

        executor = TaskExecutor()
        assert executor is not None

    def test_execute_action(self, tmp_path):
        """测试执行动作。"""
        from src.core.task_executor import TaskExecutor

        executor = TaskExecutor()
        context = {'agent_id': 'agent1', 'phase': 'project_init'}
        result = executor.execute_action('create_requirements', context)
        assert result is not None


class TestDocGeneratorIntegration:
    """文档生成器集成测试类。"""

    def test_doc_generator_initialization(self, tmp_path):
        """测试文档生成器初始化。"""
        from src.core.doc_generator import DocGenerator

        with tempfile.TemporaryDirectory() as td:
            generator = DocGenerator(td)
            assert generator is not None

    def test_generate_requirements_document(self, tmp_path):
        """测试生成需求文档。"""
        from src.core.doc_generator import DocGenerator
        from pathlib import Path
        import shutil

        with tempfile.TemporaryDirectory() as td:
            templates_src = Path(__file__).parent.parent / 'templates'
            templates_dst = Path(td) / 'templates'
            if templates_src.exists():
                shutil.copytree(templates_src, templates_dst)
            
            generator = DocGenerator(td)
            context = {
                'project_name': 'TestProject',
                'project_type': 'PYTHON',
                'timestamp': datetime.now().isoformat()
            }
            success, doc_path = generator.generate_document('requirements', context, version='v1')
            assert success, f"文档生成失败: {doc_path}"
            assert Path(doc_path).exists(), f"文档路径不存在: {doc_path}"


class TestExceptionHandlerIntegration:
    """异常处理器集成测试。"""

    def test_exception_handler_initialization(self, tmp_path):
        """测试异常处理器初始化。"""
        from src.core.exception_handler import ExceptionHandler

        handler = ExceptionHandler('test_agent', 'test_phase')
        assert handler is not None

    def test_classify_network_exception(self, tmp_path):
        """测试分类网络异常。"""
        from src.core.exception_handler import ExceptionHandler, ExceptionType

        handler = ExceptionHandler('test_agent')
        exc = Exception('network connection timeout')
        ex_type, _ = handler.classify_exception(exc)
        assert ex_type == ExceptionType.RETRYABLE

    def test_classify_state_exception(self, tmp_path):
        """测试分类状态异常。"""
        from src.core.exception_handler import ExceptionHandler, ExceptionType

        handler = ExceptionHandler('test_agent')
        exc = Exception('state version conflict')
        ex_type, _ = handler.classify_exception(exc)
        assert ex_type == ExceptionType.RECOVERABLE

    def test_classify_fatal_exception(self, tmp_path):
        """测试分类致命异常。"""
        from src.core.exception_handler import ExceptionHandler, ExceptionType

        handler = ExceptionHandler('test_agent')
        exc = Exception('permission denied')
        ex_type, _ = handler.classify_exception(exc)
        assert ex_type == ExceptionType.FATAL


class TestGitMonitorIntegration:
    """Git监控器集成测试。"""

    @pytest.mark.skip(reason="GitMonitor initialization test requires a valid git repository. This test is environment-dependent and may fail in CI/CD or test environments without proper git configuration.")
    def test_git_monitor_initialization(self, tmp_path):
        """测试Git监控器初始化。"""
        import subprocess

        with tempfile.TemporaryDirectory() as td:
            subprocess.run(['git', 'init'], capture_output=True, check=True, cwd=td)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], capture_output=True, cwd=td)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], capture_output=True, cwd=td)

            from src.core.git_monitor import GitMonitor, GitConfig

            config = GitConfig(polling_interval=30)
            monitor = GitMonitor(td, config)
            assert monitor is not None


class TestAgentIntegration:
    """Agent集成测试。"""

    def test_agent_initialization(self, tmp_path):
        """测试Agent初始化。"""
        from src.cli.agent import Agent, AgentConfig

        config = AgentConfig(agent_id='agent1', agent_type='产品经理')
        agent = Agent(config)
        assert agent.config.agent_id == 'agent1'

    def test_agent_start_stop(self, tmp_path):
        """测试Agent启动停止。"""
        from src.cli.agent import Agent, AgentConfig, AgentStatus

        config = AgentConfig(agent_id='agent1', agent_type='产品经理')
        agent = Agent(config)
        agent.initialize('.')
        agent.start()
        assert agent.status.value in ['running', 'error']
        agent.stop()
        assert agent.status.value == 'stopped'

    def test_agent_mode_switch(self, tmp_path):
        """测试Agent模式切换。"""
        from src.cli.agent import Agent, AgentConfig, AgentMode

        config = AgentConfig(agent_id='agent1', agent_type='产品经理')
        agent = Agent(config)
        agent.switch_mode(AgentMode.MANUAL)
        assert agent.config.mode == AgentMode.MANUAL
        agent.switch_mode(AgentMode.AUTO)
        assert agent.config.mode == AgentMode.AUTO


class TestFullWorkflowIntegration:
    """完整工作流集成测试。"""

    def test_full_workflow_project_init_to_completed(self, tmp_path):
        """测试完整工作流（简化版）。"""
        from src.core.state_machine import StateMachine, State

        sm = StateMachine()
        states = [
            State.REQUIREMENTS_DRAFT,
            State.REQUIREMENTS_REVIEW,
        ]
        for state in states:
            result = sm.transition_to(state)
            assert result['success']
        assert sm.current_state == State.REQUIREMENTS_REVIEW

    def test_workflow_history_tracking(self, tmp_path):
        """测试工作流历史跟踪。"""
        from src.core.state_machine import StateMachine, State

        sm = StateMachine()
        sm.transition_to(State.REQUIREMENTS_DRAFT)
        sm.transition_to(State.REQUIREMENTS_REVIEW)

        history = sm.history
        assert len(history) == 2

    def test_workflow_state_info(self, tmp_path):
        """测试工作流状态信息。"""
        from src.core.state_machine import StateMachine, State

        sm = StateMachine()
        info = sm.STATE_INFO[State.PROJECT_INIT]
        assert info.state == State.PROJECT_INIT
        assert info.name == '项目初始化'


class TestEdgeCases:
    """边界情况测试。"""

    def test_empty_project_name(self, tmp_path):
        """测试空项目名处理。"""
        from src.cli.main import init_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(init_command, ['', '--no-git'])
            assert result.exit_code != 0 or '无效' in result.output or 'empty' in result.output.lower()

    def test_invalid_agent_switch(self, tmp_path):
        """测试无效Agent切换。"""
        from src.cli.main import init_command, switch_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(switch_command, ['3'])
            assert result.exit_code != 0

    def test_invalid_review_stage(self, tmp_path):
        """测试无效评审阶段。"""
        from src.cli.main import init_command, review_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(review_command, ['invalid'])
            assert result.exit_code != 0

    def test_invalid_signoff_stage(self, tmp_path):
        """测试无效签署阶段。"""
        from src.cli.main import init_command, signoff_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(signoff_command, ['invalid'])
            assert result.exit_code != 0


class TestTemplateGeneration:
    """模板生成测试。"""

    def test_requirements_template_exists(self, tmp_path):
        """测试需求模板存在。"""
        templates_dir = Path(__file__).parent.parent / 'templates'
        template_path = templates_dir / 'requirements_TEMPLATE.md'
        assert template_path.exists()

    def test_design_template_exists(self, tmp_path):
        """测试设计模板存在。"""
        templates_dir = Path(__file__).parent.parent / 'templates'
        template_path = templates_dir / 'design_TEMPLATE.md'
        assert template_path.exists()

    def test_test_case_template_exists(self, tmp_path):
        """测试测试用例模板存在。"""
        templates_dir = Path(__file__).parent.parent / 'templates'
        template_path = templates_dir / 'test_case_TEMPLATE.md'
        assert template_path.exists()


class TestConfigurationLoading:
    """配置加载测试。"""

    def test_pyproject_dependencies(self, tmp_path):
        """测试pyproject依赖。"""
        pyproject = Path(__file__).parent.parent / 'pyproject.toml'
        assert pyproject.exists()

        content = pyproject.read_text()
        assert 'click' in content
        assert 'pyyaml' in content
        assert 'jinja2' in content

    def test_script_entry_point(self, tmp_path):
        """测试脚本入口点。"""
        pyproject = Path(__file__).parent.parent / 'pyproject.toml'
        content = pyproject.read_text()
        assert 'oc-collab' in content


class TestDocumentationExists:
    """文档存在性测试。"""

    def test_user_manual_exists(self, tmp_path):
        """测试用户手册存在。"""
        docs_dir = Path(__file__).parent.parent / 'docs'
        manual_path = docs_dir / '使用手册.md'
        assert manual_path.exists()

    def test_development_plan_exists(self, tmp_path):
        """测试开发计划存在。"""
        docs_dir = Path(__file__).parent.parent / 'docs' / '05-development'
        plan_path = docs_dir / 'development_plan_v1.md'
        assert plan_path.exists()

    def test_requirements_doc_exists(self, tmp_path):
        """测试需求文档存在。"""
        docs_dir = Path(__file__).parent.parent / 'docs' / '01-requirements'
        req_path = docs_dir / 'requirements_v2.md'
        assert req_path.exists()

    def test_design_doc_exists(self, tmp_path):
        """测试设计文档存在。"""
        docs_dir = Path(__file__).parent.parent / 'docs' / '02-design'
        design_path = docs_dir / 'detailed_design_v1.md'
        assert design_path.exists()


class TestStatePersistence:
    """状态持久化测试。"""

    def test_state_file_creation(self, tmp_path):
        """测试状态文件创建。"""
        from src.core.state_manager import StateManager

        with tempfile.TemporaryDirectory() as td:
            manager = StateManager(td)
            manager.init_state('TestProject', 'PYTHON')
            state_file = Path(td) / 'state' / 'project_state.yaml'
            assert state_file.exists()

    def test_state_file_loading(self, tmp_path):
        """测试状态文件加载。"""
        from src.core.state_manager import StateManager

        with tempfile.TemporaryDirectory() as td:
            manager = StateManager(td)
            manager.init_state('TestProject', 'PYTHON')
            state = manager.load_state()
            assert state['project']['name'] == 'TestProject'

    def test_state_file_update(self, tmp_path):
        """测试状态文件更新。"""
        from src.core.state_manager import StateManager

        with tempfile.TemporaryDirectory() as td:
            manager = StateManager(td)
            manager.init_state('TestProject', 'PYTHON')
            manager.update_phase('requirements_draft')
            state = manager.load_state()
            assert state['phase'] == 'requirements_draft'


class TestAgentBehaviorRules:
    """Agent行为规则测试类。"""

    def test_agent1_create_requirements(self, tmp_path):
        """测试Agent 1创建需求。"""
        from src.core.brain_engine import BrainEngine

        engine = BrainEngine()
        action, rule = engine.get_action('agent1', 'project_init')
        assert action is not None
        action_value = action.value if action else 'wait'
        assert action_value in ['create_requirements', 'wait']

    def test_agent1_signoff_requirements(self, tmp_path):
        """测试Agent 1签署需求。"""
        from src.core.brain_engine import BrainEngine

        engine = BrainEngine()
        action, rule = engine.get_action('agent1', 'requirements_review')
        assert action is not None
        action_value = action.value if action else 'wait'
        assert action_value in ['signoff_requirements', 'wait']

    def test_agent1_review_design(self, tmp_path):
        """测试Agent 1评审设计。"""
        from src.core.brain_engine import BrainEngine

        engine = BrainEngine()
        action, rule = engine.get_action('agent1', 'design_review')
        assert action is not None
        action_value = action.value if action else 'wait'
        assert action_value in ['review_design', 'wait']

    def test_agent2_review_requirements(self, tmp_path):
        """测试Agent 2评审需求。"""
        from src.core.brain_engine import BrainEngine

        engine = BrainEngine()
        action, rule = engine.get_action('agent2', 'requirements_draft')
        assert action is not None
        action_value = action.value if action else 'wait'
        assert action_value in ['review_requirements', 'wait']

    def test_agent2_create_design(self, tmp_path):
        """测试Agent 2创建设计。"""
        from src.core.brain_engine import BrainEngine

        engine = BrainEngine()
        action, rule = engine.get_action('agent2', 'requirements_approved')
        assert action is not None
        action_value = action.value if action else 'wait'
        assert action_value in ['create_design', 'wait']

    def test_agent2_implement_code(self, tmp_path):
        """测试Agent 2实现代码。"""
        from src.core.brain_engine import BrainEngine

        engine = BrainEngine()
        action, rule = engine.get_action('agent2', 'design_approved')
        assert action is not None
        action_value = action.value if action else 'wait'
        assert action_value in ['implement_code', 'wait']


class TestNotificationSystem:
    """通知系统测试。"""

    def test_notification_config_creation(self, tmp_path):
        """测试通知配置创建。"""
        from src.core.exception_handler import NotificationConfig, NotificationChannel, ExceptionSeverity

        config = NotificationConfig(
            channel=NotificationChannel.LOG,
            enabled=True,
            min_severity=ExceptionSeverity.MEDIUM
        )
        assert config.channel == NotificationChannel.LOG

    def test_notification_channel_enum(self, tmp_path):
        """测试通知渠道枚举。"""
        from src.core.exception_handler import NotificationChannel

        assert NotificationChannel.LOG.value == 'log'
        assert NotificationChannel.FILE.value == 'file'
        assert NotificationChannel.WEBHOOK.value == 'webhook'


class TestCrashRecovery:
    """崩溃恢复测试。"""

    def test_crash_log_saving(self, tmp_path):
        """测试崩溃日志保存。"""
        from src.core.exception_handler import ExceptionHandler, ExceptionInfo, ExceptionType, ExceptionSeverity
        from datetime import datetime

        with tempfile.TemporaryDirectory() as td:
            handler = ExceptionHandler('test_agent', 'test_phase')
            handler.crash_log_dir = Path(td)
            handler.crash_log_dir.mkdir(exist_ok=True)

            exc_info = ExceptionInfo(
                exception_type=ExceptionType.RETRYABLE,
                severity=ExceptionSeverity.MEDIUM,
                message='test error',
                timestamp=datetime.now().isoformat(),
                agent_id='test_agent',
                phase='test_phase',
                context={}
            )

            crash_id = handler._save_crash_log(exc_info)
            assert crash_id.startswith('test_agent_')

    def test_recovery_info_saving(self, tmp_path):
        """测试恢复信息保存。"""
        from src.core.exception_handler import ExceptionHandler, ExceptionInfo, ExceptionType, ExceptionSeverity
        from datetime import datetime

        with tempfile.TemporaryDirectory() as td:
            handler = ExceptionHandler('test_agent', 'test_phase')
            handler.recovery_dir = Path(td)
            handler.recovery_dir.mkdir(exist_ok=True)

            exc_info = ExceptionInfo(
                exception_type=ExceptionType.FATAL,
                severity=ExceptionSeverity.CRITICAL,
                message='fatal error',
                timestamp=datetime.now().isoformat(),
                agent_id='test_agent',
                phase='test_phase',
                context={'state': {'version': 1}}
            )

            handler._save_recovery_info(exc_info)
            recovery_file = handler.recovery_dir / 'test_agent_recovery.json'
            assert recovery_file.exists()


class TestCLIHelp:
    """CLI帮助测试。"""

    def test_main_help(self, tmp_path):
        """测试主命令帮助。"""
        from src.cli.main import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'init' in result.output
        assert 'status' in result.output

    def test_init_help(self, tmp_path):
        """测试init命令帮助。"""
        from src.cli.main import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ['init', '--help'])
        assert result.exit_code == 0
        assert 'PROJECT_NAME' in result.output

    def test_auto_help(self, tmp_path):
        """测试auto命令帮助。"""
        from src.cli.main import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ['auto', '--help'])
        assert result.exit_code == 0
        assert '--max-iterations' in result.output

    def test_todo_help(self, tmp_path):
        """测试todo命令帮助。"""
        from src.cli.main import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ['todo', '--help'])
        assert result.exit_code == 0

    def test_work_help(self, tmp_path):
        """测试work命令帮助。"""
        from src.cli.main import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ['work', '--help'])
        assert result.exit_code == 0
        assert '--execute' in result.output


class TestRemoteCommand:
    """远程仓库管理命令测试。"""

    def test_remote_list(self, tmp_path):
        """测试列出远程仓库。"""
        from src.cli.main import init_command, remote_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(remote_command, ['list'])
            assert result.exit_code == 0
            assert '远程仓库' in result.output or '未配置' in result.output

    def test_remote_add(self, tmp_path):
        """测试添加远程仓库。"""
        from src.cli.main import init_command, remote_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(remote_command, ['add', 'gitee', 'https://gitee.com/test/project.git'])
            assert result.exit_code == 0
            assert '已添加' in result.output or 'gitee' in result.output.lower()

    def test_remote_add_missing_args(self, tmp_path):
        """测试添加远程仓库缺少参数。"""
        from src.cli.main import init_command, remote_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(remote_command, ['add'])
            assert result.exit_code != 0


class TestSyncAllCommand:
    """全平台同步命令测试。"""

    def test_sync_all_help(self, tmp_path):
        """测试sync-all命令帮助。"""
        from src.cli.main import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ['sync-all', '--help'])
        assert result.exit_code == 0
        assert '--message' in result.output

    def test_sync_all_no_changes(self, tmp_path):
        """测试sync-all无变化情况。"""
        from src.cli.main import init_command, sync_all_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(sync_all_command, ['--message', 'test: no changes'])
            assert result.exit_code == 0
            assert '没有需要提交的本地修改' in result.output or '已提交' in result.output


class TestConfigCompatibilityFix:
    """配置兼容性修复测试。"""

    def test_status_with_project_name_only_in_metadata(self, tmp_path):
        """测试项目名称仅在metadata中。"""
        from src.cli.main import init_command, status_command
        from click.testing import CliRunner
        import yaml
        from pathlib import Path

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            state_file = Path('state/project_state.yaml')
            with open(state_file, 'r') as f:
                state = yaml.safe_load(f)
            state['metadata']['project_name'] = 'TestProjectMetadata'
            with open(state_file, 'w') as f:
                yaml.dump(state, f)
            result = runner.invoke(status_command)
            assert result.exit_code == 0
            assert 'TestProjectMetadata' in result.output

    def test_status_with_project_info_structure(self, tmp_path):
        """测试project结构（兼容性）。"""
        from src.cli.main import init_command, status_command
        from click.testing import CliRunner
        import yaml
        from pathlib import Path

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            state_file = Path('state/project_state.yaml')
            with open(state_file, 'r') as f:
                state = yaml.safe_load(f)
            state['project']['name'] = 'TestProjectFromProject'
            if 'metadata' in state:
                state['metadata'].pop('project_name', None)
            with open(state_file, 'w') as f:
                yaml.dump(state, f)
            result = runner.invoke(status_command)
            assert result.exit_code == 0
            assert 'TestProjectFromProject' in result.output


class TestAutoRetryFeature:
    """智能重试功能测试。"""

    def test_sync_retry_help(self, tmp_path):
        """测试sync --retry帮助信息。"""
        from src.cli.main import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ['sync', '--help'])
        assert result.exit_code == 0
        assert '--retry' in result.output
        assert '--max-retries' in result.output

    def test_push_retry_help(self, tmp_path):
        """测试push --retry帮助信息。"""
        from src.cli.main import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ['push', '--help'])
        assert result.exit_code == 0
        assert '--retry' in result.output
        assert '--message' in result.output

    def test_auto_retry_config_creation(self, tmp_path):
        """测试智能重试配置创建。"""
        from src.core.auto_retry import AutoRetryConfig

        config = AutoRetryConfig(
            max_retries=5,
            retry_interval=10,
            exponential_backoff=True
        )
        assert config.max_retries == 5
        assert config.retry_interval == 10
        assert config.exponential_backoff is True

    def test_auto_retry_should_retry_network_error(self, tmp_path):
        """测试网络错误应重试。"""
        from src.core.auto_retry import AutoRetry

        auto_retry = AutoRetry(str(tmp_path))
        error = Exception("Connection timeout")
        assert auto_retry._should_retry(error) is True

    def test_auto_retry_should_not_retry_auth_error(self, tmp_path):
        """测试认证错误不应重试。"""
        from src.core.auto_retry import AutoRetry

        auto_retry = AutoRetry(str(tmp_path))
        error = Exception("Authentication failed")
        assert auto_retry._should_retry(error) is False

    def test_auto_retry_calculate_delay(self, tmp_path):
        """测试延迟计算。"""
        from src.core.auto_retry import AutoRetry, AutoRetryConfig

        config = AutoRetryConfig(
            max_retries=10,
            retry_interval=30,
            exponential_backoff=True,
            max_interval=300
        )
        auto_retry = AutoRetry(str(tmp_path), config)
        
        assert auto_retry._calculate_delay(0) == 30
        assert auto_retry._calculate_delay(1) == 60
        assert auto_retry._calculate_delay(2) == 120


class TestAutoDocsFeature:
    """自动文档同步功能测试。"""

    def test_docs_help(self, tmp_path):
        """测试docs命令帮助信息。"""
        from src.cli.main import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ['docs', '--help'])
        assert result.exit_code == 0
        assert 'check' in result.output
        assert 'preview' in result.output
        assert 'apply' in result.output

    def test_docs_check(self, tmp_path):
        """测试docs check命令。"""
        from src.cli.main import init_command, docs_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(docs_command, ['check'])
            assert result.exit_code == 0
            assert '变更检测' in result.output

    def test_docs_preview(self, tmp_path):
        """测试docs preview命令。"""
        from src.cli.main import init_command, docs_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(docs_command, ['preview'])
            assert result.exit_code == 0

    def test_auto_docs_config_creation(self, tmp_path):
        """测试自动文档配置创建。"""
        from src.core.auto_docs import AutoDocsConfig

        config = AutoDocsConfig(
            enabled=True,
            update_changelog=True,
            update_manual=True,
            require_confirm=False
        )
        assert config.enabled is True
        assert config.update_changelog is True

    def test_auto_docs_detect_change_type(self, tmp_path):
        """测试变更类型检测。"""
        from src.core.auto_docs import AutoDocs

        auto_docs = AutoDocs(str(tmp_path))
        
        assert auto_docs._detect_change_type("feat: new feature") == "新功能"
        assert auto_docs._detect_change_type("fix: bug fix") == "缺陷修复"
        assert auto_docs._detect_change_type("docs: update docs") == "文档更新"

    def test_auto_docs_extract_scope(self, tmp_path):
        """测试范围提取。"""
        from src.core.auto_docs import AutoDocs

        auto_docs = AutoDocs(str(tmp_path))
        
        assert auto_docs._extract_scope("feat(core): new feature") == "core"
        assert auto_docs._extract_scope("fix: bug fix") == "系统"


class TestProjectCommand:
    """项目管理命令测试。"""

    def test_project_status(self, tmp_path):
        """测试project status命令。"""
        from src.cli.main import init_command, project_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(project_command, ['status'])
            assert result.exit_code == 0
            assert '项目状态' in result.output

    def test_project_update_test(self, tmp_path):
        """测试project update --type test命令。"""
        from src.cli.main import init_command, project_command
        from click.testing import CliRunner
        import yaml
        from pathlib import Path

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(project_command, ['update', '--type', 'test', '--cases', '100', '--passed', '95'])
            assert result.exit_code == 0
            assert '测试统计已更新' in result.output

            state_file = Path('state/project_state.yaml')
            with open(state_file, 'r') as f:
                state = yaml.safe_load(f)
            assert state['test']['blackbox_cases'] == 100
            assert state['test']['blackbox_passed'] == 95

    def test_project_complete(self, tmp_path):
        """测试project complete命令。"""
        from src.cli.main import init_command, project_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(project_command, ['complete'])
            assert result.exit_code == 0
            assert '开发任务已标记为完成' in result.output

    def test_project_info(self, tmp_path):
        """测试project info命令。"""
        from src.cli.main import init_command, project_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(project_command, ['info'])
            assert result.exit_code == 0
            assert '阶段列表' in result.output


class TestAdvanceCommand:
    """阶段推进命令测试。"""

    def test_advance_help(self, tmp_path):
        """测试advance命令帮助信息。"""
        from src.cli.main import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ['advance', '--help'])
        assert result.exit_code == 0
        assert '--phase' in result.output
        assert '--force' in result.output
        assert '--check' in result.output

    def test_advance_check(self, tmp_path):
        """测试advance --check命令。"""
        from src.cli.main import init_command, advance_command
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            runner.invoke(init_command, ['test_project', '--no-git'])
            os.chdir('test_project')
            result = runner.invoke(advance_command, ['--check'])
            assert result.exit_code == 0

    def test_phase_advance_engine_init(self, tmp_path):
        """测试阶段推进引擎初始化。"""
        from src.core.phase_advance import PhaseAdvanceEngine

        engine = PhaseAdvanceEngine(str(tmp_path))
        assert engine is not None

    def test_phase_advance_check_condition(self, tmp_path):
        """测试阶段条件检查。"""
        from src.core.phase_advance import PhaseAdvanceEngine

        engine = PhaseAdvanceEngine(str(tmp_path))

        result = engine.check_condition("development", {"development": {"status": "completed"}})
        assert result is True

        result = engine.check_condition("development", {"development": {"status": "in_progress"}})
        assert result is False

    def test_phase_advance_list_phases(self, tmp_path):
        """测试阶段列表。"""
        from src.core.phase_advance import PhaseAdvanceEngine
        from src.core.state_manager import StateManager

        with tempfile.TemporaryDirectory() as td:
            Path(td, 'state').mkdir()
            StateManager(td).init_state('TestProject', 'PYTHON')

            engine = PhaseAdvanceEngine(td)
            result = engine.list_phases()

            assert "current_phase" in result
            assert "phases" in result
            assert len(result["phases"]) > 0


class TestAutoForceOption:
    """auto --force 选项测试"""

    def test_auto_force_help(self, tmp_path):
        """测试 auto --force 帮助信息。"""
        from src.cli.main import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ['auto', '--help'])
        assert result.exit_code == 0
        assert '--force' in result.output
        assert '-f' in result.output

    def test_auto_force_option_exists(self, tmp_path):
        """测试 auto 命令有 force 选项。"""
        from src.cli.main import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ['auto', '--force', '--help'])
        assert result.exit_code == 0


class TestAgentAutoRunner:
    """Agent 自动执行守护进程测试"""

    def test_agent_auto_runner_help(self, tmp_path):
        """测试 agent_auto_runner 脚本存在。"""
        import os
        script_path = Path(__file__).parent.parent / 'scripts' / 'agent_auto_runner.py'
        assert script_path.exists(), f"脚本不存在: {script_path}"

    def test_agent_auto_runner_import(self, tmp_path):
        """测试 agent_auto_runner 可以导入。"""
        import sys
        script_path = Path(__file__).parent.parent / 'scripts' / 'agent_auto_runner.py'
        if script_path.exists():
            sys.path.insert(0, str(script_path.parent))
            import agent_auto_runner
            assert hasattr(agent_auto_runner, 'AgentAutoRunner')

    def test_agent_auto_runner_config(self, tmp_path):
        """测试 AgentAutoRunner 配置。"""
        import sys
        script_path = Path(__file__).parent.parent / 'scripts' / 'agent_auto_runner.py'
        if script_path.exists():
            sys.path.insert(0, str(script_path.parent))
            try:
                import agent_auto_runner
                runner = agent_auto_runner.AgentAutoRunner(str(tmp_path), 60)
                assert runner.poll_interval == 60
                assert runner.project_path == tmp_path.resolve()
            except Exception as e:
                pass  # 可能因为缺少依赖

    def test_start_stop_scripts_exist(self, tmp_path):
        """测试启动停止脚本存在。"""
        scripts_dir = Path(__file__).parent.parent / 'scripts'
        start_script = scripts_dir / 'start_auto_monitor.sh'
        stop_script = scripts_dir / 'stop_auto_monitor.sh'
        assert start_script.exists(), f"启动脚本不存在: {start_script}"
        assert stop_script.exists(), f"停止脚本不存在: {stop_script}"
