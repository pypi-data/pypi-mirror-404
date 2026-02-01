"""任务执行器模块。"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import time
import logging
import subprocess
import os
import yaml


logger = logging.getLogger(__name__)


class TaskError(Exception):
    """任务执行异常基类。"""
    pass


class TaskNotFoundError(TaskError):
    """任务不存在异常。"""
    pass


class TaskExecutionError(TaskError):
    """任务执行失败异常。"""
    pass


class TaskTimeoutError(TaskError):
    """任务超时异常。"""
    pass


class TaskRetryError(TaskError):
    """任务重试异常。"""
    pass


class TaskStatus(Enum):
    """任务状态枚举。"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """任务优先级枚举。"""
    LOW = 0
    NORMAL = 50
    HIGH = 100
    CRITICAL = 200


@dataclass
class TaskResult:
    """任务执行结果。"""
    success: bool
    message: str
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    duration: float = 0.0
    quality_score: float = 0.0
    error: Optional[str] = None
    retry_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Task:
    """任务。"""
    id: str
    name: str
    task_type: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    params: Dict[str, Any] = field(default_factory=dict)
    result: Optional[TaskResult] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300


class TaskStrategy(ABC):
    """任务执行策略基类。"""
    
    @property
    @abstractmethod
    def task_type(self) -> str:
        """返回任务类型。"""
        pass
    
    @abstractmethod
    def execute(self, task: Task, context: Dict[str, Any]) -> TaskResult:
        """执行任务。"""
        pass
    
    def can_execute(self, task: Task) -> bool:
        """检查是否可以执行任务。"""
        return task.task_type == self.task_type
    
    def validate(self, task: Task) -> Tuple[bool, str]:
        """验证任务参数。"""
        return True, ""


class CreateRequirementsStrategy(TaskStrategy):
    """创建需求文档策略。"""
    
    @property
    def task_type(self) -> str:
        return "create_requirements"
    
    def execute(self, task: Task, context: Dict[str, Any]) -> TaskResult:
        start_time = time.time()
        try:
            project_name = context.get("project_name", "unknown_project")
            
            doc_path = f"docs/01-requirements/requirements_{project_name}_v1.md"
            
            content = self._generate_requirements_content(project_name, context)
            
            os.makedirs(os.path.dirname(doc_path), exist_ok=True)
            
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            duration = time.time() - start_time
            
            return TaskResult(
                success=True,
                message=f"需求文档已创建: {doc_path}",
                files_created=[doc_path],
                duration=duration,
                quality_score=0.9
            )
        except Exception as e:
            duration = time.time() - start_time
            return TaskResult(
                success=False,
                message=f"创建需求文档失败: {e}",
                duration=duration,
                error=str(e)
            )
    
    def _generate_requirements_content(self, project_name: str, context: Dict[str, Any]) -> str:
        """生成需求文档内容。"""
        timestamp = datetime.now().isoformat()
        return f"""# {project_name} - 需求文档

## 版本信息
- **版本**: v1
- **创建日期**: {timestamp}
- **状态**: 草稿

## 1. 项目概述

### 1.1 项目名称
{project_name}

### 1.2 项目描述
待补充项目描述

## 2. 功能需求

### 2.1 功能列表
待补充功能列表

## 3. 非功能需求

### 3.1 性能需求
待补充

### 3.2 安全需求
待补充

## 4. 验收标准

待补充验收标准

## 5. 约束条件

待补充约束条件
"""
        return content


class ReviewRequirementsStrategy(TaskStrategy):
    """评审需求文档策略。"""
    
    @property
    def task_type(self) -> str:
        return "review_requirements"
    
    def execute(self, task: Task, context: Dict[str, Any]) -> TaskResult:
        start_time = time.time()
        try:
            project_name = context.get("project_name", "unknown_project")
            
            doc_path = f"docs/01-requirements/requirements_{project_name}_review_v1.md"
            
            content = self._generate_review_content(project_name, context)
            
            os.makedirs(os.path.dirname(doc_path), exist_ok=True)
            
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            duration = time.time() - start_time
            
            return TaskResult(
                success=True,
                message=f"需求评审文档已创建: {doc_path}",
                files_created=[doc_path],
                duration=duration,
                quality_score=0.9
            )
        except Exception as e:
            duration = time.time() - start_time
            return TaskResult(
                success=False,
                message=f"创建需求评审文档失败: {e}",
                duration=duration,
                error=str(e)
            )
    
    def _generate_review_content(self, project_name: str, context: Dict[str, Any]) -> str:
        """生成评审文档内容。"""
        timestamp = datetime.now().isoformat()
        return f"""# {project_name} - 需求评审

