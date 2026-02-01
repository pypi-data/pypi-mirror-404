"""Tests for Claude session"""

import os
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from session import ClaudeSession


def test_session_initialization():
    """Test that ClaudeSession initializes correctly"""
    session = ClaudeSession()

    assert session.model == "claude-sonnet-4-20250514"
    assert session.conversation_history == []
    assert session.project_path is not None
    assert isinstance(session.project_path, Path)


def test_session_with_project_path():
    """Test session with custom project path"""
    test_path = "/tmp/test_project"
    session = ClaudeSession(project_path=test_path)

    assert session.project_path == Path(test_path)


def test_session_with_read_only_files(tmp_path):
    """Test session with read-only files"""
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("def hello():\n    print('world')")

    session = ClaudeSession(
        project_path=str(tmp_path),
        read_only_files=["test.py"]
    )

    assert "test.py" in session.read_only_context
    assert "def hello()" in session.read_only_context


@pytest.mark.skipif(
    not os.environ.get('ANTHROPIC_API_KEY'),
    reason="ANTHROPIC_API_KEY not set"
)
def test_send_message_real_api():
    """Integration test with real Claude API"""
    session = ClaudeSession()

    if not session.client:
        pytest.skip("Claude API client not initialized")

    response = session.send_message("Say 'test passed' and nothing else")

    assert response is not None
    assert len(response) > 0
    assert "test" in response.lower()
    print(f"✅ API response: {response}")
