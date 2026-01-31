"""Non-blocking keyboard input detection for ESC interruption."""

import sys
import threading
import time
from typing import Callable, Optional


# Unix implementation
if sys.platform != 'win32':
    import select
    import tty
    import termios

    def check_key_pressed() -> Optional[str]:
        """Check if a key was pressed (non-blocking).

        Returns:
            The key character if pressed, None otherwise
        """
        if select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1)
        return None

    class KeyListener:
        """Background thread that listens for ESC key press.

        Usage:
            interrupt_event = threading.Event()
            listener = KeyListener(lambda: interrupt_event.set())
            listener.start()
            # ... do work, checking interrupt_event.is_set() ...
            listener.stop()
        """

        def __init__(self, on_escape: Callable[[], None]):
            """Initialize the key listener.

            Args:
                on_escape: Callback to invoke when ESC is pressed
            """
            self.on_escape = on_escape
            self._running = False
            self._thread: Optional[threading.Thread] = None
            self._old_settings = None

        def start(self) -> None:
            """Start listening for keys in background thread."""
            if self._running:
                return

            self._running = True

            try:
                # Save terminal settings
                self._old_settings = termios.tcgetattr(sys.stdin)
                # Set terminal to cbreak mode (no buffering, no echo)
                tty.setcbreak(sys.stdin.fileno())
            except termios.error:
                # Not a TTY (e.g., piped input)
                self._running = False
                return

            # Start listener thread
            self._thread = threading.Thread(target=self._listen, daemon=True)
            self._thread.start()

        def stop(self) -> None:
            """Stop listening and restore terminal settings."""
            self._running = False

            # Wait for thread to finish first (so it stops reading stdin)
            if self._thread:
                self._thread.join(timeout=0.3)
                self._thread = None

            # Restore terminal settings immediately (TCSANOW, not TCSADRAIN which can block)
            if self._old_settings:
                try:
                    termios.tcsetattr(sys.stdin, termios.TCSANOW, self._old_settings)
                except termios.error:
                    pass  # Terminal may have been closed
                self._old_settings = None

            # Flush any buffered stdin to prevent stale input
            try:
                while select.select([sys.stdin], [], [], 0)[0]:
                    sys.stdin.read(1)
            except Exception:
                pass

        def _listen(self) -> None:
            """Background listener loop."""
            while self._running:
                try:
                    key = check_key_pressed()
                    if key == '\x1b':  # ESC key
                        self.on_escape()
                        break
                except Exception:
                    # stdin may be closed or unavailable
                    break

                # Small sleep to avoid busy-waiting
                time.sleep(0.05)

# Windows implementation
else:
    import msvcrt

    class KeyListener:
        """Background thread that listens for ESC key press (Windows)."""

        def __init__(self, on_escape: Callable[[], None]):
            """Initialize the key listener.

            Args:
                on_escape: Callback to invoke when ESC is pressed
            """
            self.on_escape = on_escape
            self._running = False
            self._thread: Optional[threading.Thread] = None

        def start(self) -> None:
            """Start listening for keys in background thread."""
            if self._running:
                return

            self._running = True
            self._thread = threading.Thread(target=self._listen, daemon=True)
            self._thread.start()

        def stop(self) -> None:
            """Stop listening."""
            self._running = False
            if self._thread:
                self._thread.join(timeout=0.2)
                self._thread = None

        def _listen(self) -> None:
            """Background listener loop."""
            while self._running:
                try:
                    if msvcrt.kbhit():
                        key = msvcrt.getch()
                        if key == b'\x1b':  # ESC
                            self.on_escape()
                            break
                except Exception:
                    break

                # Small sleep to avoid busy-waiting
                time.sleep(0.05)