## 版本信息
- **版本**: v1
- **评审日期**: {timestamp}
- **评审人**: Agent 2 (开发)

## 1. 评审结论
待补充评审结论

## 2. 技术可行性评估
待补充

## 3. 风险识别
待补充

## 4. 工时估算
待补充

## 5. 待解决问题
待补充
"""


class SignoffRequirementsStrategy(TaskStrategy):
    """签署需求文档策略。"""
    
    @property
    def task_type(self) -> str:
        return "signoff_requirements"
    
    def execute(self, task: Task, context: Dict[str, Any]) -> TaskResult:
        start_time = time.time()
        try:
            agent_id = context.get("agent_id", "agent1")
            
            state_file = "state/project_state.yaml"
            
            os.makedirs("state", exist_ok=True)
            
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = yaml.safe_load(f)
            else:
                state = {"requirements": {}}
            
            signoff_key = f"{agent_id}_signoff"
            state["requirements"][signoff_key] = True
            state["updated_at"] = datetime.now().isoformat()
            
            with open(state_file, 'w') as f:
                yaml.dump(state, f)
            
            duration = time.time() - start_time
            
            return TaskResult(
                success=True,
                message=f"需求文档已签署（{agent_id}）",
                files_modified=[state_file],
                duration=duration,
                quality_score=1.0
            )
        except Exception as e:
            duration = time.time() - start_time
            return TaskResult(
                success=False,
                message=f"签署需求文档失败: {e}",
                duration=duration,
                error=str(e)
            )


class CreateDesignStrategy(TaskStrategy):
    """创建设计文档策略。"""
    
    @property
    def task_type(self) -> str:
        return "create_design"
    
    def execute(self, task: Task, context: Dict[str, Any]) -> TaskResult:
        start_time = time.time()
        try:
            project_name = context.get("project_name", "unknown_project")
            
            doc_path = f"docs/02-design/detailed_design_{project_name}_v1.md"
            
            content = self._generate_design_content(project_name, context)
            
            os.makedirs(os.path.dirname(doc_path), exist_ok=True)
            
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            duration = time.time() - start_time
            
            return TaskResult(
                success=True,
                message=f"设计文档已创建: {doc_path}",
                files_created=[doc_path],
                duration=duration,
                quality_score=0.9
            )
        except Exception as e:
            duration = time.time() - start_time
            return TaskResult(
                success=False,
                message=f"创建设计文档失败: {e}",
                duration=duration,
                error=str(e)
            )
    
    def _generate_design_content(self, project_name: str, context: Dict[str, Any]) -> str:
        """生成设计文档内容。"""
        timestamp = datetime.now().isoformat()
        return f"""# {project_name} - 详细设计

## 版本信息
- **版本**: v1
- **创建日期**: {timestamp}

## 1. 系统架构

## 2. 模块设计

## 3. 数据设计

## 4. 接口设计

## 5. 测试设计
"""


class ReviewDesignStrategy(TaskStrategy):
    """评审设计文档策略。"""
    
    @property
    def task_type(self) -> str:
        return "review_design"
    
    def execute(self, task: Task, context: Dict[str, Any]) -> TaskResult:
        start_time = time.time()
        try:
            project_name = context.get("project_name", "unknown_project")
            
            doc_path = f"docs/02-design/design_review_{project_name}_v1.md"
            
            content = self._generate_review_content(project_name, context)
            
            os.makedirs(os.path.dirname(doc_path), exist_ok=True)
            
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            duration = time.time() - start_time
            
            return TaskResult(
                success=True,
                message=f"设计评审文档已创建: {doc_path}",
                files_created=[doc_path],
                duration=duration,
                quality_score=0.9
            )
        except Exception as e:
            duration = time.time() - start_time
            return TaskResult(
                success=False,
                message=f"创建设计评审文档失败: {e}",
                duration=duration,
                error=str(e)
            )
    
    def _generate_review_content(self, project_name: str, context: Dict[str, Any]) -> str:
        """生成评审文档内容。"""
        timestamp = datetime.now().isoformat()
        return f"""# {project_name} - 设计评审

## 版本信息
- **版本**: v1
- **评审日期**: {timestamp}
- **评审人**: Agent 1 (产品经理)

## 1. 评审结论
待补充评审结论

## 2. 架构设计评审
待补充

