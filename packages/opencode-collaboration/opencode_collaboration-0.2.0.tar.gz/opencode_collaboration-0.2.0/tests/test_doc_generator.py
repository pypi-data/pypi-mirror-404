import pytest
"""文档生成器测试。"""
import tempfile
import os
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.doc_generator import DocGenerator, QualityChecker, QualityCheckResult


class TestDocGenerator:
    """文档生成器测试类。"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def doc_generator(self, temp_dir):
        """创建文档生成器实例。"""
        return DocGenerator(temp_dir)
    
    def test_initialization(self, temp_dir):
        """测试初始化。"""
        dg = DocGenerator(temp_dir)
        
        assert dg.project_path.exists()
        assert dg.templates_dir.exists()
        assert dg.output_dir.exists()
    
    def test_list_document_types(self, doc_generator):
        """测试列出文档类型。"""
        types = doc_generator.list_document_types()
        
        assert "requirements" in types
        assert "design" in types
        assert "test_case" in types
        assert "bug_report" in types
        assert "test_report" in types
        assert "deployment_report" in types
    
    def test_get_summary(self, doc_generator):
        """测试获取摘要。"""
        summary = doc_generator.get_summary()
        
        assert "templates_dir" in summary
        assert "output_dir" in summary
        assert "supported_types" in summary
        assert len(summary["supported_types"]) == 6
    
    def test_generate_unknown_document_type(self, doc_generator):
        """测试生成未知文档类型。"""
        success, message = doc_generator.generate_document(
            doc_type="unknown",
            context={"project_name": "Test"}
        )
        
        assert success == False
        assert "未知文档类型" in message


class TestQualityChecker:
    """质量检查器测试类。"""
    
    @pytest.fixture
    def quality_checker(self):
        """创建质量检查器实例。"""
        return QualityChecker()
    
    def test_check_valid_content(self, quality_checker):
        """测试检查有效内容。"""
        content = """# 测试项目 - 需求文档

## 版本信息
- **版本**: v1
- **创建日期**: 2024-01-01

## 1. 项目概述
这是一个测试项目，用于验证质量检查功能。

## 2. 功能需求
这是一个完整的需求描述，包含足够多的内容来通过质量检查。
"""
        
        result = quality_checker.check(content)
        
        assert result.passed == True
        assert result.score >= 80.0
    
    def test_check_short_title(self, quality_checker):
        """测试检查过短标题。"""
        content = """# 测试

## 版本信息
这是一个测试文档，内容很少。
"""
        
        result = quality_checker.check(content)
        
        assert "标题过短" in result.issues
    
    def test_check_missing_required_sections(self, quality_checker):
        """测试检查缺少必要章节。"""
        content = """# 测试项目

这是一个没有标准章节的文档。
"""
        
        result = quality_checker.check(content)
        
        assert "缺少必要章节" in result.issues
    
    def test_check_no_h1_title(self, quality_checker):
        """测试检查缺少一级标题。"""
        content = """## 版本信息
这是一个没有一级标题的文档。
"""
        
        result = quality_checker.check(content)
        
        assert "缺少一级标题" in result.issues
    
    def test_check_empty_sections(self, quality_checker):
        """测试检查空章节。"""
        content = """# 测试项目

## 版本信息

## 项目概述
这是一个测试。
"""
        
        result = quality_checker.check(content)
        
        assert any("空章节" in issue for issue in result.issues)
    
    def test_get_check_summary(self, quality_checker):
        """测试获取检查摘要。"""
        content = """# 测试项目 - 需求文档

## 版本信息
- **版本**: v1

## 1. 项目概述
这是一个测试项目。
"""
        
        summary = quality_checker.get_check_summary(content)
        
        assert "passed" in summary
        assert "score" in summary
        assert "issues_count" in summary
    
    def test_quality_score_calculation(self, quality_checker):
        """测试质量分数计算。"""
        good_content = """# 测试项目 - 需求文档

## 版本信息
- **版本**: v1
- **创建日期**: 2024-01-01

## 1. 项目概述
这是一个完整的测试项目描述，包含足够多的内容来通过所有的质量检查。

