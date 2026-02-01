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
    
    def _get_stage_data(self, stage: str, state: dict) -> dict:
        """获取阶段数据（处理 design 列表的情况）。"""
        config = self.STAGE_CONFIG.get(stage, {})
        status_field = config.get("status_field", stage)
        stage_data = state.get(status_field, {})
        
        # design 阶段是列表，需要找到当前进行中的设计文档
        if stage == "design" and isinstance(stage_data, list):
            # 查找状态为 in_progress 或 completed 的设计文档
            for doc in stage_data:
                if isinstance(doc, dict) and doc.get("status") in ["in_progress", "completed", "approved"]:
                    return doc
            # 如果没有找到，返回第一个
            if stage_data and isinstance(stage_data[0], dict):
                return stage_data[0]
            return {}
        
        return stage_data if isinstance(stage_data, dict) else {}
    
    def _save_stage_data(self, stage: str, state: dict, stage_data: dict):
        """保存阶段数据（处理 design 列表的情况）。"""
        config = self.STAGE_CONFIG.get(stage, {})
        status_field = config.get("status_field", stage)
        
        # design 阶段是列表，需要找到并更新对应的设计文档
        if stage == "design" and isinstance(state.get(status_field), list):
            for i, doc in enumerate(state[status_field]):
                if isinstance(doc, dict) and doc.get("status") in ["in_progress", "completed", "approved"]:
                    state[status_field][i] = stage_data
                    return
        else:
            state[status_field] = stage_data
    
    def can_sign(self, stage: str, agent: str) -> Tuple[bool, str]:
        """检查是否可以进行签署。"""
        if stage not in self.STAGE_CONFIG:
            return False, f"未知的签署阶段: {stage}"
        
        state = self.state_manager.load_state()
        stage_data = self._get_stage_data(stage, state)
        
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
        stage_data = self._get_stage_data(stage, state)
        
        signoff_key = f"{agent}_signoff"
        stage_data[signoff_key] = True
        
        self._save_stage_data(stage, state, stage_data)
        
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
        stage_data = self._get_stage_data(stage, state)
        
        stage_data[f"{agent}_signoff"] = False
        stage_data[f"{agent}_rejected"] = True
        stage_data[f"{agent}_rejection_reason"] = reason
        
        self._save_stage_data(stage, state, stage_data)
        
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
        
        state = self.state_manager.load_state()
        stage_data = self._get_stage_data(stage, state)
        
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
