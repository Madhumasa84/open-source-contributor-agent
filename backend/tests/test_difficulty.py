import pytest
from app.schemas.repository import DifficultyLevel, RepositoryOverview
from app.services.difficulty import DifficultyEstimator

def make_repo(**kwargs) -> RepositoryOverview:
    default_args = {
        "root": "/tmp/test",
        "languages": {},
        "frameworks": [],
        "dependencies": {},
        "test_frameworks": [],
        "build_systems": [],
        "architecture": [],
        "important_files": [],
        "entry_points": [],
        "risks": [],
        "code_quality_metrics": {},
        "contribution_difficulty": DifficultyLevel.easy,
    }
    default_args.update(kwargs)
    return RepositoryOverview(**default_args)

def test_estimate_easy():
    estimator = DifficultyEstimator()
    # score = 1 ("typo")
    estimate = estimator.estimate("typo in docs", None)

    assert estimate.level == DifficultyLevel.easy
    assert estimate.files_impacted == 1
    assert estimate.estimated_work == "1-3 hours"
    assert "Issue text suggests a documentation or copy-only change." in estimate.rationale

def test_estimate_medium():
    estimator = DifficultyEstimator()
    # score = 4 ("security")
    estimate = estimator.estimate("security issue", None)

    assert estimate.level == DifficultyLevel.medium
    assert estimate.files_impacted == 3
    assert estimate.estimated_work == "Half day to 1 day"
    assert "Issue mentions high-risk implementation areas." in estimate.rationale

def test_estimate_hard():
    estimator = DifficultyEstimator()
    # score = 6 (4 from "security", 2 from "bug")
    estimate = estimator.estimate("security bug", None)

    assert estimate.level == DifficultyLevel.hard
    assert estimate.files_impacted == 5
    assert estimate.estimated_work == "1-3 days"

def test_estimate_expert():
    estimator = DifficultyEstimator()
    # score = 7 (4 from "security", 3 from file_count > 400)
    repo = make_repo(code_quality_metrics={"code_file_count": 500})
    estimate = estimator.estimate("security", repo)

    assert estimate.level == DifficultyLevel.expert
    assert estimate.files_impacted == 8
    assert estimate.estimated_work == "Several days"
    assert "Repository has a large code surface." in estimate.rationale

def test_repository_risks_and_entry_points():
    estimator = DifficultyEstimator()
    # score = 1 (risks)
    repo = make_repo(risks=["high risk"], entry_points=["main.py"])
    estimate = estimator.estimate("", repo)

    assert estimate.level == DifficultyLevel.easy
    assert estimate.files_impacted == 2
    assert "Repository analyzer detected contribution risks." in estimate.rationale

def test_edge_cases():
    estimator = DifficultyEstimator()
    # score = 0
    estimate = estimator.estimate(None, None)

    assert estimate.level == DifficultyLevel.easy
    assert estimate.files_impacted == 1
    assert "Estimate is based on repository size and limited issue context." in estimate.rationale
