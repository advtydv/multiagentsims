import datetime
import time

def log_message(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def now_ns() -> int:
    """Returns the current time in nanoseconds since the epoch."""
    return time.time_ns()