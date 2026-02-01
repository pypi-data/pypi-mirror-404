import pytest
"""Agent行为集成测试。"""
import tempfile
import os
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.brain_engine import BrainEngine, AgentType, ActionType, Rule, Condition
from src.core.task_executor import TaskExecutor, TaskPriority
from src.core.state_machine import StateMachine, State


class TestAgent1Rules:
    """Agent 1行为规则测试类。"""
    
    @pytest.fixture
    def brain_engine(self):
        """创建大脑引擎实例。"""
        return BrainEngine()
    
    def test_create_requirements_rule(self, brain_engine):
        """测试创建需求规则匹配。"""
        action, rule = brain_engine.get_action(
            agent_type="agent1",
            phase="project_init"
        )
        
        assert action == ActionType.CREATE_REQUIREMENTS
        assert rule is not None
        assert rule.id == "agent1-create-requirements"
        assert rule.priority == 100
    
    def test_signoff_requirements_rule(self, brain_engine):
        """测试签署需求规则匹配。"""
        action, rule = brain_engine.get_action(
            agent_type="agent1",
            phase="requirements_review",
            signoff={"requirements": {"pm_signoff": False, "dev_signoff": True}}
        )
        
        assert action == ActionType.SIGNOFF_REQUIREMENTS
        assert rule is not None
        assert rule.id == "agent1-signoff-requirements"
    
    def test_review_design_rule(self, brain_engine):
        """测试评审设计规则匹配。"""
        action, rule = brain_engine.get_action(
            agent_type="agent1",
            phase="design_review"
        )
        
        assert action == ActionType.REVIEW_DESIGN
        assert rule is not None
        assert rule.id == "agent1-review-design"
    
    def test_execute_blackbox_test_rule(self, brain_engine):
        """测试执行黑盒测试规则匹配。"""
        action, rule = brain_engine.get_action(
            agent_type="agent1",
            phase="testing"
        )
        
        assert action == ActionType.EXECUTE_BLACKBOX_TEST
        assert rule is not None
        assert rule.id == "agent1-execute-blackbox-test"
    
    def test_execute_deployment_rule(self, brain_engine):
        """测试执行部署规则匹配。"""
        action, rule = brain_engine.get_action(
            agent_type="agent1",
            phase="deployment"
        )
        
        assert action == ActionType.EXECUTE_DEPLOYMENT
        assert rule is not None
        assert rule.id == "agent1-deploy"
    
    def test_agent1_all_phases(self, brain_engine):
        """测试Agent 1所有阶段的动作。"""
        phase_actions = {
            "project_init": ActionType.CREATE_REQUIREMENTS,
            "requirements_review": ActionType.SIGNOFF_REQUIREMENTS,
            "design_review": ActionType.REVIEW_DESIGN,
            "testing": ActionType.EXECUTE_BLACKBOX_TEST,
            "deployment": ActionType.EXECUTE_DEPLOYMENT
        }
        
        for phase, expected_action in phase_actions.items():
            action, rule = brain_engine.get_action(
                agent_type="agent1",
                phase=phase,
                signoff={"requirements": {"pm_signoff": True, "dev_signoff": True}}
            )
            assert action == expected_action, f"阶段 {phase} 预期动作 {expected_action}，实际 {action}"


class TestAgent2Rules:
    """Agent 2行为规则测试类。"""
    
    @pytest.fixture
    def brain_engine(self):
        """创建大脑引擎实例。"""
        return BrainEngine()
    
    def test_review_requirements_rule(self, brain_engine):
        """测试评审需求规则匹配。"""
        action, rule = brain_engine.get_action(
            agent_type="agent2",
            phase="requirements_draft"
        )
        
        assert action == ActionType.REVIEW_REQUIREMENTS
        assert rule is not None
        assert rule.id == "agent2-review-requirements"
        assert rule.priority == 100
    
    def test_signoff_requirements_rule(self, brain_engine):
        """测试签署需求规则匹配。"""
        action, rule = brain_engine.get_action(
            agent_type="agent2",
            phase="requirements_review",
            signoff={"requirements": {"pm_signoff": True, "dev_signoff": False}}
        )
        
        assert action == ActionType.SIGNOFF_REQUIREMENTS
        assert rule is not None
        assert rule.id == "agent2-signoff-requirements"
    
    def test_create_design_rule(self, brain_engine):
        """测试创建设计规则匹配。"""
        action, rule = brain_engine.get_action(
            agent_type="agent2",
            phase="requirements_approved"
        )
        
        assert action == ActionType.CREATE_DESIGN
        assert rule is not None
        assert rule.id == "agent2-create-design"
    
    def test_implement_code_rule(self, brain_engine):
        """测试实现代码规则匹配。"""
        action, rule = brain_engine.get_action(
            agent_type="agent2",
            phase="design_approved"
        )
        
        assert action == ActionType.IMPLEMENT_CODE
        assert rule is not None
        assert rule.id == "agent2-implement-code"
    
    def test_fix_bugs_rule(self, brain_engine):
        """测试修复Bug规则匹配。"""
        action, rule = brain_engine.get_action(
            agent_type="agent2",
            phase="development",
            pending_issues=0
        )
        
        assert action == ActionType.FIX_BUGS
        assert rule is not None
        assert rule.id == "agent2-fix-bugs"
    
    def test_agent2_all_phases(self, brain_engine):
        """测试Agent 2所有阶段的动作。"""
        phase_actions = {
            "requirements_draft": ActionType.REVIEW_REQUIREMENTS,
            "requirements_review": ActionType.SIGNOFF_REQUIREMENTS,
            "requirements_approved": ActionType.CREATE_DESIGN,
            "design_approved": ActionType.IMPLEMENT_CODE,
            "development": ActionType.FIX_BUGS
        }
        
        for phase, expected_action in phase_actions.items():
            action, rule = brain_engine.get_action(
                agent_type="agent2",
                phase=phase,
                pending_issues=0,
                signoff={"requirements": {"pm_signoff": True, "dev_signoff": True}}
            )
            assert action == expected_action, f"阶段 {phase} 预期动作 {expected_action}，实际 {action}"


