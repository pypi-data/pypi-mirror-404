import json
import os
from pathlib import Path
from typing import Optional
import time
import random
import typer
from rich.console import Console

try:
    import tng_utils
except ImportError:
    tng_utils = None

app = typer.Typer(help="TNG - Automated Test Generation for Python")
console = Console()


def load_config() -> dict:
    """Load config from local tng_config.py"""
    config_file = Path.cwd() / "tng_config.py"

    if not config_file.exists():
        return {}

    # Read and exec the config file
    config = {}
    try:
        exec(config_file.read_text(), config)
        # Extract only uppercase keys (config values)
        return {k: v for k, v in config.items() if k.isupper()}
    except Exception:
        return {}


@app.command()
def init(
    api_key: Optional[str] = typer.Option(None, help="Your TNG API Key"),
    framework: str = typer.Option("fastapi", help="Web framework (fastapi)"),
    test_framework: str = typer.Option("pytest", help="Test framework (pytest, unittest)")
):
    console.print("[bold blue]TNG Configuration Setup[/bold blue]")

    config_file = Path.cwd() / "tng_config.py"

    if config_file.exists():
        console.print("[yellow]tng_config.py already exists. Keeping existing config.[/yellow]")
        return

    # Use provided key or empty string
    key_value = api_key or ""

    config_content = f'''"""TNG Configuration - Project settings for test generation"""

# API Configuration
API_KEY = "{key_value}"
API_URL = "https://app.tng.sh/"

# Framework Detection
# Options: fastapi, flask, , generic
FRAMEWORK = "{framework}"

# Testing Configuration
TEST_FRAMEWORK = "{test_framework}"  # pytest, unittest
MOCK_LIBRARY = "pytest-mock"  # pytest-mock, unittest.mock

# Background Workers
# Options: celery, rq, dramatiq, none
WORKER = "none"

# Email
# Options: fastmail, sendgrid, none
MAILER = "none"

# ORM
# Options: sqlalchemy, django-orm, tortoise, none
ORM = "none"

# FastAPI App Path (for route introspection)
# Example: "main.py:app" or "app/api.py"
FASTAPI_APP_PATH = ""

# Test Directory
TEST_DIRECTORY = "tests"
'''

    config_file.write_text(config_content)
    console.print(f"[green]✓[/green] Created {config_file}")


@app.command("i")
def interactive():
    try:
        from tng_py.ui.go_ui_session import GoUISession

        ui = GoUISession()
        ui.start()

        while ui.running():
            choice = ui.show_menu()

            if choice == "exit":
                ui.stop()
                break
            elif choice == "tests" or choice == "generate_tests":
                # Show generate tests UI
                from tng_py.ui.generate_tests_ui import GenerateTestsUI
                gen_ui = GenerateTestsUI()
                gen_ui.show(is_audit=False)
            elif choice == "audit":
                # Show audit UI
                from tng_py.ui.generate_tests_ui import GenerateTestsUI
                gen_ui = GenerateTestsUI()
                gen_ui.show(is_audit=True)
            elif choice == "stats":
                config = load_config()
                if tng_utils and config.get("API_KEY"):
                    try:
                        stats = tng_utils.get_user_stats(
                            config.get("API_URL", "https://app.tng.sh/"),
                            config.get("API_KEY")
                        )
                        ui.show_stats(json.loads(stats) if isinstance(stats, str) else stats)
                    except Exception as e:
                        ui.show_stats({"error": str(e)})
                else:
                    ui.show_config_error(["API_KEY"])
            elif choice == "about":
                ui.show_about()
            else:
                pass  # Other menu choices handled by UI
    except ImportError:
        console.print("[red]Go UI not available. Use CLI mode: tng -m method -f file.py[/red]")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    method: Optional[str] = typer.Option(None, "-m", "--method", help="Method name to test"),
    file: Optional[str] = typer.Option(None, "-f", "--file", help="Python file path"),
    test_type: str = typer.Option(..., "-t", "--type", help="Test type: endpoint, job, mailer, model, service, middleware, dependency, lifespan, utility"),
    audit: bool = typer.Option(False, "--audit", help="Run audit mode instead of test generation"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
):
    if version:
        from tng_py import __version__
        console.print(f"tng-python {__version__}")
        raise typer.Exit()

    if ctx.invoked_subcommand is not None:
        return

    if method and file:
        if audit:
            audit_method(file, method, test_type, json_output)
        else:
            generate_test(file, method, test_type=test_type)
    elif file and not method:
        console.print("[yellow]Specify a method with -m[/yellow]")
    elif not file and not method:
        # Show help if no args
        console.print("Use [bold]tng --help[/bold] for usage")


