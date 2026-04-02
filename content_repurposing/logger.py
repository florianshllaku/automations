import sys
from datetime import datetime
from pathlib import Path

LOGS_DIR = Path(__file__).parent / "logs"

_run_log_path: Path | None = None


def init_run_log() -> Path:
    global _run_log_path
    LOGS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    _run_log_path = LOGS_DIR / f"run_{timestamp}.log"
    _run_log_path.touch()
    return _run_log_path


def log(message: str, level: str = "INFO") -> None:
    """
    Append a timestamped line to the run log file AND print it to stdout
    so it appears in the terminal and gets captured by the _Tee wrapper.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} [{level}] {message}"

    # Always print to stdout — _Tee in scraper.py will mirror this to the log file
    print(line, flush=True)

    # Also write directly to the log file (covers calls before _Tee is set up)
    if _run_log_path is not None:
        with open(_run_log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def write_raw(text: str) -> None:
    """Write raw text (e.g. from stdout/stderr tee) to the run log."""
    if _run_log_path is None or not text.strip():
        return
    with open(_run_log_path, "a", encoding="utf-8") as f:
        f.write(text if text.endswith("\n") else text + "\n")