class TestTaskStrategies:
    """任务执行策略测试类。"""
    
    @pytest.fixture
    def task_executor(self):
        """创建任务执行器实例。"""
        return TaskExecutor()
    
    def test_all_strategies_registered(self, task_executor):
        """测试所有策略已注册。"""
        expected_types = [
            "create_requirements",
            "review_requirements",
            "signoff_requirements",
            "create_design",
            "review_design",
            "execute_blackbox_test",
            "execute_deployment",
            "implement_code",
            "fix_bugs"
        ]
        
        for task_type in expected_types:
            strategy = task_executor.get_strategy(task_type)
            assert strategy is not None, f"策略 {task_type} 未注册"
    
    def test_create_requirements_strategy(self, task_executor):
        """测试创建需求策略。"""
        context = {"project_name": "TestProject"}
        
        task = task_executor.create_task(
            name="创建需求",
            task_type="create_requirements",
            params=context
        )
        
        result = task_executor.execute_task(task, context)
        
        assert result.success == True
        assert "TestProject" in result.message
        assert len(result.files_created) == 1
        assert result.files_created[0].endswith("requirements_TestProject_v1.md")
    
    def test_signoff_requirements_strategy(self, task_executor):
        """测试签署需求策略。"""
        context = {"agent_id": "agent1"}
        
        task = task_executor.create_task(
            name="签署需求",
            task_type="signoff_requirements",
            params=context
        )
        
        result = task_executor.execute_task(task, context)
        
        assert result.success == True
        assert "agent1" in result.message
    
    def test_create_design_strategy(self, task_executor):
        """测试创建设计策略。"""
        context = {"project_name": "TestProject"}
        
        task = task_executor.create_task(
            name="创建设计",
            task_type="create_design",
            params=context
        )
        
        result = task_executor.execute_task(task, context)
        
        assert result.success == True
        assert len(result.files_created) == 1
        assert result.files_created[0].endswith("detailed_design_TestProject_v1.md")
    
    def test_execute_action_method(self, task_executor):
        """测试execute_action方法。"""
        context = {"project_name": "TestProject"}
        
        result = task_executor.execute_action("create_requirements", context)
        
        assert result.success == True
        assert "TestProject" in result.message


