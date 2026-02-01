"""大脑引擎模块。"""
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import yaml
import os


logger = logging.getLogger(__name__)


class BrainEngineError(Exception):
    """大脑引擎异常基类。"""
    pass


class RuleLoadError(BrainEngineError):
    """规则加载异常。"""
    pass


class RuleExecutionError(BrainEngineError):
    """规则执行异常。"""
    pass


class AgentType(Enum):
    """Agent类型枚举。"""
    AGENT_1 = "agent1"
    AGENT_2 = "agent2"


class ActionType(Enum):
    """动作类型枚举。"""
    CREATE_REQUIREMENTS = "create_requirements"
    REVIEW_REQUIREMENTS = "review_requirements"
    SIGNOFF_REQUIREMENTS = "signoff_requirements"
    CREATE_DESIGN = "create_design"
    REVIEW_DESIGN = "review_design"
    SIGNOFF_DESIGN = "signoff_design"
    EXECUTE_BLACKBOX_TEST = "execute_blackbox_test"
    EXECUTE_DEPLOYMENT = "execute_deployment"
    IMPLEMENT_CODE = "implement_code"
    FIX_BUGS = "fix_bugs"
    WAIT = "wait"
    SKIP = "skip"


@dataclass
class Condition:
    """规则条件。"""
    type: str
    params: Dict[str, Any] = field(default_factory=dict)
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """评估条件。"""
        if self.type == "phase_equals":
            return context.get("phase") == self.params.get("value")
        elif self.type == "phase_in":
            return context.get("phase") in self.params.get("values", [])
        elif self.type == "signoff_complete":
            stage = self.params.get("stage", "")
            signoff = context.get("signoff", {}).get(stage, {})
            return signoff.get("pm_signoff", False) and signoff.get("dev_signoff", False)
        elif self.type == "no_pending_issues":
            return context.get("pending_issues", 0) == 0
        elif self.type == "file_exists":
            return context.get("file_exists", {}).get(self.params.get("path"), False)
        elif self.type == "custom":
            func = self.params.get("function")
            if callable(func):
                return func(context)
            return False
        return True


@dataclass
class Rule:
    """行为规则。"""
    id: str
    name: str
    agent_type: AgentType
    conditions: List[Condition] = field(default_factory=list)
    action: ActionType = ActionType.WAIT
    priority: int = 0
    enabled: bool = True
    description: str = ""
    
    def matches(self, context: Dict[str, Any]) -> bool:
        """检查规则是否匹配当前上下文。"""
        if not self.enabled:
            return False
        
        if context.get("agent_type") != self.agent_type.value:
            return False
        
        for condition in self.conditions:
            if not condition.evaluate(context):
                return False
        
        return True


@dataclass
class RuleSet:
    """规则集。"""
    name: str
    version: str = "1.0.0"
    rules: List[Rule] = field(default_factory=list)
    
    def get_rules_for_agent(self, agent_type: AgentType) -> List[Rule]:
        """获取指定Agent的所有规则。"""
        return [r for r in self.rules if r.agent_type == agent_type]
    
    def get_matching_rules(self, context: Dict[str, Any]) -> List[Rule]:
        """获取匹配的规则列表。"""
        agent_type = AgentType(context.get("agent_type", "agent1"))
        rules = self.get_rules_for_agent(agent_type)
        matching = [r for r in rules if r.matches(context)]
        return sorted(matching, key=lambda r: -r.priority)


