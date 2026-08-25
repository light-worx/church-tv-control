from dataclasses import dataclass


@dataclass
class TVStatus:
    tv_online: bool
    church_tv_running: bool
    openlp_reachable: bool
    message: str = ""

    @property
    def all_ok(self) -> bool:
        return (
            self.tv_online
            and self.church_tv_running
            and self.openlp_reachable
        )