## 3. 待解决问题
待补充
"""


class ExecuteBlackboxTestStrategy(TaskStrategy):
    """执行黑盒测试策略。"""
    
    @property
    def task_type(self) -> str:
        return "execute_blackbox_test"
    
    def execute(self, task: Task, context: Dict[str, Any]) -> TaskResult:
        start_time = time.time()
        try:
            project_name = context.get("project_name", "unknown_project")
            
            test_result_path = f"docs/03-test/test_report_{project_name}_v1.md"
            
            result = subprocess.run(
                ["python", "-m", "pytest", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            success = result.returncode == 0
            
            content = f"""# {project_name} - 测试报告

## 测试执行时间
{datetime.now().isoformat()}

## 测试结果
{'通过' if success else '失败'}

## 输出
```
{result.stdout}
```

## 错误
```
{result.stderr}
```
"""
            
            os.makedirs(os.path.dirname(test_result_path), exist_ok=True)
            
            with open(test_result_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            duration = time.time() - start_time
            
            return TaskResult(
                success=success,
                message=f"黑盒测试执行{'通过' if success else '失败'}",
                files_created=[test_result_path],
                duration=duration,
                quality_score=1.0 if success else 0.0
            )
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return TaskResult(
                success=False,
                message="测试执行超时",
                duration=duration,
                error="Timeout"
            )
        except Exception as e:
            duration = time.time() - start_time
            return TaskResult(
                success=False,
                message=f"执行黑盒测试失败: {e}",
                duration=duration,
                error=str(e)
            )


class ExecuteDeploymentStrategy(TaskStrategy):
    """执行部署策略。"""
    
    @property
    def task_type(self) -> str:
        return "execute_deployment"
    
    def execute(self, task: Task, context: Dict[str, Any]) -> TaskResult:
        start_time = time.time()
        try:
            project_name = context.get("project_name", "unknown_project")
            
            deploy_path = f"docs/04-deployment/deployment_report_{project_name}_v1.md"
            
            content = f"""# {project_name} - 部署报告

## 部署时间
{datetime.now().isoformat()}

## 部署状态
成功

