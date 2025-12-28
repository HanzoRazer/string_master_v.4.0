import subprocess
import sys


def test_cli_gravity_smoke():
    """Smoke test: ensure gravity command runs without error."""
    # Test using the installed zt-gravity command or python -m
    result = subprocess.run(
        [sys.executable, "-m", "zone_tritone.cli", "gravity", "--root", "C", "--steps", "3"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    # Check return code
    assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"
    # Check for expected output (in stdout or stderr due to buffering)
    output = result.stdout + result.stderr
    assert "Gravity chain" in output or "Zone" in output, f"Expected output not found. Got: {output}"


def test_cli_analyze_smoke():
    """Smoke test: ensure analyze command runs without error."""
    result = subprocess.run(
        [sys.executable, "-m", "zone_tritone.cli", "analyze", "--chords", "Dm7 G7 Cmaj7"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    # Check return code
    assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"
    # Check for expected output
    output = result.stdout + result.stderr
    assert "Gravity Analysis" in output or "Transition statistics" in output, f"Expected output not found. Got: {output}"


def test_cli_explain_smoke():
    """Smoke test: ensure explain command runs without error."""
    result = subprocess.run(
        [sys.executable, "-m", "zone_tritone.cli", "explain", "--chords", "Dm7 G7 Cmaj7"],
        capture_output=True,
        text=True,
        timeout=5,
        encoding="utf-8",  # Explicitly use UTF-8
    )
    # Check return code
    assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"
    # Check for expected output sections (handle potential encoding variations)
    output = result.stdout + result.stderr
    assert "EXPLAIN" in output, f"Expected header not found. Got: {output}"
    assert "gravity anchors" in output or "tritone axis" in output, f"Expected anchors section not found. Got: {output}"
    assert "Step-by-step transitions" in output, f"Expected transitions section not found. Got: {output}"
    assert "Gravity comparison" in output, f"Expected comparison section not found. Got: {output}"


def test_cli_explain_html_smoke():
    """Smoke test: ensure explain --html command runs without error."""
    result = subprocess.run(
        [sys.executable, "-m", "zone_tritone.cli", "explain", "--chords", "Dm7 G7 Cmaj7", "--html"],
        capture_output=True,
        text=True,
        timeout=5,
        encoding="utf-8",
    )
    # Check return code
    assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"
    # Check for HTML output
    output = result.stdout + result.stderr
    assert "<article" in output, f"Expected HTML article tag not found. Got: {output}"
    assert "<h1>" in output or "<h2>" in output, f"Expected HTML headers not found. Got: {output}"
    assert "<table>" in output, f"Expected HTML table not found. Got: {output}"
    assert "EXPLAIN" in output, f"Expected EXPLAIN content not found. Got: {output}"


def test_cli_explain_markdown_smoke():
    """Smoke test: ensure explain --format markdown command runs without error."""
    result = subprocess.run(
        [sys.executable, "-m", "zone_tritone.cli", "explain", "--chords", "Dm7 G7 Cmaj7", "--format", "markdown"],
        capture_output=True,
        text=True,
        timeout=5,
        encoding="utf-8",
    )
    # Check return code
    assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"
    # Check for Markdown output
    output = result.stdout + result.stderr
    assert "# Zone" in output, f"Expected Markdown header not found. Got: {output}"
    assert "## " in output, f"Expected Markdown subheaders not found. Got: {output}"
    assert "| # |" in output or "| From |" in output, f"Expected Markdown table not found. Got: {output}"
    assert "EXPLAIN" in output, f"Expected EXPLAIN content not found. Got: {output}"
