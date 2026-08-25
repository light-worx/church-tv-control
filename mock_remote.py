import time
import threading

from models import TVStatus
from remote import RemoteBackend


class MockRemoteBackend(RemoteBackend):
    """
    Simulated Church TV PC.

    This allows the complete GUI to be developed and tested
    without access to the real TV computer.
    """

    def __init__(self):
        self._lock = threading.Lock()

        self.tv_online = True
        self.church_tv_running = True
        self.openlp_reachable = True

    def get_status(self) -> TVStatus:
        # Simulate a small amount of network latency.
        time.sleep(0.5)

        with self._lock:
            return TVStatus(
                tv_online=self.tv_online,
                church_tv_running=self.church_tv_running,
                openlp_reachable=self.openlp_reachable,
            )

    def start(self) -> str:
        with self._lock:
            self.tv_online = True
            self.church_tv_running = True
        return "TV computer started successfully."

    def get_screenshot(self) -> bytes:
        # The GTK mock does not use the preview.
        return b""

    def restart_display(self) -> str:
        with self._lock:
            if not self.tv_online:
                raise RuntimeError("TV computer is not reachable.")

            self.church_tv_running = False

        # Simulate stopping/restarting church-tv.sh.
        time.sleep(2)

        with self._lock:
            if not self.tv_online:
                raise RuntimeError(
                    "The TV computer became unavailable while restarting "
                    "the display."
                )

            self.church_tv_running = True

        return "Church TV display restarted successfully."

    def reboot(self) -> str:
        with self._lock:
            if not self.tv_online:
                raise RuntimeError("TV computer is not reachable.")

            self.tv_online = False
            self.church_tv_running = False
            self.openlp_reachable = False

        # Simulate a reboot.
        time.sleep(5)

        with self._lock:
            self.tv_online = True
            self.church_tv_running = True

        # OpenLP is independent of the TV PC, so it can come back
        # according to the simulated OpenLP setting.
        return "TV computer rebooted successfully."

    def shutdown(self) -> str:
        with self._lock:
            if not self.tv_online:
                raise RuntimeError("TV computer is not reachable.")

            self.tv_online = False
            self.church_tv_running = False
            self.openlp_reachable = False

        # Simulate the shutdown command completing.
        time.sleep(2)

        return "TV computer has been shut down."

    # ------------------------------------------------------------------
    # Simulation controls
    # ------------------------------------------------------------------

    def set_tv_online(self, online: bool):
        with self._lock:
            self.tv_online = online

            if not online:
                self.church_tv_running = False

    def set_church_tv_running(self, running: bool):
        with self._lock:
            if self.tv_online:
                self.church_tv_running = running

    def set_openlp_reachable(self, reachable: bool):
        with self._lock:
            self.openlp_reachable = reachable