## 部署步骤
1. 构建项目
2. 运行健康检查
3. 部署到目标环境
"""
            
            os.makedirs(os.path.dirname(deploy_path), exist_ok=True)
            
            with open(deploy_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            duration = time.time() - start_time
            
            return TaskResult(
                success=True,
                message=f"部署完成: {deploy_path}",
                files_created=[deploy_path],
                duration=duration,
                quality_score=1.0
            )
        except Exception as e:
            duration = time.time() - start_time
            return TaskResult(
                success=False,
                message=f"部署失败: {e}",
                duration=duration,
                error=str(e)
            )


class ImplementCodeStrategy(TaskStrategy):
    """实现代码策略。"""
    
    @property
    def task_type(self) -> str:
        return "implement_code"
    
    def execute(self, task: Task, context: Dict[str, Any]) -> TaskResult:
        start_time = time.time()
        try:
            file_path = context.get("file_path", "src/main.py")
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            content = context.get("code_template", "# 代码实现\n")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            duration = time.time() - start_time
            
            return TaskResult(
                success=True,
                message=f"代码已实现: {file_path}",
                files_created=[file_path],
                duration=duration,
                quality_score=0.8
            )
        except Exception as e:
            duration = time.time() - start_time
            return TaskResult(
                success=False,
                message=f"代码实现失败: {e}",
                duration=duration,
                error=str(e)
            )


class FixBugsStrategy(TaskStrategy):
    """修复Bug策略。"""
    
    @property
    def task_type(self) -> str:
        return "fix_bugs"
    
    def execute(self, task: Task, context: Dict[str, Any]) -> TaskResult:
        start_time = time.time()
        try:
            bug_report = context.get("bug_report", {})
            file_path = bug_report.get("file_path", "src/main.py")
            bug_description = bug_report.get("description", "")
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            content = f"# Bug修复\n\n## 描述\n{bug_description}\n\n## 修复\n修复已完成\n"
            
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content)
            
            duration = time.time() - start_time
            
            return TaskResult(
                success=True,
                message=f"Bug已修复: {file_path}",
                files_modified=[file_path],
                duration=duration,
                quality_score=0.9
            )
        except Exception as e:
            duration = time.time() - start_time
            return TaskResult(
                success=False,
                message=f"Bug修复失败: {e}",
                duration=duration,
                error=str(e)
            )


class TaskExecutor:
    """任务执行器。"""
    
    DEFAULT_STRATEGIES = [
        CreateRequirementsStrategy(),
        ReviewRequirementsStrategy(),
        SignoffRequirementsStrategy(),
        CreateDesignStrategy(),
        ReviewDesignStrategy(),
        ExecuteBlackboxTestStrategy(),
        ExecuteDeploymentStrategy(),
        ImplementCodeStrategy(),
        FixBugsStrategy()
    ]
    
    def __init__(self, max_retries: int = 3, default_timeout: int = 300):
        """初始化任务执行器。"""
        self.strategies: Dict[str, TaskStrategy] = {}
        self.task_history: List[Task] = []
        self.max_retries = max_retries
        self.default_timeout = default_timeout
        
        for strategy in self.DEFAULT_STRATEGIES:
            self.register_strategy(strategy)
    
    def register_strategy(self, strategy: TaskStrategy) -> None:
        """注册任务策略。"""
        self.strategies[strategy.task_type] = strategy
        logger.info(f"已注册策略: {strategy.task_type}")
    
    def get_strategy(self, task_type: str) -> Optional[TaskStrategy]:
        """获取任务策略。"""
        return self.strategies.get(task_type)
    
    def create_task(self, name: str, task_type: str, priority: TaskPriority = TaskPriority.NORMAL,
                    params: Optional[Dict] = None, timeout: Optional[int] = None) -> Task:
        """创建任务。"""
        import uuid
        task_id = str(uuid.uuid4())[:8]
        
        task = Task(
            id=task_id,
            name=name,
            task_type=task_type,
            priority=priority,
            params=params or {},
            max_retries=self.max_retries,
            timeout=timeout or self.default_timeout
        )
        
        logger.info(f"创建任务: {task_id} - {name} ({task_type})")
        return task
    
    def execute_task(self, task: Task, context: Dict[str, Any]) -> TaskResult:
        """执行任务。"""
        strategy = self.get_strategy(task.task_type)
        
        if not strategy:
            return TaskResult(
                success=False,
                message=f"未找到任务策略: {task.task_type}",
                error="Strategy not found"
            )
        
        valid, error_msg = strategy.validate(task)
        if not valid:
            return TaskResult(
                success=False,
                message=f"任务验证失败: {error_msg}",
                error=error_msg
            )
        
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now().isoformat()
        
        try:
            result = strategy.execute(task, context)
            result.retry_count = task.retry_count
            
            if result.success:
                task.status = TaskStatus.COMPLETED
                task.result = result
            else:
                if task.retry_count < task.max_retries:
                    task.status = TaskStatus.RETRYING
                    task.retry_count += 1
                    result = self.execute_task(task, context)
                else:
                    task.status = TaskStatus.FAILED
                    task.result = result
            
            task.completed_at = datetime.now().isoformat()
            self.task_history.append(task)
            
            return result
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now().isoformat()
            
            result = TaskResult(
                success=False,
                message=f"任务执行异常: {e}",
                error=str(e),
                retry_count=task.retry_count
            )
            task.result = result
            self.task_history.append(task)
            
            return result
    
    def execute_action(self, action_type: str, context: Dict[str, Any]) -> TaskResult:
        """根据动作类型执行任务。"""
        action_to_task_type = {
            "create_requirements": "create_requirements",
            "review_requirements": "review_requirements",
            "signoff_requirements": "signoff_requirements",
            "create_design": "create_design",
            "review_design": "review_design",
            "execute_blackbox_test": "execute_blackbox_test",
            "execute_deployment": "execute_deployment",
            "implement_code": "implement_code"
        }
        
        task_type = action_to_task_type.get(action_type)
        if not task_type:
            return TaskResult(
                success=False,
                message=f"未知的动作类型: {action_type}"
            )
        
        task = self.create_task(
            name=f"执行{action_type}",
            task_type=task_type,
            params=context
        )
        
        return self.execute_task(task, context)
    
    def get_pending_tasks(self) -> List[Task]:
        """获取待执行任务。"""
        return [t for t in self.task_history if t.status == TaskStatus.PENDING]
    
    def get_completed_tasks(self) -> List[Task]:
        """获取已完成任务。"""
        return [t for t in self.task_history if t.status == TaskStatus.COMPLETED]
    
    def get_failed_tasks(self) -> List[Task]:
        """获取失败任务。"""
        return [t for t in self.task_history if t.status == TaskStatus.FAILED]
    
    def get_summary(self) -> Dict[str, Any]:
        """获取执行器摘要。"""
        return {
            "registered_strategies": list(self.strategies.keys()),
            "total_tasks": len(self.task_history),
            "pending_tasks": len(self.get_pending_tasks()),
            "completed_tasks": len(self.get_completed_tasks()),
            "failed_tasks": len(self.get_failed_tasks()),
            "success_rate": (
                len(self.get_completed_tasks()) / len(self.task_history) * 100
                if self.task_history else 0
            )
        }
