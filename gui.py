import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib

from models import TVStatus
from config import APP_TITLE, STATUS_REFRESH_SECONDS


class StatusRow:
    """
    A single status indicator consisting of:
    indicator + label
    """

    def __init__(self, title):
        self.title = title

        self.box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
        )

        self.indicator = Gtk.Label()
        self.indicator.set_width_chars(2)

        self.label = Gtk.Label()
        self.label.set_xalign(0)

        self.box.pack_start(
            self.indicator,
            False,
            False,
            0,
        )

        self.box.pack_start(
            self.label,
            True,
            True,
            0,
        )

        self.set_status(None)

    def set_status(self, value):
        if value is True:
            self.indicator.set_markup(
                '<span foreground="#2e8b57">●</span>'
            )
            self.label.set_text(
                f"{self.title}: OK"
            )

        elif value is False:
            self.indicator.set_markup(
                '<span foreground="#c0392b">●</span>'
            )
            self.label.set_text(
                f"{self.title}: Not available"
            )

        else:
            self.indicator.set_markup(
                '<span foreground="#888888">●</span>'
            )
            self.label.set_text(
                f"{self.title}: Checking…"
            )


class ChurchTVWindow(Gtk.Window):

    def __init__(self, controller):
        super().__init__(title=APP_TITLE)

        self.controller = controller
        self.operation_in_progress = False

        self.set_border_width(24)
        self.set_default_size(520, 600)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.connect(
            "destroy",
            self.on_destroy,
        )

        self.build_ui()

        self.refresh_status()

        GLib.timeout_add_seconds(
            STATUS_REFRESH_SECONDS,
            self.periodic_status_refresh,
        )

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def build_ui(self):

        main = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=18,
        )

        self.add(main)

        title = Gtk.Label()

        title.set_markup(
            "<span size='xx-large' weight='bold'>"
            "CHURCH TV CONTROL"
            "</span>"
        )

        main.pack_start(
            title,
            False,
            False,
            0,
        )

        subtitle = Gtk.Label(
            label="Church TV remote control"
        )

        subtitle.get_style_context().add_class(
            "dim-label"
        )

        main.pack_start(
            subtitle,
            False,
            False,
            0,
        )

        # --------------------------------------------------------------
        # Status
        # --------------------------------------------------------------

        status_frame = Gtk.Frame(
            label="Status"
        )

        status_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
        )

        status_box.set_border_width(16)

        status_frame.add(status_box)

        self.tv_status = StatusRow(
            "TV Computer"
        )

        self.display_status = StatusRow(
            "Church TV Display"
        )

        self.openlp_status = StatusRow(
            "OpenLP Stage View"
        )

        status_box.pack_start(
            self.tv_status.box,
            False,
            False,
            0,
        )

        status_box.pack_start(
            self.display_status.box,
            False,
            False,
            0,
        )

        status_box.pack_start(
            self.openlp_status.box,
            False,
            False,
            0,
        )

        main.pack_start(
            status_frame,
            False,
            False,
            0,
        )

        # --------------------------------------------------------------
        # TV actions
        # --------------------------------------------------------------

        actions_frame = Gtk.Frame(
            label="TV Control"
        )

        actions_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
        )

        actions_box.set_border_width(16)

        self.start_button = Gtk.Button(
            label="Start TV"
        )

        self.start_button.set_size_request(-1, 48)

        self.start_button.connect(
            "clicked",
            self.on_start,
        )

        actions_box.pack_start(
            self.start_button,
            False,
            False,
            0,
        )

        self.shutdown_button = Gtk.Button(
            label="Shut Down TV"
        )

        self.shutdown_button.set_size_request(-1, 48)

        self.shutdown_button.connect(
            "clicked",
            self.on_shutdown,
        )

        actions_box.pack_start(
            self.shutdown_button,
            False,
            False,
            0,
        )

        actions_frame.add(actions_box)

        main.pack_start(
            actions_frame,
            False,
            False,
            0,
        )

        # --------------------------------------------------------------
        # OpenLP actions
        # --------------------------------------------------------------

        openlp_frame = Gtk.Frame(
            label="OpenLP"
        )

        openlp_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
        )

        openlp_box.set_border_width(16)

        openlp_frame.add(openlp_box)

        self.openlp_fix_button = Gtk.Button(
            label="Fix OpenLP Service Problem"
        )

        self.openlp_fix_button.set_size_request(
            -1,
            48,
        )

        self.openlp_fix_button.connect(
            "clicked",
            self.on_fix_openlp,
        )

        openlp_box.pack_start(
            self.openlp_fix_button,
            False,
            False,
            0,
        )

        main.pack_start(
            openlp_frame,
            False,
            False,
            0,
        )

        # --------------------------------------------------------------
        # Feedback
        # --------------------------------------------------------------

        self.feedback_label = Gtk.Label(
            label="Checking TV computer…"
        )

        self.feedback_label.set_xalign(0)
        self.feedback_label.set_line_wrap(True)

        main.pack_start(
            self.feedback_label,
            False,
            False,
            0,
        )

        self.last_checked_label = Gtk.Label(
            label="Last checked: —"
        )

        self.last_checked_label.get_style_context().add_class(
            "dim-label"
        )

        main.pack_start(
            self.last_checked_label,
            False,
            False,
            0,
        )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def refresh_status(self):

        if not self.operation_in_progress:
            self.controller.refresh_status()

    def periodic_status_refresh(self):

        self.refresh_status()

        return True

    def update_status(self, status: TVStatus):

        self.tv_status.set_status(
            status.tv_online
        )

        self.display_status.set_status(
            status.church_tv_running
        )

        self.openlp_status.set_status(
            status.openlp_reachable
        )

        if status.all_ok:
            self.set_feedback(
                "Church TV is running normally."
            )

        elif not status.tv_online:
            self.set_feedback(
                "Unable to contact the Church TV computer."
            )

        elif not status.church_tv_running:
            self.set_feedback(
                "The Church TV display is not running."
            )

        elif not status.openlp_reachable:
            self.set_feedback(
                "OpenLP Stage View is not reachable."
            )

        else:
            self.set_feedback(
                "Status updated."
            )

        from datetime import datetime

        self.last_checked_label.set_text(
            "Last checked: "
            + datetime.now().strftime("%H:%M:%S")
        )

        self.start_button.set_visible(
            not status.tv_online
        )
        self.shutdown_button.set_visible(
            status.tv_online
        )

        return False

    def status_error(
        self,
        status,
        error_message=None,
    ):

        self.tv_status.set_status(False)
        self.display_status.set_status(False)
        self.openlp_status.set_status(False)

        if error_message:
            self.set_feedback(
                "Unable to check the TV computer: "
                + error_message
            )
        else:
            self.set_feedback(
                "Unable to check the TV computer."
            )

        from datetime import datetime

        self.last_checked_label.set_text(
            "Last checked: "
            + datetime.now().strftime("%H:%M:%S")
        )

        return False

    # ------------------------------------------------------------------
    # TV operations
    # ------------------------------------------------------------------

    def on_start(self, button):

        if self.operation_in_progress:
            return

        self.start_operation(
            "Starting TV computer…"
        )

        self.controller.start()

    def on_shutdown(self, button):

        if self.operation_in_progress:
            return

        if not self.confirm(
            "Shut Down TV?",
            "This will turn off the remote TV computer. "
            "The TV display will stop until the computer "
            "is started again.",
        ):
            return

        self.start_operation(
            "Shutting down TV computer…"
        )

        self.controller.shutdown()

    # ------------------------------------------------------------------
    # OpenLP operations
    # ------------------------------------------------------------------

    def on_fix_openlp(self, button):

        if self.operation_in_progress:
            return

        if not self.confirm(
            "Fix OpenLP Service Problem?",
            "This will repair the OpenLP service-file "
            "problem by clearing OpenLP's thumbnail cache. "
            "Your service files and songs will not be deleted.",
        ):
            return

        self.start_operation(
            "Fixing OpenLP service problem…"
        )

        self.controller.fix_openlp_service_problem()

    # ------------------------------------------------------------------
    # Operation state
    # ------------------------------------------------------------------

    def start_operation(self, message):

        self.operation_in_progress = True

        self.start_button.set_sensitive(False)
        self.shutdown_button.set_sensitive(False)
        self.openlp_fix_button.set_sensitive(False)

        self.set_feedback(message)

    def operation_finished(
        self,
        success,
        message,
    ):

        self.operation_in_progress = False

        self.start_button.set_sensitive(True)
        self.shutdown_button.set_sensitive(True)
        self.openlp_fix_button.set_sensitive(True)

        if success:
            self.set_feedback(message)
        else:
            self.set_feedback(
                "Operation failed: "
                + message
            )

        self.refresh_status()

        return False

    # ------------------------------------------------------------------
    # Confirmation
    # ------------------------------------------------------------------

    def confirm(
        self,
        title,
        message,
    ):

        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.CANCEL,
            text=title,
        )

        dialog.format_secondary_text(
            message
        )

        dialog.add_button(
            "Continue",
            Gtk.ResponseType.OK,
        )

        response = dialog.run()

        dialog.destroy()

        return response == Gtk.ResponseType.OK

    # ------------------------------------------------------------------
    # Miscellaneous
    # ------------------------------------------------------------------

    def set_feedback(self, message):

        self.feedback_label.set_text(
            message
        )

    def on_destroy(self, widget):

        self.controller.shutdown_controller()

        Gtk.main_quit()
