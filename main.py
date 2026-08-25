import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

from controller import Controller
from gui import ChurchTVWindow
from remote import SSHRemoteBackend
from openlp import OpenLPBackend


def main():

    # --------------------------------------------------------------
    # Real backends
    #
    # TV control is performed remotely over SSH.
    # OpenLP repair is handled by the local OpenLP backend.
    # --------------------------------------------------------------

    tv_backend = SSHRemoteBackend()
    openlp_backend = OpenLPBackend()

    window = None

    def status_callback(status, error_message=None):
        if status is not None:
            return window.update_status(status)

        return window.status_error(
            status,
            error_message,
        )

    def operation_callback(success, message):
        return window.operation_finished(
            success,
            message,
        )

    controller = Controller(
        backend=tv_backend,
        status_callback=status_callback,
        operation_callback=operation_callback,
        openlp_backend=openlp_backend,
    )

    window = ChurchTVWindow(
        controller=controller,
    )

    window.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()