## 2. 功能需求
这是一个详细的功能需求描述，涵盖了项目的所有功能点。
"""
        
        result = quality_checker.check(good_content)
        
        assert result.score > 80.0
        assert len(result.issues) == 0


class TestDocGeneratorWithTemplates:
    """带模板的文档生成器测试类。"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def doc_generator(self, temp_dir):
        """创建文档生成器实例。"""
        return DocGenerator(temp_dir)
    
    def test_generate_requirements_document(self, doc_generator):
        """测试生成需求文档。"""
        context = {
            "project_name": "TestProject",
            "version": "v1",
            "created_at": "2024-01-01",
            "status": "草稿"
        }
        
        success, output_path = doc_generator.generate_document(
            doc_type="requirements",
            context=context
        )
        
        assert success == True
        assert "requirements_TestProject_v1.md" in output_path
        assert os.path.exists(output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "TestProject" in content
        assert "需求文档" in content
    
    def test_generate_design_document(self, doc_generator):
        """测试生成设计文档。"""
        context = {
            "project_name": "TestProject",
            "version": "v1",
            "created_at": "2024-01-01"
        }
        
        success, output_path = doc_generator.generate_document(
            doc_type="design",
            context=context
        )
        
        assert success == True
        assert "detailed_design_TestProject_v1.md" in output_path
    
    def test_generate_test_case_document(self, doc_generator):
        """测试生成测试用例文档。"""
        context = {
            "project_name": "TestProject",
            "version": "v1"
        }
        
        success, output_path = doc_generator.generate_document(
            doc_type="test_case",
            context=context
        )
        
        assert success == True
        assert "test_case_TestProject_v1.md" in output_path
    
    def test_generate_bug_report_document(self, doc_generator):
        """测试生成Bug报告文档。"""
        context = {
            "project_name": "TestProject",
            "version": "v1"
        }
        
        success, output_path = doc_generator.generate_document(
            doc_type="bug_report",
            context=context
        )
        
        assert success == True
        assert "bug_report_TestProject_v1.md" in output_path
    
    def test_generate_test_report_document(self, doc_generator):
        """测试生成测试报告文档。"""
        context = {
            "project_name": "TestProject",
            "version": "v1"
        }
        
        success, output_path = doc_generator.generate_document(
            doc_type="test_report",
            context=context
        )
        
        assert success == True
        assert "test_report_TestProject_v1.md" in output_path
    
    def test_generate_deployment_report_document(self, doc_generator):
        """测试生成部署报告文档。"""
        context = {
            "project_name": "TestProject",
            "version": "v1"
        }
        
        success, output_path = doc_generator.generate_document(
            doc_type="deployment_report",
            context=context
        )
        
        assert success == True
        assert "deployment_report_TestProject_v1.md" in output_path


class TestDocGeneratorIntegration:
    """文档生成器集成测试类。"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def doc_generator(self, temp_dir):
        """创建文档生成器实例。"""
        return DocGenerator(temp_dir)
    
    @pytest.fixture
    def quality_checker(self):
        """创建质量检查器实例。"""
        return QualityChecker()
    
    def test_generate_and_check_document(self, doc_generator, quality_checker):
        """测试生成并检查文档。"""
        context = {
            "project_name": "TestProject",
            "version": "v1",
            "created_at": "2024-01-01"
        }
        
        success, output_path = doc_generator.generate_document(
            doc_type="requirements",
            context=context
        )
        
        assert success == True
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        result = quality_checker.check(content)
        
        assert result.passed == True
    
    def test_check_and_regenerate(self, doc_generator, quality_checker):
        """测试检查并重新生成。"""
        context = {
            "project_name": "TestProject",
            "version": "v1",
            "created_at": "2024-01-01"
        }
        
        success, output_path, result = quality_checker.check_and_regenerate(
            doc_generator,
            "requirements",
            context
        )
        
        assert success == True
        assert result.passed == True
    
    def test_all_document_types_workflow(self, doc_generator, quality_checker):
        """测试所有文档类型的工作流程。"""
        context = {
            "project_name": "IntegrationTest",
            "version": "v1",
            "created_at": "2024-01-01"
        }
        
        document_types = [
            "requirements",
            "design",
            "test_case",
            "bug_report",
            "test_report",
            "deployment_report"
        ]
        
        for doc_type in document_types:
            success, output_path = doc_generator.generate_document(
                doc_type=doc_type,
                context=context
            )
            
            assert success == True, f"文档类型 {doc_type} 生成失败"
            
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = quality_checker.check(content)
            
            assert result.passed == True, f"文档类型 {doc_type} 质量检查失败: {result.issues}"


class TestQualityCheckerEdgeCases:
    """质量检查器边界情况测试类。"""
    
    @pytest.fixture
    def quality_checker(self):
        """创建质量检查器实例。"""
        return QualityChecker()
    
    def test_empty_content(self, quality_checker):
        """测试空内容。"""
        result = quality_checker.check("")
        
        assert result.passed == False
        assert result.score < 50.0
        assert len(result.issues) > 0
    
    def test_very_short_content(self, quality_checker):
        """测试非常短的内容。"""
        result = quality_checker.check("# Hi")
        
        assert result.passed == False
        assert "标题过短" in result.issues
        assert "内容过短" in result.issues
    
    def test_content_with_only_headers(self, quality_checker):
        """测试只有标题的内容。"""
        content = """# 项目标题

## 章节一

## 章节二

## 章节三
"""
        
        result = quality_checker.check(content)
        
        assert "内容过短" in result.issues
    
    def test_content_with_special_characters(self, quality_checker):
        """测试包含特殊字符的内容。"""
        content = """# 项目-名称_v1.0

## 版本-信息
- **版本**: v1.0
- **日期**: 2024-01-01

## 1. 项目概述
这是一个包含特殊字符的测试内容，用于验证质量检查功能。
"""
        
        result = quality_checker.check(content)
        
        assert result.passed == True


class TestDocGeneratorWithCustomOutput:
    """自定义输出路径测试类。"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def doc_generator(self, temp_dir):
        """创建文档生成器实例。"""
        return DocGenerator(temp_dir)
    
    def test_custom_output_path(self, doc_generator):
        """测试自定义输出路径。"""
        context = {"project_name": "Test"}
        
        custom_path = "custom/output/test_doc.md"
        success, output_path = doc_generator.generate_document(
            doc_type="requirements",
            context=context,
            output_path=custom_path
        )
        
        assert success == True
        assert output_path == custom_path
        assert os.path.exists(custom_path)
    
    def test_version_parameter(self, doc_generator):
        """测试版本参数。"""
        context = {"project_name": "Test"}
        
        success, output_path = doc_generator.generate_document(
            doc_type="requirements",
            context=context,
            version="v2.0"
        )
        
        assert success == True
        assert "v2.0" in output_path
