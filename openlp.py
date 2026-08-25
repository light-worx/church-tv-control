import subprocess
from pathlib import Path


class OpenLPBackend:
    """
    Local OpenLP operations.

    These operations are performed on the OpenLP PC itself.
    """

    def __init__(self):
        self.repair_script = (
            Path(__file__).resolve().parent
            / "clearcorrupt.sh"
        )

    def fix_service_problem(self) -> str:
        """
        Remove OpenLP's thumbnails cache to repair
        corrupted service-file problems.
        """

        if not self.repair_script.exists():
            raise RuntimeError(
                f"Repair script not found: {self.repair_script}"
            )

        if not self.repair_script.is_file():
            raise RuntimeError(
                f"Repair script is not a file: {self.repair_script}"
            )

        if not self.repair_script.stat().st_mode & 0o111:
            raise RuntimeError(
                "The OpenLP repair script is not executable."
            )

        result = subprocess.run(
            [str(self.repair_script)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            error = result.stderr.strip()

            if not error:
                error = (
                    f"Repair script failed "
                    f"with exit code {result.returncode}."
                )

            raise RuntimeError(error)

        return "OpenLP service problem has been fixed."
