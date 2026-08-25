from concurrent.futures import ThreadPoolExecutor

from gi.repository import GLib


class Controller:
    """
    Coordinates the GUI with the TV and OpenLP backends.

    Backend operations are performed in worker threads so that GTK's
    main thread is never blocked by network or filesystem operations.
    """

    def __init__(
        self,
        backend,
        status_callback,
        operation_callback,
        openlp_backend=None,
    ):
        self.backend = backend
        self.openlp_backend = openlp_backend

        self.status_callback = status_callback
        self.operation_callback = operation_callback

        self.executor = ThreadPoolExecutor(max_workers=3)

    # ------------------------------------------------------------------
    # TV status
    # ------------------------------------------------------------------

    def refresh_status(self):
        self.executor.submit(self._do_refresh_status)

    def _do_refresh_status(self):
        try:
            status = self.backend.get_status()

            GLib.idle_add(
                self.status_callback,
                status,
            )

        except Exception as exc:
            GLib.idle_add(
                self._status_error,
                str(exc),
            )

    def _status_error(self, message):
        self.status_callback(
            None,
            message,
        )

        return False

    # ------------------------------------------------------------------
    # TV operations
    # ------------------------------------------------------------------

    def start(self):
        self.executor.submit(
            self._run_tv_operation,
            "start",
        )

    def restart_display(self):
        self.executor.submit(
            self._run_tv_operation,
            "restart_display",
        )

    def reboot(self):
        self.executor.submit(
            self._run_tv_operation,
            "reboot",
        )

    def shutdown(self):
        self.executor.submit(
            self._run_tv_operation,
            "shutdown",
        )

    def _run_tv_operation(self, operation):
        try:
            method = getattr(
                self.backend,
                operation,
            )

            message = method()

            GLib.idle_add(
                self._operation_finished,
                True,
                message,
            )

        except Exception as exc:
            GLib.idle_add(
                self._operation_finished,
                False,
                str(exc),
            )

    # ------------------------------------------------------------------
    # OpenLP operations
    # ------------------------------------------------------------------

    def fix_openlp_service_problem(self):
        if self.openlp_backend is None:
            GLib.idle_add(
                self._operation_finished,
                False,
                "OpenLP repair is not available.",
            )
            return

        self.executor.submit(
            self._run_openlp_operation,
        )

    def _run_openlp_operation(self):
        try:
            message = (
                self.openlp_backend.fix_service_problem()
            )

            GLib.idle_add(
                self._operation_finished,
                True,
                message,
            )

        except Exception as exc:
            GLib.idle_add(
                self._operation_finished,
                False,
                str(exc),
            )

    # ------------------------------------------------------------------
    # Completion
    # ------------------------------------------------------------------

    def _operation_finished(self, success, message):
        self.operation_callback(
            success,
            message,
        )

        return False

    def shutdown_controller(self):
        self.executor.shutdown(
            wait=False
        )
