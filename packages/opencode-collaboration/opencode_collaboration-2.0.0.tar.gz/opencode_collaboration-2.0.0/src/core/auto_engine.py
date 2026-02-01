"""自动协作引擎模块。"""
import signal
from datetime import datetime
from typing import Dict, List, Optional, Any

from .state_manager import StateManager
from .git import GitHelper
from .workflow import WorkflowEngine
from .signoff import SignoffEngine
from .phase_advance import PhaseAdvanceEngine
from ..utils.lock import LockManager, LockExistsError
from ..utils.date import get_current_time


class AutoCollaborationError(Exception):
    """自动协作异常基类。"""
    pass


class LockConflictError(AutoCollaborationError):
    """锁文件冲突异常。"""
    pass


class MaxIterationsError(AutoCollaborationError):
    """达到最大迭代次数异常。"""
    pass


class AutoCollaborationEngine:
    """自动协作引擎。"""
    
    MAX_ITERATIONS = 10
    
    PHASE_TASKS = {
        "project_init": {
            "agent1": [],
            "agent2": []
        },
        "requirements_draft": {
            "agent1": [],
            "agent2": []
        },
        "requirements_review": {
            "agent1": ["review_requirements", "signoff_requirements"],
            "agent2": ["review_requirements", "signoff_requirements"]
        },
        "requirements_approved": {
            "agent1": [],
            "agent2": []
        },
        "design_draft": {
            "agent1": [],
            "agent2": []
        },
        "design_review": {
            "agent1": ["review_design", "signoff_design"],
            "agent2": ["review_design", "signoff_design"]
        },
        "design_approved": {
            "agent1": [],
            "agent2": []
        },
        "development": {
            "agent1": [],
            "agent2": ["development", "testing"]
        },
        "testing": {
            "agent1": ["signoff_test"],
            "agent2": []
        },
        "deployment": {
            "agent1": [],
            "agent2": []
        },
        "completed": {
            "agent1": [],
            "agent2": []
        }
    }
    
    def __init__(self, project_path: str):
        """初始化自动协作引擎。"""
        self.project_path = project_path
        self.state_manager = StateManager(project_path)
        self.git_helper = GitHelper(project_path)
        self.workflow_engine = WorkflowEngine(self.state_manager)
        self.signoff_engine = SignoffEngine(self.state_manager, self.workflow_engine)
        self.phase_advance_engine = PhaseAdvanceEngine(project_path)
        self.lock_manager = LockManager(project_path)
        self.current_iteration = 0
        self.is_running = False
        self.execution_history = []
    
    def run(self, max_iterations: Optional[int] = None) -> Dict[str, Any]:
        """执行自动协作流程。"""
        if max_iterations is None:
            max_iterations = self.MAX_ITERATIONS

        self.is_running = True
        self.current_iteration = 0
        self.execution_history = []

        try:
            self.lock_manager.check_and_cleanup()
            self.lock_manager.acquire("auto command execution")

            if self.git_helper.has_local_changes():
                return {
                    "success": False,
                    "error": "存在未提交的本地修改，请先执行 git add 和 commit"
                }

            for i in range(max_iterations):
                self.current_iteration = i + 1

                if not self.is_running:
                    break

                # 1. 检查并自动推进阶段
                phase_result = self.phase_advance_engine.check_and_advance()
                if phase_result["advanced"]:
                    self.execution_history.append({
                        "action": "phase_advance",
                        "from": phase_result["from_phase"],
                        "to": phase_result["to_phase"],
                        "reason": phase_result["reason"]
                    })

                # 1.5 检测测试阶段的 bug 并激活 Agent 2
                bug_result = self.phase_advance_engine.detect_test_activate_agent_bugs_and2()
                if bug_result.get("triggered"):
                    self.execution_history.append({
                        "action": "bug_detected_agent2_activated",
                        "bugs_count": bug_result.get("bugs_found"),
                        "bugs": bug_result.get("bugs", [])
                    })

                # 2. 检测状态
                state = self.detect_state()
                if state.get("completed"):
                    break

                # 3. 执行任务
                agent = self.get_active_agent()
                result = self.execute_task(state, agent)
                self.execution_history.append(result)

                # 4. 同步 Git
                if result.get("git_synced"):
                    self.sync_git()

                # 5. 检查完成
                if self.check_completion():
                    break

            return self._generate_summary()
            
        except LockExistsError as e:
            return {
                "success": False,
                "error": str(e)
            }
        except KeyboardInterrupt:
            return {
                "success": False,
                "error": "用户中断执行，状态已保存",
                "iterations": self.current_iteration
            }
        finally:
            self.is_running = False
            try:
                self.lock_manager.release()
            except Exception:
                pass
    
    def detect_state(self) -> Dict[str, Any]:
        """检测当前状态。"""
        state = self.state_manager.load_state()
        
        phase = state.get("phase", "unknown")
        req_status = self.state_manager.get_signoff_status("requirements")
        design_status = self.state_manager.get_signoff_status("design")
        
        blockers = []
        if phase == "requirements_review":
            if not req_status["pm_signoff"]:
                blockers.append("等待产品经理签署需求")
            if not req_status["dev_signoff"]:
                blockers.append("等待开发签署需求")
        elif phase == "design_review":
            if not design_status["pm_signoff"]:
                blockers.append("等待产品经理签署设计")
            if not design_status["dev_signoff"]:
                blockers.append("等待开发签署设计")
        
        return {
            "phase": phase,
            "requirements_status": req_status,
            "design_status": design_status,
            "blockers": blockers,
            "completed": phase == "completed"
        }
    
    def get_active_agent(self) -> str:
        """获取当前活跃的Agent。"""
        return self.state_manager.get_active_agent()
    
    def execute_task(self, state: Dict[str, Any], agent: str) -> Dict[str, Any]:
        """执行当前任务。"""
        phase = state.get("phase", "")
        tasks = self.PHASE_TASKS.get(phase, {}).get(agent, [])
        
        result = {
            "phase": phase,
            "agent": agent,
            "tasks": [],
            "git_synced": False
        }
        
        for task in tasks:
            task_result = self._execute_single_task(task, state)
            result["tasks"].append(task_result)
            if task_result.get("state_changed"):
                result["git_synced"] = True
        
        return result
    
    def _execute_single_task(self, task: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个任务。"""
        result = {"task": task, "state_changed": False}
        
        if task == "review_requirements":
            self.state_manager.increment_review_cycle()
            result["state_changed"] = True
        
        elif task == "signoff_requirements":
            agent = self.state_manager.get_active_agent()
            can_sign, message = self.signoff_engine.can_sign("requirements", agent)
            if can_sign:
                self.signoff_engine.sign("requirements", agent, "自动签署")
                result["state_changed"] = True
            result["message"] = message
        
        elif task == "review_design":
            self.state_manager.increment_review_cycle()
            result["state_changed"] = True
        
        elif task == "signoff_design":
            agent = self.state_manager.get_active_agent()
            can_sign, message = self.signoff_engine.can_sign("design", agent)
            if can_sign:
                self.signoff_engine.sign("design", agent, "自动签署")
                result["state_changed"] = True
            result["message"] = message
        
        elif task == "signoff_test":
            agent = self.state_manager.get_active_agent()
            can_sign, message = self.signoff_engine.can_sign("test", agent)
            if can_sign:
                self.signoff_engine.sign("test", agent, "自动签署")
                result["state_changed"] = True
            result["message"] = message
        
        return result
    
    def sync_git(self) -> bool:
        """同步Git变更。"""
        try:
            if self.git_helper.has_local_changes():
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = f"feat(auto): 自动协作执行 - {timestamp}"
                self.git_helper.push(message)
                return True
            return False
        except Exception:
            return False
    
    def check_completion(self) -> bool:
        """检查是否完成。"""
        phase = self.state_manager.get_current_phase()
        return phase == "completed"
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成执行摘要。"""
        phase = self.state_manager.get_current_phase()
        
        return {
            "success": True,
            "completed": phase == "completed",
            "current_phase": phase,
            "total_iterations": self.current_iteration,
            "execution_history": self.execution_history,
            "timestamp": get_current_time()
        }
    
    def stop(self) -> None:
        """停止自动协作。"""
        self.is_running = False


class TodoCommandExecutor:
    """待办事项执行器。"""
    
    TODO_MAP = {
        "project_init": ["初始化项目"],
        "requirements_draft": ["创建需求文档"],
        "requirements_review": ["评审需求", "签署需求"],
        "requirements_approved": ["进入设计阶段"],
        "design_draft": ["创建设计文档"],
        "design_review": ["评审设计", "签署设计"],
        "design_approved": ["进入开发阶段"],
        "development": ["开发实现", "编写测试"],
        "testing": ["测试验证", "签署测试"],
        "deployment": ["部署发布"],
        "completed": []
    }
    
    def __init__(self, project_path: str):
        """初始化待办事项执行器。"""
        self.project_path = project_path
        self.state_manager = StateManager(project_path)
        self.workflow_engine = WorkflowEngine(self.state_manager)
    
    def get_todo_list(self) -> List[Dict[str, Any]]:
        """获取待办事项列表。"""
        state = self.state_manager.load_state()
        phase = state.get("phase", "")
        
        todos = self.TODO_MAP.get(phase, [])
        
        result = []
        for todo in todos:
            item = {
                "task": todo,
                "status": "pending",
                "phase": phase
            }
            result.append(item)
        
        return result
    
    def get_progress(self) -> Dict[str, Any]:
        """获取进度信息。"""
        state = self.state_manager.load_state()
        phase = state.get("phase", "")
        
        phase_order = [
            "project_init", "requirements_draft", "requirements_review",
            "requirements_approved", "design_draft", "design_review",
            "design_approved", "development", "testing", "deployment", "completed"
        ]
        
        try:
            current_idx = phase_order.index(phase)
            total = len(phase_order) - 1
            percentage = (current_idx / total) * 100
        except ValueError:
            percentage = 0
        
        return {
            "current_phase": phase,
            "progress_percentage": round(percentage, 1),
            "remaining_phases": phase_order[phase_order.index(phase)+1:] if phase in phase_order else []
        }
    
    def get_blockers(self) -> List[Dict[str, str]]:
        """获取阻塞项。"""
        state = self.detect_state()
        blockers = state.get("blockers", [])
        
        return [{"blocker": b} for b in blockers]
    
    def detect_state(self) -> Dict[str, Any]:
        """检测当前状态。"""
        state = self.state_manager.load_state()
        phase = state.get("phase", "")
        req_status = self.state_manager.get_signoff_status("requirements")
        design_status = self.state_manager.get_signoff_status("design")
        
        blockers = []
        if phase == "requirements_review":
            if not req_status["pm_signoff"]:
                blockers.append("等待产品经理签署需求")
            if not req_status["dev_signoff"]:
                blockers.append("等待开发签署需求")
        elif phase == "design_review":
            if not design_status["pm_signoff"]:
                blockers.append("等待产品经理签署设计")
            if not design_status["dev_signoff"]:
                blockers.append("等待开发签署设计")
        
        return {
            "phase": phase,
            "blockers": blockers
        }


class WorkCommandExecutor:
    """工作流引导执行器。"""
    
    def __init__(self, project_path: str):
        """初始化工作流引导执行器。"""
        self.project_path = project_path
        self.state_manager = StateManager(project_path)
        self.workflow_engine = WorkflowEngine(self.state_manager)
        self.todo_executor = TodoCommandExecutor(project_path)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """获取状态摘要。"""
        state = self.state_manager.load_state()
        phase = state.get("phase", "")
        agent = self.state_manager.get_active_agent()
        req_status = self.state_manager.get_signoff_status("requirements")
        design_status = self.state_manager.get_signoff_status("design")
        todo_list = self.todo_executor.get_todo_list()
        progress = self.todo_executor.get_progress()
        
        return {
            "current_phase": phase,
            "current_agent": agent,
            "requirements_signoff": req_status,
            "design_signoff": design_status,
            "todo_count": len(todo_list),
            "progress": progress
        }
    
    def get_suggestions(self) -> List[Dict[str, Any]]:
        """获取操作建议。"""
        state = self.state_manager.load_state()
        phase = state.get("phase", "")
        agent = self.state_manager.get_active_agent()
        blockers = self.todo_executor.get_blockers()
        
        suggestions = []
        
        if blockers:
            for blocker in blockers:
                suggestions.append({
                    "action": "等待",
                    "description": blocker["blocker"],
                    "priority": "high"
                })
        
        todo_list = self.todo_executor.get_todo_list()
        for todo in todo_list:
            if todo["status"] == "pending":
                suggestions.append({
                    "action": todo["task"],
                    "description": f"执行: {todo['task']}",
                    "priority": "normal"
                })
        
        return suggestions
    
    def execute_suggestion(self, action: str) -> Dict[str, Any]:
        """执行建议操作。"""
        return {"success": False, "message": "一键执行功能待实现"}
