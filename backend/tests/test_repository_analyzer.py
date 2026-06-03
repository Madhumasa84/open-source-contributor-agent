import json

import pytest

from app.services.repository_analyzer import RepositoryAnalyzer


@pytest.mark.asyncio
async def test_repository_analyzer_detects_next_fastapi_pytest(tmp_path):
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "dependencies": {"next": "latest", "react": "latest"},
                "devDependencies": {"vitest": "latest"},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "requirements.txt").write_text("fastapi\npytest\nsqlalchemy\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "test_main.py").write_text("def test_ok(): assert True\n", encoding="utf-8")

    overview = await RepositoryAnalyzer().analyze(tmp_path)

    assert overview.languages["Python"] == 2
    assert "Next.js" in overview.frameworks
    assert "FastAPI" in overview.frameworks
    assert "pytest" in overview.test_frameworks
    assert "main.py" in overview.entry_points
