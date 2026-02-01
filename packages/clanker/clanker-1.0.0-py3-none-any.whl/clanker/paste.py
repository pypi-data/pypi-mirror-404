from __future__ import annotations

from dataclasses import dataclass
import errno
import os
from pathlib import Path
import sys


@dataclass
class PasteResult:
    ok: bool
    reason: str | None = None


def paste_into_terminal(text: str) -> PasteResult:
    if not text:
        return PasteResult(False, "empty command")

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return PasteResult(False, "stdin/stdout is not a TTY")

    legacy_setting = _read_legacy_tiocsti()
    if legacy_setting == "0":
        return PasteResult(False, "TIOCSTI disabled (dev.tty.legacy_tiocsti=0)")

    try:
        import fcntl
        import termios
    except ImportError:
        return PasteResult(False, "TIOCSTI not available on this platform")

    try:
        fd = os.open("/dev/tty", os.O_RDWR)
    except OSError as exc:
        return PasteResult(False, f"failed to open /dev/tty: {exc}")

    try:
        data = text.encode("utf-8")
        for byte in data:
            try:
                fcntl.ioctl(fd, termios.TIOCSTI, bytes([byte]))
            except OSError as exc:
                if exc.errno == errno.EPERM:
                    return PasteResult(False, "TIOCSTI denied by kernel or security policy")
                return PasteResult(False, f"TIOCSTI ioctl failed: {exc}")
    finally:
        os.close(fd)

    return PasteResult(True)


def _read_legacy_tiocsti() -> str | None:
    path = Path("/proc/sys/dev/tty/legacy_tiocsti")
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
