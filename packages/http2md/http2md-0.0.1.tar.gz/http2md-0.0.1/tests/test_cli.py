import subprocess
import pytest
import sys

def test_cli_help():
    """Test that the CLI runs and shows help."""
    # We run the module directly to test
    result = subprocess.run(
        [sys.executable, "-m", "http2md.cli", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Convert HTTP content to Markdown" in result.stdout
