"""文档生成器模块。"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import re


logger = logging.getLogger(__name__)


class DocGeneratorError(Exception):
    """文档生成异常基类。"""
    pass


class TemplateNotFoundError(DocGeneratorError):
    """模板不存在异常。"""
    pass


class QualityCheckError(DocGeneratorError):
    """质量检查异常。"""
    pass


class RenderingError(DocGeneratorError):
    """渲染异常。"""
    pass


@dataclass
class DocumentInfo:
    """文档信息。"""
    doc_type: str
    template_name: str
    output_path: str
    title: str = ""
    version: str = "v1"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class QualityCheckResult:
    """质量检查结果。"""
    passed: bool
    score: float
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class DocGenerator:
    """文档生成器。"""
    
    TEMPLATES_DIR = "templates"
    OUTPUT_DIR = "output"
    
    DOCUMENT_TYPES = {
        "requirements": {
            "template": "requirements_TEMPLATE.md",
            "output_pattern": "docs/01-requirements/requirements_{project}_{version}.md",
            "review_template": "requirements_review_TEMPLATE.md",
            "review_output_pattern": "docs/01-requirements/requirements_{project}_review_{version}.md"
        },
        "design": {
            "template": "design_TEMPLATE.md",
            "output_pattern": "docs/02-design/detailed_design_{project}_{version}.md",
            "review_template": "design_review_TEMPLATE.md",
            "review_output_pattern": "docs/02-design/design_review_{project}_{version}.md"
        },
        "test_case": {
            "template": "test_case_TEMPLATE.md",
            "output_pattern": "docs/03-test/test_case_{project}_{version}.md"
        },
        "bug_report": {
            "template": "bug_report_TEMPLATE.md",
            "output_pattern": "docs/03-test/bug_report_{project}_{version}.md"
        },
        "test_report": {
            "template": "test_report_TEMPLATE.md",
            "output_pattern": "docs/03-test/test_report_{project}_{version}.md"
        },
        "deployment_report": {
            "template": "deployment_report_TEMPLATE.md",
            "output_pattern": "docs/04-deployment/deployment_report_{project}_{version}.md"
        }
    }
    
    def __init__(self, project_path: str, templates_dir: Optional[str] = None):
        """初始化文档生成器。"""
        self.project_path = Path(project_path)
        self.templates_dir = Path(templates_dir) if templates_dir else self.project_path / self.TEMPLATES_DIR
        self.output_dir = self.project_path / self.OUTPUT_DIR
        
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """确保必要目录存在。"""
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_document(
        self,
        doc_type: str,
        context: Dict[str, Any],
        output_path: Optional[str] = None,
        version: str = "v1"
    ) -> Tuple[bool, str]:
        """生成文档。"""
        if doc_type not in self.DOCUMENT_TYPES:
            return False, f"未知文档类型: {doc_type}"
        
        config = self.DOCUMENT_TYPES[doc_type]
        template_name = config["template"]
        
        if not self._template_exists(template_name):
            return False, f"模板不存在: {template_name}"
        
        try:
            project_name = context.get("project_name", "project")
            
            full_output_path = output_path or config["output_pattern"].format(
                project=project_name,
                version=version
            )
            
            rendered_content = self._render_template(template_name, context)
            
            os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
            
            with open(full_output_path, 'w', encoding='utf-8') as f:
                f.write(rendered_content)
            
            logger.info(f"文档已生成: {full_output_path}")
            
            return True, full_output_path
            
        except Exception as e:
            raise RenderingError(f"文档渲染失败: {e}")
    
    def generate_review_document(
        self,
        doc_type: str,
        context: Dict[str, Any],
        output_path: Optional[str] = None,
        version: str = "v1"
    ) -> Tuple[bool, str]:
        """生成评审文档。"""
        if doc_type not in self.DOCUMENT_TYPES:
            return False, f"未知文档类型: {doc_type}"
        
        config = self.DOCUMENT_TYPES[doc_type]
        review_template = config.get("review_template")
        
        if not review_template:
            return False, f"文档类型 {doc_type} 不支持评审文档"
        
        if not self._template_exists(review_template):
            return False, f"评审模板不存在: {review_template}"
        
        try:
            project_name = context.get("project_name", "project")
            
            full_output_path = output_path or config["review_output_pattern"].format(
                project=project_name,
                version=version
            )
            
            rendered_content = self._render_template(review_template, context)
            
            os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
            
            with open(full_output_path, 'w', encoding='utf-8') as f:
                f.write(rendered_content)
            
            return True, full_output_path
            
        except Exception as e:
            raise RenderingError(f"评审文档渲染失败: {e}")
    
    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """渲染模板。"""
        import os
        from jinja2 import Environment, FileSystemLoader
        
        templates_dir = str(self.templates_dir)
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir, exist_ok=True)
        
        try:
            env = Environment(
                loader=FileSystemLoader(templates_dir),
                autoescape=True
            )
            template = env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            raise RenderingError(f"模板渲染失败: {e}")
    
    def _template_exists(self, template_name: str) -> bool:
        """检查模板是否存在。"""
        import os
        template_path = self.templates_dir / template_name
        return os.path.exists(template_path)
    
    def list_document_types(self) -> List[str]:
        """列出支持的文档类型。"""
        return list(self.DOCUMENT_TYPES.keys())
    
    def get_template_path(self, doc_type: str) -> Optional[str]:
        """获取模板路径。"""
        if doc_type not in self.DOCUMENT_TYPES:
            return None
        return str(self.templates_dir / self.DOCUMENT_TYPES[doc_type]["template"])
    
    def create_document_from_scratch(
        self,
        doc_type: str,
        project_name: str,
        title: str,
        content: str = "",
        version: str = "v1"
    ) -> Tuple[bool, str]:
        """从零创建文档。"""
        context = {
            "project_name": project_name,
            "title": title,
            "version": version,
            "created_at": datetime.now().isoformat(),
            "content": content
        }
        
        return self.generate_document(doc_type, context, version=version)
    
    def generate_status_report(self, project_name: str, phase: str, details: Dict[str, Any]) -> Tuple[bool, str]:
        """生成状态报告。"""
        context = {
            "project_name": project_name,
            "phase": phase,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        
        return self.generate_document(
            "test_report",
            context,
            output_path=f"docs/04-deployment/status_report_{project_name}.md",
            version="v1"
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """获取生成器摘要。"""
        import os
        
        templates = []
        if self.templates_dir.exists():
            for f in os.listdir(self.templates_dir):
                if f.endswith((".md", ".j2", ".jinja2")):
                    templates.append(f)
        
        return {
            "templates_dir": str(self.templates_dir),
            "output_dir": str(self.output_dir),
            "supported_types": list(self.DOCUMENT_TYPES.keys()),
            "available_templates": templates
        }


class QualityChecker:
    """质量检查器。"""
    
    MIN_TITLE_LENGTH = 5
    MAX_TITLE_LENGTH = 100
    MIN_CONTENT_LENGTH = 50
    REQUIRED_SECTIONS = ["版本信息", "项目概述"]
    OPTIONAL_SECTIONS = ["测试结果", "部署状态"]
    
    def __init__(self):
        """初始化质量检查器。"""
        self.check_rules = {
            "title_length": self._check_title_length,
            "content_length": self._check_content_length,
            "required_sections": self._check_required_sections,
            "markdown_format": self._check_markdown_format,
            "no_empty_sections": self._check_no_empty_sections
        }
    
    def check(self, content: str, doc_type: Optional[str] = None) -> QualityCheckResult:
        """执行质量检查。"""
        issues = []
        suggestions = []
        score = 100.0
        
        for rule_name, check_func in self.check_rules.items():
            rule_issues, rule_suggestions, rule_score = check_func(content)
            issues.extend(rule_issues)
            suggestions.extend(rule_suggestions)
            score -= (100.0 - rule_score)
        
        score = max(0.0, min(100.0, score))
        passed = score >= 80.0 and len(issues) == 0
        
        return QualityCheckResult(
            passed=passed,
            score=round(score, 2),
            issues=issues,
            suggestions=suggestions
        )
    
    def _check_title_length(self, content: str) -> Tuple[List[str], List[str], float]:
        """检查标题长度。"""
        issues = []
        suggestions = []
        score = 100.0
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('#'):
                title = line.lstrip('# ').strip()
                if len(title) < self.MIN_TITLE_LENGTH:
                    issues.append(f"标题过短: '{title[:20]}...'")
                    suggestions.add("标题应至少包含5个字符")
                    score -= 10.0
                elif len(title) > self.MAX_TITLE_LENGTH:
                    issues.append(f"标题过长: '{title[:20]}...'")
                    suggestions.append("标题应不超过100个字符")
                    score -= 5.0
                break
        
        return issues, suggestions, score
    
    def _check_content_length(self, content: str) -> Tuple[List[str], List[str], float]:
        """检查内容长度。"""
        issues = []
        suggestions = []
        score = 100.0
        
        content_body = content.split('\n\n')
        total_length = sum(len(c) for c in content_body if not c.startswith('#'))
        
        if total_length < self.MIN_CONTENT_LENGTH:
            issues.append(f"内容过短: 仅有 {total_length} 个字符")
            suggestions.append("文档内容应至少包含50个字符")
            score -= 20.0
        
        return issues, suggestions, score
    
    def _check_required_sections(self, content: str) -> Tuple[List[str], List[str], float]:
        """检查必要章节。"""
        issues = []
        suggestions = []
        score = 100.0
        
        for section in self.REQUIRED_SECTIONS:
            if f"## {section}" not in content:
                issues.append(f"缺少必要章节: {section}")
                suggestions.append(f"添加 '## {section}' 章节")
                score -= 10.0
        
        return issues, suggestions, score
    
    def _check_markdown_format(self, content: str) -> Tuple[List[str], List[str], float]:
        """检查Markdown格式。"""
        issues = []
        suggestions = []
        score = 100.0
        
        lines = content.split('\n')
        
        has_h1 = any(line.startswith('# ') for line in lines)
        if not has_h1:
            issues.append("缺少一级标题 (# 标题)")
            suggestions.add("添加文档一级标题")
            score -= 10.0
        
        return issues, suggestions, score
    
    def _check_no_empty_sections(self, content: str) -> Tuple[List[str], List[str], float]:
        """检查空章节。"""
        issues = []
        suggestions = []
        score = 100.0
        
        lines = content.split('\n')
        in_section = False
        section_title = ""
        empty_count = 0
        
        for line in lines:
            if line.startswith('##'):
                if empty_count > 0 and in_section:
                    issues.append(f"空章节: {section_title}")
                    suggestions.append(f"为 '{section_title}' 添加内容")
                    score -= 5.0
                in_section = True
                section_title = line.lstrip('# ').strip()
                empty_count = 0
            elif line.strip() and in_section:
                empty_count = 0
            elif in_section:
                empty_count += 1
        
        return issues, suggestions, score
    
    def check_and_regenerate(
        self,
        doc_generator: DocGenerator,
        doc_type: str,
        context: Dict[str, Any],
        max_retries: int = 3
    ) -> Tuple[bool, str, QualityCheckResult]:
        """检查并重新生成（如果质量不达标）。"""
        for attempt in range(max_retries):
            success, output_path = doc_generator.generate_document(doc_type, context)
            
            if not success:
                return False, output_path, QualityCheckResult(
                    passed=False,
                    score=0.0,
                    issues=[f"文档生成失败: {output_path}"]
                )
            
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                result = self.check(content)
                
                if result.passed:
                    return True, output_path, result
                
                logger.warning(f"文档质量检查未通过 (尝试 {attempt + 1}/{max_retries}): {result.issues}")
                
            except Exception as e:
                return False, output_path, QualityCheckResult(
                    passed=False,
                    score=0.0,
                    issues=[f"质量检查失败: {e}"]
                )
        
        return False, output_path, QualityCheckResult(
            passed=False,
            score=0.0,
            issues=["质量检查多次未通过"]
        )
    
    def get_check_summary(self, content: str) -> Dict[str, Any]:
        """获取检查摘要。"""
        result = self.check(content)
        
        return {
            "passed": result.passed,
            "score": result.score,
            "issues_count": len(result.issues),
            "suggestions_count": len(result.suggestions),
            "issues": result.issues[:5],
            "suggestions": result.suggestions[:5]
        }
