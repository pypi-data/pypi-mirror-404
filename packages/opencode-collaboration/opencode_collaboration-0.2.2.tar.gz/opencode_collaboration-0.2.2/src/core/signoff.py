"""签署引擎模块。"""
from typing import Tuple


class SignoffError(Exception):
    """签署异常基类。"""
    pass


class PermissionDeniedError(SignoffError):
    """权限不足异常。"""
    pass


class InvalidStateError(SignoffError):
    """状态无效异常。"""
    pass


class DuplicateSignoffError(SignoffError):
    """重复签署异常。"""
    pass


class RejectionError(SignoffError):
    """拒签异常。"""
    pass


class SignoffEngine:
    """签署引擎。"""
    
    STAGE_CONFIG = {
        "requirements": {
            "agent1_role": "产品经理",
            "agent2_role": "开发",
            "status_field": "requirements"
        },
        "design": {
            "agent1_role": "产品经理",
            "agent2_role": "开发",
            "status_field": "design"
        },
        "test": {
            "agent1_role": "产品经理",
            "agent2_role": "开发",
            "status_field": "test"
        }
    }
    
    def __init__(self, state_manager, workflow_engine):
        """初始化签署引擎。"""
        self.state_manager = state_manager
        self.workflow_engine = workflow_engine
    
    def can_sign(self, stage: str, agent: str) -> Tuple[bool, str]:
        """检查是否可以进行签署。"""
        if stage not in self.STAGE_CONFIG:
            return False, f"未知的签署阶段: {stage}"
        
        config = self.STAGE_CONFIG[stage]
        state = self.state_manager.load_state()
        stage_data = state.get(config["status_field"], {})
        
        required_status = {
            "requirements": "review",
            "design": "review",
            "test": "in_progress"
        }
        
        current_status = stage_data.get("status", "")
        if current_status not in [required_status.get(stage, ""), "approved", "passed"]:
            return False, f"当前阶段状态不允许签署: {current_status}"
        
        signoff_key = f"{agent}_signoff"
        if stage_data.get(signoff_key, False):
            return False, f"{agent}已经签署过"
        
        return True, ""
    
    def sign(self, stage: str, agent: str, comment: str = "") -> dict:
        """执行签署操作。"""
        can_sign, message = self.can_sign(stage, agent)
        if not can_sign:
            raise SignoffError(message)
        
        state = self.state_manager.load_state()
        config = self.STAGE_CONFIG[stage]
        stage_data = state.get(config["status_field"], {})
        
        signoff_key = f"{agent}_signoff"
        stage_data[signoff_key] = True
        
        state["updated_at"] = self.state_manager.load_state()
        self.state_manager.save_state(state)
        
        self.state_manager.add_history(
            action="signoff",
            agent=agent,
            details=f"签署{stage}阶段: {comment}"
        )
        
        return {
            "stage": stage,
            "agent": agent,
            "signed": True,
            "comment": comment
        }
    
    def reject(self, stage: str, agent: str, reason: str) -> dict:
        """处理拒签。"""
        if len(reason) < 10:
            raise RejectionError("拒签原因必须不少于10个字符")
        
        state = self.state_manager.load_state()
        config = self.STAGE_CONFIG[stage]
        stage_data = state.get(config["status_field"], {})
        
        stage_data[f"{agent}_signoff"] = False
        stage_data[f"{agent}_rejected"] = True
        stage_data[f"{agent}_rejection_reason"] = reason
        
        self.state_manager.save_state(state)
        
        self.workflow_engine.handle_rejection(stage, reason)
        
        self.state_manager.add_history(
            action="reject",
            agent=agent,
            details=f"拒签{stage}阶段，原因为: {reason}"
        )
        
        return {
            "stage": stage,
            "agent": agent,
            "rejected": True,
            "reason": reason
        }
    
    def get_signoff_summary(self, stage: str) -> dict:
        """获取签署摘要。"""
        if stage not in self.STAGE_CONFIG:
            return {"error": f"未知的签署阶段: {stage}"}
        
        config = self.STAGE_CONFIG[stage]
        state = self.state_manager.load_state()
        stage_data = state.get(config["status_field"], {})
        
        return {
            "stage": stage,
            "pm_signoff": stage_data.get("pm_signoff", False),
            "dev_signoff": stage_data.get("dev_signoff", False),
            "both_signed": stage_data.get("pm_signoff", False) and stage_data.get("dev_signoff", False),
            "pm_rejected": stage_data.get("pm_rejected", False),
            "dev_rejected": stage_data.get("dev_rejected", False)
        }
    
    def check_all_signed(self, stages: list = None) -> bool:
        """检查是否所有阶段都已签署。"""
        if stages is None:
            stages = ["requirements", "design"]
        
        for stage in stages:
            summary = self.get_signoff_summary(stage)
            if "error" in summary:
                continue
            if not summary.get("both_signed", False):
                return False
        
        return True
