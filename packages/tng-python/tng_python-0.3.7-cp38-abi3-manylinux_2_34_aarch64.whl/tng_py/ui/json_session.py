"""JSON Session - Event emitter for plugin integration"""

import json


class JsonSession:

    def __init__(self):
        self.running = False

    def start(self):
        """Mark session as started"""
        self.running = True
        self.emit_event("started", {"message": "TNG JSON Session Started"})

    def stop(self):
        """Mark session as stopped"""
        self.running = False
        self.emit_event("stopped", {"message": "TNG JSON Session Stopped"})

    def is_running(self):
        """Check if session is running"""
        return self.running

    def show_progress(self, title, callback):
        """
        Show progress with JSON events

        Args:
            title: Progress title
            callback: Function that receives JsonProgressReporter and returns result dict

        Returns:
            Result from callback
        """
        self.emit_event("progress_start", {"title": title})

        reporter = JsonProgressReporter()

        try:
            result = callback(reporter)

            if result and result.get("error"):
                # Error already handled by reporter
                pass
            else:
                self.emit_event("progress_complete", {
                    "message": result.get("message", "Done") if result else "Done",
                    "result": result
                })

            return result
        except Exception as e:
            self.emit_event("error", {"message": str(e)})
            raise

    def show_audit_results(self, audit_result):
        """Emit audit results as JSON event"""
        self.emit_event("result", audit_result)

    def show_test_results(self, title, passed, failed, errors, total, results=None):
        """Emit test results as JSON event"""
        if results is None:
            results = []

        self.emit_event("test_results", {
            "title": title,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "total": total,
            "results": results
        })

    def show_auth_error(self, message="Authentication failed"):
        """Emit authentication error"""
        self.emit_event("auth_error", {"message": message})

    def show_config_error(self, missing):
        """Emit configuration error"""
        self.emit_event("config_error", {"missing": missing})

    def show_config_missing(self, missing_items):
        """Emit config missing event"""
        self.emit_event("config_missing", {"missing": missing_items})

    def show_system_status(self, status):
        """Emit system status"""
        self.emit_event("system_status", status)

    def show_no_items(self, item_type):
        """Emit no items found event"""
        self.emit_event("no_items", {"type": item_type})

    def display_error(self, message):
        """Emit error message"""
        self.emit_event("error", {"message": self._strip_colors(message)})

    def display_warning(self, message):
        """Emit warning message"""
        self.emit_event("warning", {"message": self._strip_colors(message)})

    def display_info(self, message):
        """Emit info message"""
        self.emit_event("info", {"message": self._strip_colors(message)})

    def display_list(self, title, items):
        """Emit list display"""
        self.emit_event("list", {
            "title": self._strip_colors(title),
            "items": items
        })

    def _strip_colors(self, text):
        """Remove ANSI color codes from text"""
        import re
        return re.sub(r'\x1b\[\d+(;\d+)*m', '', str(text))

    def emit_event(self, event_type, data=None):
        """
        Emit a JSON event to stdout

        Args:
            event_type: Type of event
            data: Optional event data dict
        """
        event = {"type": event_type}
        if data:
            event.update(data)
        print(json.dumps(event))


class JsonProgressReporter:
    """Progress reporter that emits JSON events"""

    def __init__(self):
        self.step = 0

    def update(self, message, percent=None, step_increment=True, explicit_step=None, **options):
        """
        Emit progress update event

        Args:
            message: Progress message
            percent: Optional percentage (0-100)
            step_increment: Whether to increment step counter
            explicit_step: Optional explicit step index
            **options: Additional options (ignored for compatibility)
        """
        step_idx = explicit_step if explicit_step is not None else self.step

        payload = {
            "type": "progress_update",
            "message": message,
            "step": step_idx
        }

        if percent is not None:
            payload["percent"] = percent

        print(json.dumps(payload))

        if step_increment and explicit_step is None:
            self.step += 1

    def error(self, message):
        """
        Emit error event

        Args:
            message: Error message
        """
        print(json.dumps({"type": "error", "message": message}))

    def complete(self, message, auto_exit=False):
        """
        Emit completion event

        Args:
            message: Completion message
            auto_exit: Whether to auto-exit (for audit mode)
        """
        payload = {"type": "complete", "message": message}
        if auto_exit:
            payload["auto_exit"] = True
        print(json.dumps(payload))
