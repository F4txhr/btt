import os
import fcntl
import time
import logging

logger = logging.getLogger(__name__)

# =============================
# TOKEN LOCKING
# =============================

_token_lock_fd = None

def acquire_token_lock(lock_file: str, timeout_seconds: int) -> bool:
    """
    Acquires an exclusive, process-safe file lock.
    Blocks until the lock is acquired or the timeout is reached.

    Args:
        lock_file: The path to the file to use for locking.
        timeout_seconds: The maximum time to wait for the lock.

    Returns:
        True if the lock was acquired, False otherwise.
    """
    global _token_lock_fd
    start_time = time.time()
    # Open or create the lock file
    _token_lock_fd = os.open(lock_file, os.O_CREAT | os.O_RDWR)

    while True:
        try:
            # Attempt to acquire an exclusive, non-blocking lock
            fcntl.flock(_token_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Write the current PID for observability/debugging
            try:
                os.ftruncate(_token_lock_fd, 0)
                os.write(_token_lock_fd, str(os.getpid()).encode())
                os.lseek(_token_lock_fd, 0, os.SEEK_SET) # Rewind to start
            except (IOError, OSError):
                pass # Ignore if writing fails, lock is still held
            logger.info(f"Acquired token lock on '{lock_file}' for PID {os.getpid()}.")
            return True
        except (IOError, OSError): # Catches BlockingIOError on Linux
            if time.time() - start_time > timeout_seconds:
                logger.warning(f"Timeout waiting for token lock on '{lock_file}'.")
                os.close(_token_lock_fd)
                _token_lock_fd = None
                return False
            time.sleep(0.2)

def release_token_lock():
    """Releases the held file lock."""
    global _token_lock_fd
    if _token_lock_fd is None:
        return

    try:
        fcntl.flock(_token_lock_fd, fcntl.LOCK_UN)
        os.close(_token_lock_fd)
        logger.info(f"Released token lock for PID {os.getpid()}.")
    except (IOError, OSError) as e:
        logger.error(f"Error releasing token lock: {e}")
    finally:
        _token_lock_fd = None


# =============================
# PID MANAGEMENT
# =============================

def is_process_running(pid: int) -> bool:
    """
    Checks if a process with the given PID is currently running.
    """
    if not pid:
        return False
    try:
        # Sending signal 0 to a pid will raise an OSError if the pid is not running,
        # and do nothing otherwise.
        os.kill(pid, 0)
        return True
    except OSError: # ProcessLookupError is a subclass of OSError
        return False

class PIDManager:
    """
    A context manager for handling PID files to ensure single-instance execution.

    Example:
        pid_manager = PIDManager("my_app.pid")
        with pid_manager as pid_is_new:
            if not pid_is_new:
                logger.error("Process already running.")
                return
            # ... rest of the application logic ...
    """
    def __init__(self, pid_file: str):
        self.pid_file = pid_file
        self.pid = os.getpid()

    def __enter__(self) -> bool:
        """
        Enters the context, checking for and writing the PID file.

        Returns:
            True if the new PID file was created successfully and no other
            instance is running. False if another instance is detected.
        """
        if os.path.exists(self.pid_file):
            try:
                with open(self.pid_file, 'r') as f:
                    old_pid = int(f.read().strip())
                if is_process_running(old_pid):
                    return False # Another instance is running
            except (ValueError, FileNotFoundError):
                # PID file is invalid or was removed between check and read
                pass

        # Write the new PID file
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(self.pid))
            return True
        except IOError:
            return False

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exits the context, cleaning up the PID file.
        """
        try:
            # Only remove the pid file if it's ours
            with open(self.pid_file, 'r') as f:
                if int(f.read().strip()) == self.pid:
                    os.remove(self.pid_file)
        except (IOError, ValueError, FileNotFoundError):
            pass
