"""Generate Tests UI - Interactive test generation flow using Go UI"""

import json
from pathlib import Path

from .go_ui_session import GoUISession


class GenerateTestsUI:
    """UI for selecting files and methods and generating tests"""

    def __init__(self, cli_mode=False):
        self.cli_mode = cli_mode
        if not cli_mode:
            self.go_ui_session = GoUISession()
            self.go_ui_session.start()

    def show(self, is_audit=False):
        """Main test generation flow"""
        while True:
            result = self._show_file_selection(is_audit=is_audit)
            if result == "back":
                return "back"
            elif result == "exit":
                return "exit"
            elif result == "main_menu":
                return "back"
            elif result is None:
                return "exit"

    def _show_file_selection(self, is_audit=False):
        """Show file selection interface"""
        python_files = self._get_user_python_files()

        if not python_files:
            self.go_ui_session.show_no_items("Python files")
            return "back"

        # Build items with relative path as display name (to distinguish auth.py from schemas/auth.py)
        cwd = Path.cwd()
        items = []
        file_map = {}  # Map display name to full path

        for file in python_files:
            try:
                rel_path = str(file.relative_to(cwd))
            except ValueError:
                rel_path = str(file)

            items.append({"name": rel_path, "path": str(file.parent)})
            file_map[rel_path] = str(file)

        title = "Select Python File to Audit" if is_audit else "Select Python File"
        selected_name = self.go_ui_session.show_list_view(title, items)

        if selected_name == "back":
            return "back"
        if not selected_name or selected_name == "exit":
            return "exit"

        # Look up the full path from our map
        selected_file = file_map.get(selected_name)

        if not selected_file:
            return "back"

        return self._show_methods_for_file(selected_file, is_audit=is_audit)

    def _show_methods_for_file(self, file_path, is_audit=False):
        """Show methods for a specific file"""
        methods = self._get_file_methods(file_path)

        if not methods:
            self.go_ui_session.show_no_items("methods")
            return self._show_file_selection(is_audit=is_audit)

        file_name = Path(file_path).name
        items = [
            {"name": method["display"], "path": f"Method in {file_name}"}
            for method in methods
        ]

        title = f"Select Method to Audit for {file_name}" if is_audit else f"Select Method for {file_name}"
        selected_display = self.go_ui_session.show_list_view(
            title, items
        )

        if selected_display == "back":
            return self._show_file_selection(is_audit=is_audit)

        if selected_display:
            # Find the method object that matches the selected display name
            selected_method = None
            for method in methods:
                if method["display"] == selected_display:
                    selected_method = method
                    break

            if selected_method:
                test_type = self.go_ui_session.show_python_test_menu()
                if test_type == "back":
                    return self._show_methods_for_file(file_path, is_audit=is_audit)

                final_type = None if test_type == "auto" else test_type

                result = self._generate_tests_for_method(file_path, selected_method, test_type=final_type, is_audit=is_audit)

                if is_audit:
                    # In streaming mode, _handle_audit_flow already showed the results.
                    # We don't want to show the 'old' static results view afterwards.
                    return self._show_methods_for_file(file_path, is_audit=is_audit)

                if result and result.get("file_path") and not result.get("error"):
                    self._show_post_generation_menu(result)
                    return self._show_file_selection(is_audit=is_audit)
                elif result and result.get("error"):
                    return None
            return self._show_methods_for_file(file_path, is_audit=is_audit)
        else:
            return self._show_methods_for_file(file_path, is_audit=is_audit)

    def _generate_tests_for_method(self, file_path, selected_method, test_type=None, is_audit=False):
        """Generate tests or audit selected method using Go UI progress"""
        if is_audit and not self.cli_mode:
            return self._handle_audit_flow(file_path, selected_method, test_type)

        file_name = Path(file_path).name
        action_name = "Auditing" if is_audit else "Generating test for"

        # Create display name: class_name#method_name or filename#method_name
        if selected_method.get("class"):
            display_name = f"{selected_method['class']}#{selected_method['name']}"
        else:
            display_name = f"{file_name}#{selected_method['name']}"

        def progress_handler(progress):
            progress.update("Preparing request...")

            try:
                # Load config from local tng_config.py
                config = self._load_config()
                if not config.get("API_KEY"):
                    progress.error("No API key configured. Run: tng init")
                    return {"error": "No API key", "result": None}

                base_url = config.get("API_URL", "https://app.tng.sh/")
                api_key = config.get("API_KEY")

                # Build full config for Rust

                # Enhanced context gathering - set ENHANCED_CONTEXT = False in config to disable
                use_enhanced = config.get("ENHANCED_CONTEXT", True)
                additional_context = None
                context_time_ms = 0

                if use_enhanced:
                    progress.update("Gathering enhanced context (Rust)...", step_increment=False)

                full_config = {
                    "api_key": api_key,
                    "api_url": base_url,
                    "framework": config.get("FRAMEWORK", "generic"),
                    "test_framework": config.get("TEST_FRAMEWORK", "pytest"),
                    "mock_library": config.get("MOCK_LIBRARY", "pytest-mock"),
                    "worker": config.get("WORKER", "none"),
                    "mailer": config.get("MAILER", "none"),
                    "orm": config.get("ORM", "none"),
                    "fastapi_app_path": config.get("FASTAPI_APP_PATH", ""),
                    "test_directory": config.get("TEST_DIRECTORY", "tests"),
                    "test_type": test_type or "endpoint",
                    # A/B testing metadata
                    "ab_test": {
                        "enhanced_context": use_enhanced,
                        "context_time_ms": 0,
                    },
                    "enhanced_context": use_enhanced,
                }

                progress.update("Submitting to API...")

                import tng_utils


                # Structural steps (Steps 2-5)
                progress.update("Context Builder: Pending...", step_increment=True) # Step 2
                progress.update("Style Analyzer: Pending...", step_increment=True)   # Step 3
                progress.update("Logic Analyzer: Pending...", step_increment=True)   # Step 4
                progress.update("Logic Generator: Pending...", step_increment=True)  # Step 5

                # Mapping from JSON key to (Step Index, Label)
                agent_steps = {
                    "context_agent_status": (2, "Context Builder"),
                    "style_agent_status": (3, "Style Analyzer"),
                    "logical_issue_status": (4, "Logic Analyzer"),
                    "behavior_expert_status": (5, "Logic Generator"),
                }

                def poll_callback(message, percent=None):
                    try:
                        if not message or not isinstance(message, str):
                            return

                        msg_str = message.strip()
                        if not msg_str:
                            return

                        # Try to parse as JSON (structured data)
                        if msg_str.startswith("{") and msg_str.endswith("}"):
                            try:
                                info = json.loads(msg_str)
                                if not isinstance(info, dict):
                                    progress.update(msg_str, percent=percent, step_increment=False)
                                    return

                                found_known_step = False
                                for key, (step_idx, label) in agent_steps.items():
                                    if key not in info:
                                        continue

                                    found_known_step = True
                                    item_data = info[key]

                                    # Normalize status and values
                                    if isinstance(item_data, dict):
                                        status = str(item_data.get("status", "pending")).lower()
                                        values = item_data.get("values", [])
                                    else:
                                        status = str(item_data).lower()
                                        values = []

                                    # Build display message
                                    if status == "processing":
                                        display_msg = f"{label}: Processing..."
                                    elif status == "completed":
                                        display_msg = f"{label}: Completed"
                                    elif status == "failed":
                                        display_msg = f"{label}: Failed"
                                    elif status == "pending":
                                        display_msg = f"{label}: Pending..."
                                    else:
                                        display_msg = f"{label}: {status.title()}..."

                                    # Add granular findings if available (e.g. "Logic Analyzer: Completed (Security, Validation)")
                                    if values and isinstance(values, list):
                                        # Clean up entries (remove underscores, strip whitespace)
                                        clean_vals = [str(v).replace('_', ' ').replace("'", "").replace(":", "").strip() for v in values if v]
                                        if clean_vals:
                                            # Limit to 3 findings to avoid UI clutter
                                            val_summary = ", ".join(clean_vals[:3])
                                            if len(clean_vals) > 3:
                                                val_summary += "..."
                                            display_msg = f"{display_msg} ({val_summary})"

                                    # Update specific step in the UI
                                    progress.update(display_msg, percent=percent, explicit_step=step_idx)

                                if not found_known_step:
                                    # Valid JSON but no keys we recognize, show as fallback
                                    progress.update(msg_str, percent=percent, step_increment=False)

                            except (json.JSONDecodeError, TypeError):
                                progress.update(msg_str, percent=percent, step_increment=False)
                        else:
                            # Simple string message (fallback for non-JSON content)
                            progress.update(msg_str, percent=percent, step_increment=False)

                    except Exception:
                        # Final safety net - do not crash the interactive session
                        pass

                if is_audit:
                    result_json = tng_utils.run_audit(
                        file_path,
                        selected_method["name"],
                        selected_method.get("class"),
                        test_type or "endpoint",
                        json.dumps(full_config),
                        poll_callback
                    )
                else:
                    result_json = tng_utils.generate_test(
                        file_path,
                        selected_method["name"],
                        selected_method.get("class"),
                        test_type or "endpoint",
                        json.dumps(full_config),
                        poll_callback
                    )

                if is_audit:
                    progress.complete("Audit ready!", auto_exit=False)
                    return {
                        "message": "Audit complete!",
                        "result": json.loads(result_json)
                    }

                progress.update("Tests generated successfully!")

                # Save the generated test file
                from tng_py.save_file import save_test_file
                file_info = save_test_file(result_json)

                return {
                    "message": "Tests generated successfully!",
                    "result": json.loads(result_json),
                    "file_info": file_info,
                    "file_path": file_info.get("file_path") if file_info else None,
                }

            except Exception as e:
                progress.error(f"Failed to generate tests: {str(e)}")
                return {"error": str(e), "result": None}

        if self.cli_mode:
            class MockProgress:
                def update(self, message, percent=None):
                    print(f"🔄 {message}")
                def error(self, message):
                    print(f"❌ {message}")

            mock_progress = MockProgress()
            try:
                return progress_handler(mock_progress)
            except Exception as e:
                mock_progress.error(str(e))
                return {"error": str(e), "result": None}
        else:
            result = self.go_ui_session.show_progress(
                f"{action_name} {display_name}", progress_handler
            )

            if is_audit and result and result.get("result"):
                return result

            if result and result.get("file_info"):
                return result
            return None

    def _handle_audit_flow(self, file_path, selected_method, test_type=None):
        """Handle the specialized streaming audit flow"""
        config = self._load_config()
        if not config.get("API_KEY"):
            print("No API key configured. Run: tng init")
            return None

        base_url = config.get("API_URL", "https://app.tng.sh/")
        api_key = config.get("API_KEY")
        use_enhanced = config.get("ENHANCED_CONTEXT", True)

        full_config = {
            "api_key": api_key,
            "api_url": base_url,
            "framework": config.get("FRAMEWORK", "generic"),
            "test_framework": config.get("TEST_FRAMEWORK", "pytest"),
            "mock_library": config.get("MOCK_LIBRARY", "pytest-mock"),
            "worker": config.get("WORKER", "none"),
            "mailer": config.get("MAILER", "none"),
            "orm": config.get("ORM", "none"),
            "fastapi_app_path": config.get("FASTAPI_APP_PATH", ""),
            "test_directory": config.get("TEST_DIRECTORY", "tests"),
            "test_type": test_type or "endpoint",
            "enhanced_context": use_enhanced,
        }

        # Prepare local source for the UI (instant preview)
        # Use the source already extracted by the outline analyzer if available
        source_code_ui = selected_method.get("source_code") or ""

        if not source_code_ui:
            try:
                import tng_utils
                full_source = Path(file_path).read_text()
                source_result = tng_utils.find_method_source(
                    full_source,
                    selected_method["name"],
                    selected_method.get("class")
                )
                if source_result:
                    source_code_ui, _ = source_result
            except Exception:
                pass

        # If still empty, use full source as a last resort (Go UI will handle it)
        if not source_code_ui:
            try:
                source_code_ui = Path(file_path).read_text()
            except Exception:
                pass

        # Start the specialized streaming UI
        streaming_ui = self.go_ui_session.show_streaming_audit_results(
            selected_method["name"],
            selected_method.get("class"),
            source_code_ui
        )

        if not streaming_ui:
            return None

        try:
            import tng_utils

            # Callback for the Rust core to feed the Go UI
            def stream_callback(message, percent=None):
                if message and message.strip().startswith("{"):
                    streaming_ui.write(message)

            result_json = tng_utils.run_audit(
                str(Path(file_path).absolute()),
                selected_method["name"],
                selected_method.get("class"),
                test_type or "endpoint",
                json.dumps(full_config),
                stream_callback
            )

            # Wait for user to exit the UI
            choice = streaming_ui.wait()

            return {
                "message": "Audit complete",
                "result": json.loads(result_json),
                "choice": choice
            }

        except Exception as e:
            print(f"Audit failed: {e}")
            return None

    def _show_post_generation_menu(self, result):
        file_info = result.get("file_info", {})
        file_path = file_info.get("file_path") or file_info.get("absolute_path")
        run_command = file_info.get("run_command", f"pytest {file_path}")

        while True:
            choice = self.go_ui_session.show_post_generation_menu(file_path, run_command)

            if choice == "run_tests":
                self._run_and_show_test_results(run_command)
            elif choice == "copy_command":
                self._copy_command_and_show_success(run_command)
            elif choice == "back":
                break
            else:
                break

    def _copy_command_and_show_success(self, command):
        """Copy command to clipboard and show success"""
        import subprocess
        import sys

        try:
            if sys.platform == "darwin":
                subprocess.run(["pbcopy"], input=command.encode("utf-8"), check=True)
                self.go_ui_session.show_clipboard_success(command)
            elif sys.platform.startswith("linux"):
                try:
                    subprocess.run(
                        ["xclip", "-selection", "clipboard"],
                        input=command.encode("utf-8"),
                        check=True,
                    )
                    self.go_ui_session.show_clipboard_success(command)
                except FileNotFoundError:
                    print(f"\n📋 Copy this command:\n{command}\n")
                    input("Press Enter to continue...")
            else:
                print(f"\n📋 Copy this command:\n{command}\n")
                input("Press Enter to continue...")
        except Exception:
            print(f"\n📋 Copy this command:\n{command}\n")
            input("Press Enter to continue...")

    def _run_and_show_test_results(self, command):
        """Run tests and show results using Go UI"""
        import subprocess

        def spinner_handler():
            output = subprocess.run(command, shell=True, capture_output=True, text=True)
            return {
                "success": True,
                "message": "Tests completed",
                "output": output.stdout + output.stderr,
                "exit_code": output.returncode,
            }

        test_output = self.go_ui_session.show_spinner("Running tests...", spinner_handler)

        passed, failed, errors, total = self._parse_test_output(
            test_output.get("output", ""), test_output.get("exit_code", 1)
        )

        self.go_ui_session.show_test_results("Test Results", passed, failed, errors, total, [])

    def _parse_test_output(self, output, exit_code):
        """Parse pytest output to extract test counts"""
        import re

        passed = failed = errors = 0

        passed_match = re.search(r"(\d+) passed", output)
        failed_match = re.search(r"(\d+) failed", output)
        error_match = re.search(r"(\d+) error", output)

        if passed_match:
            passed = int(passed_match.group(1))
        if failed_match:
            failed = int(failed_match.group(1))
        if error_match:
            errors = int(error_match.group(1))

        total = passed + failed + errors

        if total == 0:
            if exit_code == 0:
                passed = 1
                total = 1
            else:
                failed = 1
                total = 1

        return passed, failed, errors, total

    def _get_user_python_files(self):
        """Get Python files that belong to the user's project (not dependencies)"""
        current_dir = Path.cwd()
        python_files = []

        exclude_dirs = {
            "venv", "env", ".venv", ".env",
            "site-packages", "dist-packages",
            "__pycache__", ".git", ".pytest_cache",
            "node_modules", "target", "build", "dist",
            ".mypy_cache", ".tox", "htmlcov",
            "tests", "test", "spec", "migrations",
        }

        for py_file in current_dir.rglob("*.py"):
            if any(excluded in py_file.parts for excluded in exclude_dirs):
                continue

            if py_file.stat().st_size < 10:
                continue

            python_files.append(py_file)

        return sorted(python_files, key=lambda x: x.name)

    def _get_file_methods(self, file_path):
        """

        Returns a list of methods with:
        - name: method/function name
        - class: class name (or None for module-level functions)
        - display: formatted display name
        - type: method type (method, classmethod, staticmethod, function)
        - async: whether it's an async function
        """
        try:
            import tng_utils

            # Call Rust analyzer
            outline_json = tng_utils.get_file_outline(file_path)
            outline = json.loads(outline_json)

            methods = []
            seen = set()

            # Process classes and their methods
            for class_info in outline.get("classes", []):
                class_name = class_info["name"]
                for method_info in class_info.get("methods", []):
                    method_name = method_info["name"] if isinstance(method_info, dict) else method_info

                    # Skip private methods (but allow __init__, __call__, etc.)
                    if method_name.startswith("_") and not method_name.startswith("__"):
                        continue

                    display = f"{class_name}.{method_name}"
                    key = (class_name, method_name)

                    if key not in seen:
                        seen.add(key)
                        methods.append({
                            "name": method_name,
                            "class": class_name,
                            "display": display,
                            "type": "method",
                            "async": False,
                            "source_code": method_info.get("source_code") if isinstance(method_info, dict) else None
                        })

            # Process module-level functions
            for func_info in outline.get("functions", []):
                func_name = func_info["name"]

                # Skip private functions (but allow __main__, etc.)
                if func_name.startswith("_") and not func_name.startswith("__"):
                    continue

                key = (None, func_name)
                if key not in seen:
                    seen.add(key)
                    methods.append({
                        "name": func_name,
                        "class": None,
                        "display": func_name,
                        "type": "function",
                        "async": False,
                        "source_code": func_info.get("source_code")
                    })

            return methods

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []

    def _load_config(self):
        """Load config from local tng_config.py"""
        config_file = Path.cwd() / "tng_config.py"

        if not config_file.exists():
            return {}

        config = {}
        try:
            exec(config_file.read_text(), config)
            return {k: v for k, v in config.items() if k.isupper()}
        except Exception:
            return {}
