import json
import subprocess
from datetime import datetime
from pathlib import Path

from rich.console import Console

console = Console()


def save_test_file(test_content):
    """
    Save test file from API response content

    Args:
        test_content: JSON string response from API

    Returns:
        Dictionary with file information or None if failed
    """
    try:
        parsed_response = json.loads(test_content)

        if parsed_response.get("error"):
            console.print(
                f"❌ API responded with an error: {parsed_response['error']}",
                style="bold red",
            )
            return None

        # Support both shapes:
        # 1) Top-level fields: { file_content: "...", test_file_path: "..." }
        # 2) Nested object: { file_content: { file_content: "...", test_file_path: "..." } }
        # 3) Nested under test_file_content: { test_file_content: { ... same keys ... } }

        content_str = None
        meta_source = parsed_response

        fc = parsed_response.get("file_content")
        tfc = parsed_response.get("test_file_content")

        if isinstance(fc, dict):
            meta_source = fc
            content_str = meta_source.get("file_content") or meta_source.get(
                "test_file_content"
            )
        elif isinstance(tfc, dict):
            meta_source = tfc
            content_str = meta_source.get("file_content") or meta_source.get(
                "test_file_content"
            )
        else:
            # Assume top-level string content
            content_str = parsed_response.get("file_content") or parsed_response.get(
                "test_file_content"
            )

        if not content_str:
            console.print(
                "❌ API response missing file content string", style="bold red"
            )
            console.print(
                f"ℹ️ Response keys: {list(parsed_response.keys())}", style="bold cyan"
            )
            return None

        # Resolve file path from the most specific source
        file_path = (
            meta_source.get("test_file_path")
            or meta_source.get("file_path")
            or meta_source.get("file_name")
            or meta_source.get("file")
            or parsed_response.get("test_file_path")
            or parsed_response.get("file_path")
            or parsed_response.get("file_name")
            or parsed_response.get("file")
        )

        if not file_path:
            console.print(
                "❌ API response missing test_file_path or file_path field",
                style="bold red",
            )
            console.print(
                f"ℹ️ Response keys: {list(parsed_response.keys())}", style="bold cyan"
            )
            return None

        # Create directory if it doesn't exist and write file
        file_path_obj = Path(file_path)
        if not str(file_path_obj).startswith("tests/"):
            file_path_obj = Path("tests") / file_path_obj.name

        # Ensure Python test files have .py extension
        if not file_path_obj.name.endswith(".py"):
            # Replace any other extension with .py
            stem = file_path_obj.stem
            if "." in stem:
                # Handle cases like "test.rb" -> "test.py"
                stem = stem.split(".")[0]
            file_path_obj = file_path_obj.parent / f"{stem}.py"

        # Add timestamp prefix if filename doesn't have one
        filename = file_path_obj.name
        if not _has_timestamp_prefix(filename):
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            new_filename = f"{timestamp}_{filename}"
            file_path_obj = file_path_obj.parent / new_filename

        # Write the file
        try:
            file_path_obj.write_text(content_str)
        except FileNotFoundError:
            # Create directory if it doesn't exist
            file_path_obj.parent.mkdir(parents=True, exist_ok=True)
            file_path_obj.write_text(content_str)

        absolute_path = file_path_obj.resolve()

        # Run ruff validation on the saved file
        _run_ruff_validation(str(absolute_path))

        return {
            "file_path": str(file_path_obj),  # Return actual saved path with timestamp
            "absolute_path": str(absolute_path),
            "test_class_name": meta_source.get("test_class_name")
            or parsed_response.get("test_class_name"),
            "method_name": meta_source.get("method_name")
            or parsed_response.get("method_name"),
            "framework": meta_source.get("framework")
            or parsed_response.get("framework", "pytest"),
        }

    except json.JSONDecodeError as e:
        console.print(f"❌ Failed to parse API response as JSON: {e}", style="bold red")
        console.print(f"📄 Raw response: {test_content[:200]}...", style="dim white")
        raise
    except Exception as e:
        console.print(f"❌ Failed to save test file: {e}", style="bold red")
        return None


def _has_timestamp_prefix(filename):
    """
    Check if filename has numeric prefix (any numbers followed by underscore)

    Args:
        filename: The filename to check

    Returns:
        True if filename starts with numbers and underscore
    """
    import re

    # Pattern: one or more digits followed by underscore at start of filename
    numeric_pattern = r"^\d+_"
    return bool(re.match(numeric_pattern, filename))


def _run_ruff_validation(file_path):
    """
    Run ruff validation on the saved test file

    Args:
        file_path: Absolute path to the test file
    """
    try:
        # Run ruff silently; perform safe fixes if needed, but do not print to user
        subprocess.run(
            ["ruff", "check", file_path], capture_output=True, text=True, timeout=30
        )

        subprocess.run(
            ["ruff", "check", "--fix", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        subprocess.run(
            ["ruff", "check", file_path], capture_output=True, text=True, timeout=30
        )

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        # Intentionally suppress all output; ruff is best-effort
        pass