def generate_test(file_path: str, method_name: str, class_name: Optional[str] = None, test_type: Optional[str] = None):

    config = load_config()

    if not config.get("API_KEY"):
        console.print("[red]No API key configured. Run: tng init[/red]")
        raise typer.Exit(1)

    if not tng_utils:
        console.print("[red]Rust module not loaded. Reinstall with: pip install tng-python[/red]")
        raise typer.Exit(1)

    # Check file exists
    path = Path(file_path)
    if not path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(1)

    additional_context = None

    console.print("[blue]🔍 Gathering enhanced context...[/blue]")

    # Build config for Rust (convert to lowercase keys for JSON)
    full_config = {
        "api_key": config.get("API_KEY"),
        "api_url": config.get("API_URL", "https://api.tng.sh"),
        "framework": config.get("FRAMEWORK", "generic"),
        "test_framework": config.get("TEST_FRAMEWORK", "pytest"),
        "mock_library": config.get("MOCK_LIBRARY", "pytest-mock"),
        "worker": config.get("WORKER", "none"),
        "mailer": config.get("MAILER", "none"),
        "orm": config.get("ORM", "none"),
        "fastapi_app_path": config.get("FASTAPI_APP_PATH", ""),
        "test_directory": config.get("TEST_DIRECTORY", "tests"),
        "test_type": test_type,
    }

    # Rust orchestrates: read file, parse AST, find examples, build payload, submit, poll
    console.print(f"[blue]Generating test for {method_name} in {file_path}...[/blue]")
    try:
        result_json = tng_utils.generate_test(
            str(path.absolute()),
            method_name,
            class_name,
            test_type,
            json.dumps(full_config)
        )

        # Save test file using save_file module (handles timestamp, ruff, etc.)
        from tng_py.save_file import save_test_file
        saved = save_test_file(result_json)

        if saved:
            console.print(f"[green]✓ Test saved to: {saved['file_path']}[/green]")
        else:
            console.print("[yellow]Failed to save test file[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def audit_method(file_path: str, method_name: str, test_type: str, json_output: bool = False):
    """Audit a method for potential issues and suggest improvements"""

    config = load_config()

    if not config.get("API_KEY"):
        if json_output:
            print(json.dumps({"type": "config_error", "message": "No API key configured"}))
        else:
            console.print("[red]No API key configured. Run: tng init[/red]")
        raise typer.Exit(1)

    if not tng_utils:
        if json_output:
            print(json.dumps({"type": "error", "message": "Rust module not loaded"}))
        else:
            console.print("[red]Rust module not loaded. Reinstall with: pip install tng-python[/red]")
        raise typer.Exit(1)

    # Check file exists
    path = Path(file_path)
    if not path.exists():
        if json_output:
            print(json.dumps({"type": "error", "message": f"File not found: {file_path}"}))
        else:
            console.print(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(1)

    # Build config for Rust
    full_config = {
        "api_key": config.get("API_KEY"),
        "api_url": config.get("API_URL", "https://api.tng.sh"),
        "framework": config.get("FRAMEWORK", "generic"),
        "test_framework": config.get("TEST_FRAMEWORK", "pytest"),
        "test_type": test_type,
    }

    if json_output:
        # Use JsonSession for structured JSON output
        from tng_py.ui.json_session import JsonSession

        session = JsonSession()
        session.start()

        def progress_handler(progress):
            progress.update("Preparing request...")

            try:
                # Initialize agent steps
                agent_steps = {
                    "context_agent_status": (1, "Context Builder"),
                    "style_agent_status": (2, "Style Analyzer"),
                    "logical_issue_status": (3, "Logic Analyzer"),
                    "behavior_expert_status": (4, "Logic Generator"),
                    "context_insights_status": (5, "Context Insights"),
                }

                for key, (step_idx, label) in agent_steps.items():
                    progress.update(f"{label}: Pending...", step_increment=True)

                # Call Rust audit function with callback
                result_json = tng_utils.run_audit(
                    str(path.absolute()),
                    method_name,
                    None,  # class_name
                    test_type,
                    json.dumps(full_config),
                    lambda msg, percent: _handle_progress_callback(msg, percent, progress, agent_steps)
                )

                result = json.loads(result_json)

                # Auto-exit for audit mode
                progress.complete("Audit complete!", auto_exit=True)

                return {
                    "message": "Audit complete!",
                    "result": result
                }

            except Exception as e:
                progress.error(f"Failed to audit: {str(e)}")
                return {"error": str(e)}

        try:
            audit_result = session.show_progress(f"Auditing {method_name}", progress_handler)
            if audit_result and audit_result.get("result"):
                session.show_audit_results(audit_result["result"])
        except Exception as e:
            session.display_error(str(e))
            raise typer.Exit(1)

    else:
        # Use rich console for human-readable output
        console.print("[blue]🔍 Auditing method...[/blue]")

        try:
            # Call audit function from Rust module
            result_json = tng_utils.run_audit(
                str(path.absolute()),
                method_name,
                None,  # class_name
                test_type,
                json.dumps(full_config),
                None  # No callback for console mode
            )

            result = json.loads(result_json)

            # Pretty print audit results
            console.print(f"\n[bold]Audit Results for {method_name}:[/bold]\n")

            if "issues" in result:
                console.print("[bold red]Issues:[/bold red]")
                for issue in result["issues"]:
                    console.print(f"  • {issue.get('message', 'Unknown issue')}")

            if "suggestions" in result:
                console.print("\n[bold yellow]Suggestions:[/bold yellow]")
                for suggestion in result["suggestions"]:
                    console.print(f"  • {suggestion}")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)


def _handle_progress_callback(msg, percent, progress, agent_steps):
    """Handle progress callback from Rust submit_and_poll"""
    try:
        if msg.strip().startswith("{"):
            info = json.loads(msg)

            for key, (step_idx, label) in agent_steps.items():
                item_data = info.get(key)

                if item_data is None:
                    status = "pending"
                    values = []
                elif isinstance(item_data, dict):
                    status = item_data.get("status", "pending")
                    values = item_data.get("values", [])
                else:
                    status = str(item_data)
                    values = []

                # Format message
                if status == "processing":
                    display_msg = f"{label}: Processing..."
                elif status == "completed":
                    display_msg = f"{label}: Completed"
                elif status == "failed":
                    display_msg = f"{label}: Failed"
                else:
                    display_msg = f"{label}: {status.capitalize()}..."

                # Add values if present
                if values and isinstance(values, list) and len(values) > 0:
                    clean_values = [str(v).replace('_', ' ').replace("'", "").replace(":", "").strip() for v in values]
                    display_vals = clean_values[:2]
                    val_str = ", ".join(display_vals)
                    if len(clean_values) > 2:
                        val_str += ", ..."
                    display_msg = f"{display_msg} ({val_str})"

                # Update progress with explicit step
                p = percent if key == "behavior_expert_status" else None
                progress.update(display_msg, percent=p, explicit_step=step_idx, step_increment=False)
        else:
            # Non-JSON message
            progress.update(msg, percent=percent)
    except Exception:
        # Fallback for any parsing errors
        progress.update(msg, percent=percent)


if __name__ == "__main__":
    app()
