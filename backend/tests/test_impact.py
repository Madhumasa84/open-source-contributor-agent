import pytest
from pathlib import Path

from app.services.impact import ImpactAnalyzer
from app.schemas.repository import RiskLevel


def test_analyze_python_files_empty(tmp_path: Path):
    analyzer = ImpactAnalyzer()

    # Test with empty relative_files
    result = analyzer.analyze_python_files(tmp_path, [])
    assert result.files_modified == []
    assert result.functions_modified == []
    assert result.classes_modified == []
    assert result.dependency_impact == []
    assert result.risk_level == RiskLevel.low

    # Test with non-existent and non-python files
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("hello")

    result = analyzer.analyze_python_files(tmp_path, ["test.txt", "non_existent.py"])
    assert result.files_modified == ["test.txt", "non_existent.py"]
    assert result.functions_modified == []
    assert result.classes_modified == []
    assert result.dependency_impact == []
    assert result.risk_level == RiskLevel.low


def test_analyze_python_files_basic(tmp_path: Path):
    analyzer = ImpactAnalyzer()

    py_file = tmp_path / "test_basic.py"
    py_file.write_text("import os\n\ndef foo():\n    pass\n\nasync def bar():\n    pass")

    result = analyzer.analyze_python_files(tmp_path, ["test_basic.py"])

    assert result.files_modified == ["test_basic.py"]
    assert "test_basic.py:foo" in result.functions_modified
    assert "test_basic.py:bar" in result.functions_modified
    assert len(result.functions_modified) == 2
    assert result.classes_modified == []
    assert result.dependency_impact == ["test_basic.py"]
    assert result.risk_level == RiskLevel.low


def test_analyze_python_files_with_classes(tmp_path: Path):
    analyzer = ImpactAnalyzer()

    py_file = tmp_path / "test_class.py"
    py_file.write_text("class MyClass:\n    def method(self):\n        pass")

    result = analyzer.analyze_python_files(tmp_path, ["test_class.py"])

    assert result.files_modified == ["test_class.py"]
    assert "test_class.py:method" in result.functions_modified
    assert result.classes_modified == ["test_class.py:MyClass"]
    assert result.dependency_impact == []
    assert result.risk_level == RiskLevel.medium


def test_analyze_python_files_syntax_error(tmp_path: Path):
    analyzer = ImpactAnalyzer()

    py_file = tmp_path / "test_error.py"
    py_file.write_text("def invalid_syntax(:\n    pass")

    result = analyzer.analyze_python_files(tmp_path, ["test_error.py"])

    assert result.files_modified == ["test_error.py"]
    assert result.functions_modified == []
    assert result.classes_modified == []
    assert result.dependency_impact == ["test_error.py: parse failed"]
    assert result.risk_level == RiskLevel.low


def test_analyze_python_files_medium_risk(tmp_path: Path):
    analyzer = ImpactAnalyzer()

    files = []
    for i in range(9):
        filename = f"test_{i}.py"
        (tmp_path / filename).write_text("def func(): pass")
        files.append(filename)

    result = analyzer.analyze_python_files(tmp_path, files)
    assert result.risk_level == RiskLevel.medium


def test_analyze_python_files_high_risk(tmp_path: Path):
    analyzer = ImpactAnalyzer()

    files = []
    for i in range(21):
        filename = f"test_{i}.py"
        (tmp_path / filename).write_text("def func(): pass")
        files.append(filename)

    result = analyzer.analyze_python_files(tmp_path, files)
    assert result.risk_level == RiskLevel.high