class BrainEngine:
    """大脑引擎。"""
    
    DEFAULT_RULES = {
        "agent1": [
            Rule(
                id="agent1-create-requirements",
                name="创建需求文档",
                agent_type=AgentType.AGENT_1,
                conditions=[Condition("phase_equals", {"value": "project_init"})],
                action=ActionType.CREATE_REQUIREMENTS,
                priority=100,
                description="当阶段为project_init时，创建需求文档"
            ),
            Rule(
                id="agent1-signoff-requirements",
                name="签署需求文档",
                agent_type=AgentType.AGENT_1,
                conditions=[
                    Condition("phase_equals", {"value": "requirements_review"}),
                    Condition("signoff_complete", {"stage": "requirements"})
                ],
                action=ActionType.SIGNOFF_REQUIREMENTS,
                priority=90,
                description="当阶段为requirements_review且双方签署后，签署需求"
            ),
            Rule(
                id="agent1-review-design",
                name="评审设计文档",
                agent_type=AgentType.AGENT_1,
                conditions=[Condition("phase_equals", {"value": "design_review"})],
                action=ActionType.REVIEW_DESIGN,
                priority=80,
                description="当阶段为design_review时，评审设计文档"
            ),
            Rule(
                id="agent1-execute-blackbox-test",
                name="执行黑盒测试",
                agent_type=AgentType.AGENT_1,
                conditions=[Condition("phase_equals", {"value": "testing"})],
                action=ActionType.EXECUTE_BLACKBOX_TEST,
                priority=70,
                description="当阶段为testing时，执行黑盒测试"
            ),
            Rule(
                id="agent1-deploy",
                name="执行部署",
                agent_type=AgentType.AGENT_1,
                conditions=[Condition("phase_equals", {"value": "deployment"})],
                action=ActionType.EXECUTE_DEPLOYMENT,
                priority=60,
                description="当阶段为deployment时，执行部署"
            )
        ],
        "agent2": [
            Rule(
                id="agent2-review-requirements",
                name="评审需求文档",
                agent_type=AgentType.AGENT_2,
                conditions=[Condition("phase_equals", {"value": "requirements_draft"})],
                action=ActionType.REVIEW_REQUIREMENTS,
                priority=100,
                description="当阶段为requirements_draft时，评审需求文档"
            ),
            Rule(
                id="agent2-signoff-requirements",
                name="签署需求文档",
                agent_type=AgentType.AGENT_2,
                conditions=[
                    Condition("phase_equals", {"value": "requirements_review"}),
                    Condition("signoff_complete", {"stage": "requirements"})
                ],
                action=ActionType.SIGNOFF_REQUIREMENTS,
                priority=95,
                description="当阶段为requirements_review且双方签署后，签署需求"
            ),
            Rule(
                id="agent2-create-design",
                name="创建设计文档",
                agent_type=AgentType.AGENT_2,
                conditions=[Condition("phase_equals", {"value": "requirements_approved"})],
                action=ActionType.CREATE_DESIGN,
                priority=90,
                description="当阶段为requirements_approved时，创建设计文档"
            ),
            Rule(
                id="agent2-implement-code",
                name="实现代码",
                agent_type=AgentType.AGENT_2,
                conditions=[Condition("phase_equals", {"value": "design_approved"})],
                action=ActionType.IMPLEMENT_CODE,
                priority=80,
                description="当阶段为design_approved时，实现代码"
            ),
            Rule(
                id="agent2-fix-bugs",
                name="修复Bug",
                agent_type=AgentType.AGENT_2,
                conditions=[Condition("phase_equals", {"value": "development"}), Condition("no_pending_issues")],
                action=ActionType.FIX_BUGS,
                priority=70,
                description="当阶段为development且有待修复的Bug时，修复Bug"
            )
        ]
    }
    
    def __init__(self, rules_path: Optional[str] = None):
        """初始化大脑引擎。"""
        self.rules_path = rules_path
        self.rule_sets: Dict[str, RuleSet] = {}
        self.current_context: Dict[str, Any] = {}
        self._load_default_rules()
        
        if rules_path and os.path.exists(rules_path):
            self.load_rules(rules_path)
    
    def _load_default_rules(self) -> None:
        """加载默认规则。"""
        for agent_key, rules in self.DEFAULT_RULES.items():
            agent_type = AgentType(agent_key)
            rule_set = RuleSet(
                name=f"default_{agent_key}",
                version="1.0.0",
                rules=rules
            )
            self.rule_sets[rule_set.name] = rule_set
    
    def load_rules(self, path: str) -> RuleSet:
        """从文件加载规则。"""
        if not os.path.exists(path):
            logger.warning(f"规则文件不存在: {path}")
            return self._get_default_rule_set()
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                raise RuleLoadError("规则文件为空")
            
            rules = []
            for rule_data in data.get("rules", []):
                conditions = []
                for cond_data in rule_data.get("conditions", []):
                    conditions.append(Condition(
                        type=cond_data.get("type", ""),
                        params=cond_data.get("params", {})
                    ))
                
                rule = Rule(
                    id=rule_data.get("id", ""),
                    name=rule_data.get("name", ""),
                    agent_type=AgentType(rule_data.get("agent_type", "agent1")),
                    conditions=conditions,
                    action=ActionType(rule_data.get("action", "wait")),
                    priority=rule_data.get("priority", 0),
                    enabled=rule_data.get("enabled", True),
                    description=rule_data.get("description", "")
                )
                rules.append(rule)
            
            rule_set = RuleSet(
                name=data.get("name", "custom_rules"),
                version=data.get("version", "1.0.0"),
                rules=rules
            )
            
            self.rule_sets[rule_set.name] = rule_set
            logger.info(f"规则加载成功: {rule_set.name} ({len(rules)} 条规则)")
            
            return rule_set
        except Exception as e:
            raise RuleLoadError(f"规则加载失败: {e}")
    
    def _get_default_rule_set(self) -> RuleSet:
        """获取默认规则集。"""
        return self.rule_sets.get("default_agent1", RuleSet(name="default"))
    
    def reload_rules(self) -> None:
        """重新加载规则。"""
        if self.rules_path and os.path.exists(self.rules_path):
            self.load_rules(self.rules_path)
    
    def update_context(self, **kwargs) -> None:
        """更新上下文。"""
        self.current_context.update(kwargs)
    
    def get_action(self, agent_type: str, phase: str, signoff: Optional[Dict] = None,
                   pending_issues: int = 0, file_exists: Optional[Dict] = None) -> Tuple[Optional[ActionType], Optional[Rule]]:
        """获取当前应执行的动作。"""
        context = {
            "agent_type": agent_type,
            "phase": phase,
            "signoff": signoff or {},
            "pending_issues": pending_issues,
            "file_exists": file_exists or {}
        }
        self.current_context = context
        
        all_rules = []
        for rule_set in self.rule_sets.values():
            all_rules.extend(rule_set.get_matching_rules(context))
        
        if all_rules:
            top_rule = all_rules[0]
            return top_rule.action, top_rule
        
        return ActionType.WAIT, None
    
    def get_available_actions(self, agent_type: str, phase: str) -> List[ActionType]:
        """获取当前阶段可用的动作列表。"""
        action, rule = self.get_action(agent_type, phase)
        if action == ActionType.WAIT:
            return []
        return [action]
    
    def get_state_transition(self, current_phase: str, event: str) -> Optional[str]:
        """根据事件获取状态转换目标。"""
        transition_map = {
            ("project_init", "phase_change"): "requirements_draft",
            ("requirements_draft", "phase_change"): "requirements_review",
            ("requirements_review", "signoff"): "requirements_approved",
            ("requirements_review", "review_complete"): "requirements_draft",
            ("requirements_approved", "phase_change"): "design_draft",
            ("design_draft", "phase_change"): "design_review",
            ("design_review", "signoff"): "design_approved",
            ("design_review", "review_complete"): "design_draft",
            ("design_approved", "phase_change"): "development",
            ("development", "code_committed"): "testing",
            ("testing", "test_complete"): "deployment",
            ("testing", "error"): "development",
            ("deployment", "deploy_complete"): "completed"
        }
        
        return transition_map.get((current_phase, event))
    
    def get_summary(self) -> Dict[str, Any]:
        """获取大脑引擎摘要。"""
        return {
            "rules_path": self.rules_path,
            "rule_sets_count": len(self.rule_sets),
            "total_rules": sum(len(rs.rules) for rs in self.rule_sets.values()),
            "current_context": self.current_context,
            "agent1_rules": len(self.rule_sets.get("default_agent1", RuleSet(name="")).rules),
            "agent2_rules": len(self.rule_sets.get("default_agent2", RuleSet(name="")).rules)
        }
    
    def list_rules(self, agent_type: Optional[AgentType] = None) -> List[Dict[str, Any]]:
        """列出所有规则。"""
        result = []
        for rule_set in self.rule_sets.values():
            for rule in rule_set.rules:
                if agent_type is None or rule.agent_type == agent_type:
                    result.append({
                        "id": rule.id,
                        "name": rule.name,
                        "agent_type": rule.agent_type.value,
                        "action": rule.action.value,
                        "priority": rule.priority,
                        "enabled": rule.enabled,
                        "description": rule.description,
                        "conditions": [c.type for c in rule.conditions]
                    })
        return result
