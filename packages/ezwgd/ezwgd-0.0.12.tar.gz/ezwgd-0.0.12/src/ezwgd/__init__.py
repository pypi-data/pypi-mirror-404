#  Copyright (C) 2025-2026, HYLi360.
#  Free software distributed under the terms of the GNU GPL-3.0 license,
#  and comes with ABSOLUTELY NO WARRANTY.
#  See at <https://www.gnu.org/licenses/gpl-3.0.en.html>

from rich.console import Console
from rich.traceback import install


# Start Rich Engine.
console = Console()
install(show_locals=True)

_version = "0.0.12"
_nickname = "TESTING"

__version__ = f'{_version} {_nickname}'

__all__ = [
    '__version__',
    'console',
    'evo',
    'tidy',
    'utils',
    'coll',
    'SeqFileNotFoundError',
    'GFF3FileNotFoundError',
]

class BaseException4EZWGD(BaseException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class BaseWarning4EZWGD(UserWarning):
    pass


# ---all custom class (inheritances from BaseException and Warning) we used.--------------------------
class ProgramNotFoundError(BaseException4EZWGD):
    """Called when the external executable file does not exist."""

    def __init__(self, program: str) -> None:
        self.message = (
            f"[ERROR] Can't Find the Executable File of This Program: {program}"
        )

    def __str__(self) -> str:
        return f"{self.message}"

class SeqFileNotFoundError(BaseException4EZWGD):
    """Called when the external executable file does not exist."""

    def __init__(self, seq_file_path: str) -> None:
        self.message = (
            f"[ERROR] Can't Find This Sequence File: {seq_file_path}"
        )

    def __str__(self) -> str:
        return f"{self.message}"

class GFF3FileNotFoundError(BaseException4EZWGD):
    """Called when the external executable file does not exist."""

    def __init__(self, gff3_file_path: str) -> None:
        self.message = (
            f"[ERROR] Can't Find This GFF3 File: {gff3_file_path}"
        )

    def __str__(self) -> str:
        return f"{self.message}"