"""
Tests for Skill Marketplace features (Phase 7.7)
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from orchestrator._internal.execution.skill_library import check_version_compatibility
from orchestrator._internal.execution.skill_registry import RegistrySkill, SkillRegistry


@pytest.fixture
def mock_session() -> Any:
    with patch("requests.Session") as mock:
        session = MagicMock()
        mock.return_value = session
        yield session

def test_check_version_compatibility() -> None:
    assert check_version_compatibility(">=1.0.0", "1.2.0")
    assert check_version_compatibility(">=1.0.0", "1.0.0")
    assert not check_version_compatibility(">=2.0.0", "1.9.9")

    assert check_version_compatibility("<2.0", "1.5")
    assert not check_version_compatibility("<2.0", "2.0")

    assert check_version_compatibility("==1.2.3", "1.2.3")
    assert not check_version_compatibility("==1.2.3", "1.2.4")

    # Approx match (tilde)
    assert check_version_compatibility("~=1.2", "1.2.0")
    assert check_version_compatibility("~=1.2", "1.9.9")
    assert not check_version_compatibility("~=1.2", "2.0.0")  # Major bump not allowed
    assert not check_version_compatibility("~=1.2", "1.1.9")

    assert check_version_compatibility("~=1.2.3", "1.2.3")
    assert check_version_compatibility("~=1.2.3", "1.2.9")
    assert not check_version_compatibility("~=1.2.3", "1.3.0") # Minor bump not allowed for 3-part tilde

def test_registry_skill_fields() -> None:
    # Verify new fields exist
    s = RegistrySkill(
        id="org/skill",
        name="skill",
        org="org",
        version="1.0.0",
        changelog={"1.0.0": "First release"},
        compatibility={"python": ">=3.9"}
    )
    assert s.changelog["1.0.0"] == "First release"
    assert s.compatibility["python"] == ">=3.9"

def test_update_skill_metadata(mock_session: Any) -> None:
    registry = SkillRegistry()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "org/skill",
        "name": "skill",
        "org": "org",
        "version": "1.0.0",
        "changelog": {"1.0.0": "Updated"},
        "compatibility": {"python": ">=3.10"}
    }
    mock_session.patch.return_value = mock_response

    updated = registry.update_skill_metadata(
        "org/skill",
        changelog={"1.0.0": "Updated"},
        compatibility={"python": ">=3.10"}
    )

    assert updated is not None
    assert updated.changelog is not None and updated.changelog["1.0.0"] == "Updated"
    assert updated.compatibility is not None and updated.compatibility["python"] == ">=3.10"

    # Verify PATCH called
    mock_session.patch.assert_called_once()
    url = mock_session.patch.call_args[0][0]
    payload = mock_session.patch.call_args[1]["json"]

    assert "/skills/org/skill" in url
    assert payload["changelog"] == {"1.0.0": "Updated"}
