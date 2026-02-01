"""工作流引擎模块。"""
from typing import Dict, List, Optional


class WorkflowError(Exception):
    """工作流异常基类。"""
    pass


class IllegalPhaseTransitionError(WorkflowError):
    """非法阶段转换异常。"""
    pass


class WorkflowEngine:
    """工作流引擎。"""
    
    TRANSITIONS = {
        "project_init": ["requirements_draft"],
        "requirements_draft": ["requirements_review"],
        "requirements_review": ["requirements_draft", "requirements_approved"],
        "requirements_approved": ["design_draft"],
        "design_draft": ["design_review"],
        "design_review": ["design_draft", "design_approved"],
        "design_approved": ["development"],
        "development": ["testing"],
        "testing": ["deployment", "development"],
        "deployment": ["completed"],
        "completed": []
    }
    
    PHASE_ORDER = [
        "project_init",
        "requirements_draft",
        "requirements_review",
        "requirements_approved",
        "design_draft",
        "design_review",
        "design_approved",
        "development",
        "testing",
        "deployment",
        "completed"
    ]
    
    def __init__(self, state_manager):
        """初始化工作流引擎。"""
        self.state_manager = state_manager
    
    def can_transition(self, from_phase: str, to_phase: str) -> bool:
        """检查是否可以从from_phase转换到to_phase。"""
        valid_next = self.TRANSITIONS.get(from_phase, [])
        return to_phase in valid_next
    
    def get_valid_next_phases(self, phase: str) -> List[str]:
        """获取当前阶段可以转换到的阶段列表。"""
        return self.TRANSITIONS.get(phase, [])
    
    def get_next_phase(self, phase: str) -> Optional[str]:
        """获取当前阶段的下一个阶段。"""
        valid_next = self.get_valid_next_phases(phase)
        if valid_next and len(valid_next) == 1:
            return valid_next[0]
        return None
    
    def transition_to(self, to_phase: str) -> Dict[str, str]:
        """执行阶段转换。"""
        current_phase = self.state_manager.get_current_phase()
        
        if not self.can_transition(current_phase, to_phase):
            valid_next = self.get_valid_next_phases(current_phase)
            raise IllegalPhaseTransitionError(
                f"无法从 {current_phase} 转换到 {to_phase}，"
                f"可选阶段: {valid_next}"
            )
        
        self.state_manager.update_phase(to_phase)
        
        return {
            "from": current_phase,
            "to": to_phase
        }
    
    def start_review(self, stage: str) -> None:
        """发起评审流程。"""
        review_phases = {
            "requirements": "requirements_review",
            "design": "design_review"
        }
        
        if stage not in review_phases:
            raise WorkflowError(f"未知的评审阶段: {stage}")
        
        self.transition_to(review_phases[stage])
        self.state_manager.increment_review_cycle()
    
    def approve_stage(self, stage: str) -> bool:
        """批准阶段。"""
        approval_phases = {
            "requirements": "requirements_approved",
            "design": "design_approved"
        }
        
        if stage not in approval_phases:
            raise WorkflowError(f"未知的阶段: {stage}")
        
        if self.state_manager.can_proceed_to_next_phase():
            next_phase = approval_phases[stage]
            self.transition_to(next_phase)
            return True
        
        return False
    
    def handle_rejection(self, stage: str, reason: str) -> None:
        """处理拒签。"""
        rejection_map = {
            "requirements_review": "requirements_draft",
            "design_review": "design_draft"
        }
        
        if stage not in rejection_map:
            raise WorkflowError(f"不支持拒签的阶段: {stage}")
        
        target_phase = rejection_map[stage]
        self.transition_to(target_phase)
    
    def get_phase_progress(self, phase: str) -> Dict[str, any]:
        """获取阶段进度信息。"""
        try:
            current_index = self.PHASE_ORDER.index(phase)
        except ValueError:
            return {"error": "未知的阶段"}
        
        total_phases = len(self.PHASE_ORDER)
        
        return {
            "current_phase": phase,
            "progress_percentage": (current_index / (total_phases - 1)) * 100,
            "current_step": current_index + 1,
            "total_steps": total_phases,
            "remaining_phases": self.PHASE_ORDER[current_index + 1:]
        }
    
    def is_phase_completed(self, phase: str) -> bool:
        """检查阶段是否已完成。"""
        try:
            current_phase = self.state_manager.get_current_phase()
            current_index = self.PHASE_ORDER.index(current_phase)
            phase_index = self.PHASE_ORDER.index(phase)
            return current_index > phase_index
        except ValueError:
            return False
    
    def get_workflow_summary(self) -> Dict[str, any]:
        """获取工作流摘要。"""
        current_phase = self.state_manager.get_current_phase()
        phase_progress = self.get_phase_progress(current_phase)
        signoff_status = self.state_manager.get_signoff_status("requirements")
        
        return {
            "current_phase": current_phase,
            "phase_progress": phase_progress,
            "requirements_signoff": signoff_status,
            "can_proceed": self.state_manager.can_proceed_to_next_phase()
        }