class TestBrainEngineTaskIntegration:
    """大脑引擎与任务执行器集成测试类。"""
    
    @pytest.fixture
    def brain_engine(self):
        """创建大脑引擎实例。"""
        return BrainEngine()
    
    @pytest.fixture
    def task_executor(self):
        """创建任务执行器实例。"""
        return TaskExecutor()
    
    def test_agent1_full_workflow(self, brain_engine, task_executor):
        """测试Agent 1完整工作流程。"""
        workflow = [
            ("project_init", "create_requirements"),
            ("requirements_review", "signoff_requirements"),
            ("design_review", "review_design"),
            ("testing", "execute_blackbox_test"),
            ("deployment", "execute_deployment")
        ]
        
        for phase, action_type in workflow:
            action, rule = brain_engine.get_action(
                agent_type="agent1",
                phase=phase,
                signoff={"requirements": {"pm_signoff": True, "dev_signoff": True}}
            )
            
            assert action.value == action_type, f"阶段 {phase} 预期动作 {action_type}，实际 {action.value}"
            
            result = task_executor.execute_action(action.value, {"project_name": "TestProject"})
            assert result.success == True, f"阶段 {phase} 任务执行失败: {result.message}"
    
    def test_agent2_full_workflow(self, brain_engine, task_executor):
        """测试Agent 2完整工作流程。"""
        workflow = [
            ("requirements_draft", "review_requirements"),
            ("requirements_review", "signoff_requirements"),
            ("requirements_approved", "create_design"),
            ("design_approved", "implement_code"),
            ("development", "fix_bugs")
        ]
        
        for phase, action_type in workflow:
            action, rule = brain_engine.get_action(
                agent_type="agent2",
                phase=phase,
                pending_issues=0,
                signoff={"requirements": {"pm_signoff": True, "dev_signoff": True}}
            )
            
            assert action.value == action_type, f"阶段 {phase} 预期动作 {action_type}，实际 {action.value}"
            
            result = task_executor.execute_action(action.value, {"project_name": "TestProject"})
            assert result.success == True, f"阶段 {phase} 任务执行失败: {result.message}"
    
    def test_state_machine_brain_engine_integration(self, brain_engine, task_executor):
        """测试状态机与大脑引擎集成。"""
        state_machine = StateMachine()
        
        test_cases = [
            (State.PROJECT_INIT, "agent1", "create_requirements"),
            (State.REQUIREMENTS_REVIEW, "agent1", "signoff_requirements"),
            (State.DESIGN_REVIEW, "agent1", "review_design"),
            (State.TESTING, "agent1", "execute_blackbox_test"),
            (State.DEPLOYMENT, "agent1", "execute_deployment"),
            (State.REQUIREMENTS_DRAFT, "agent2", "review_requirements"),
            (State.REQUIREMENTS_REVIEW, "agent2", "signoff_requirements"),
            (State.REQUIREMENTS_APPROVED, "agent2", "create_design"),
            (State.DESIGN_APPROVED, "agent2", "implement_code"),
        ]
        
        for state, agent_type, expected_action in test_cases:
            action, rule = brain_engine.get_action(
                agent_type=agent_type,
                phase=state.value,
                signoff={"requirements": {"pm_signoff": True, "dev_signoff": True}},
                pending_issues=0
            )
            
            assert action.value == expected_action, f"状态 {state.value}, Agent {agent_type} 预期动作 {expected_action}"


class TestRulePriority:
    """规则优先级测试类。"""
    
    @pytest.fixture
    def brain_engine(self):
        """创建大脑引擎实例。"""
        return BrainEngine()
    
    def test_agent1_rules_priority(self, brain_engine):
        """测试Agent 1规则优先级。"""
        rules = brain_engine.list_rules(AgentType.AGENT_1)
        
        priorities = [r["priority"] for r in rules]
        assert priorities == sorted(priorities, reverse=True), "规则未按优先级排序"
    
    def test_agent2_rules_priority(self, brain_engine):
        """测试Agent 2规则优先级。"""
        rules = brain_engine.list_rules(AgentType.AGENT_2)
        
        priorities = [r["priority"] for r in rules]
        assert priorities == sorted(priorities, reverse=True), "规则未按优先级排序"
    
    def test_agent1_has_5_rules(self, brain_engine):
        """测试Agent 1有5个规则。"""
        rules = brain_engine.list_rules(AgentType.AGENT_1)
        assert len(rules) == 5, f"Agent 1应该有5个规则，实际 {len(rules)} 个"
    
    def test_agent2_has_5_rules(self, brain_engine):
        """测试Agent 2有5个规则。"""
        rules = brain_engine.list_rules(AgentType.AGENT_2)
        assert len(rules) == 5, f"Agent 2应该有5个规则，实际 {len(rules)} 个"


class TestTaskExecutorSummary:
    """任务执行器摘要测试类。"""
    
    @pytest.fixture
    def task_executor(self):
        """创建任务执行器实例。"""
        return TaskExecutor()
    
    def test_get_summary(self, task_executor):
        """测试获取摘要。"""
        summary = task_executor.get_summary()
        
        assert "registered_strategies" in summary
        assert "total_tasks" in summary
        assert "pending_tasks" in summary
        assert "completed_tasks" in summary
        assert "failed_tasks" in summary
        assert "success_rate" in summary
    
    def test_task_history(self, task_executor):
        """测试任务历史。"""
        context = {"project_name": "TestProject"}
        
        task_executor.execute_action("create_requirements", context)
        task_executor.execute_action("create_design", context)
        
        summary = task_executor.get_summary()
        assert summary["total_tasks"] == 2
        assert summary["completed_tasks"] == 2
        assert summary["success_rate"] == 100.0


class TestBrainEngineSummary:
    """大脑引擎摘要测试类。"""
    
    @pytest.fixture
    def brain_engine(self):
        """创建大脑引擎实例。"""
        return BrainEngine()
    
    def test_get_summary(self, brain_engine):
        """测试获取摘要。"""
        summary = brain_engine.get_summary()
        
        assert "rules_path" in summary
        assert "rule_sets_count" in summary
        assert "total_rules" in summary
        assert "agent1_rules" in summary
        assert "agent2_rules" in summary
    
    def test_total_rules_count(self, brain_engine):
        """测试总规则数。"""
        summary = brain_engine.get_summary()
        assert summary["total_rules"] == 10
        assert summary["agent1_rules"] == 5
        assert summary["agent2_rules"] == 5
