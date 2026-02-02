#!/usr/bin/env python3
"""
souleyez.ui.progress_indicators - Progress indicators for long-running operations

Provides entertaining progress feedback during AI generation and other slow tasks.
"""

import sys
import threading
import time
from typing import Any, Callable, Optional

import click

from souleyez.ui.ai_quotes import get_random_quote


class QuoteRotator:
    """Rotates entertaining quotes while a long operation runs."""

    def __init__(self, interval: float = 7.0, prefix: str = "🤖 "):
        """
        Initialize the quote rotator.

        Args:
            interval: Seconds between quote rotations (default: 7.0)
            prefix: Prefix to show before each quote (default: "🤖 ")
        """
        self.interval = interval
        self.prefix = prefix
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._first_quote = True

    def _rotate_quotes(self):
        """Background thread that rotates quotes."""
        while not self._stop_event.is_set():
            # Get a random quote
            quote = get_random_quote()

            # Clear the current line and print new quote
            if self._first_quote:
                # First quote: just print it
                click.echo(f"{self.prefix}{quote}", nl=False)
                self._first_quote = False
            else:
                # Subsequent quotes: clear line and rewrite
                # \r moves cursor to beginning, then we overwrite with spaces and new content
                sys.stdout.write("\r" + " " * 120 + "\r")  # Clear line
                sys.stdout.write(f"{self.prefix}{quote}")
                sys.stdout.flush()

            # Wait for interval or until stopped
            self._stop_event.wait(self.interval)

        # Clear the quote line when done
        sys.stdout.write("\r" + " " * 120 + "\r")
        sys.stdout.flush()

    def start(self):
        """Start rotating quotes in background thread."""
        self._stop_event.clear()
        self._first_quote = True
        self._thread = threading.Thread(target=self._rotate_quotes, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop rotating quotes."""
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=1.0)


def with_quotes(
    func: Callable, *args, interval: float = 7.0, prefix: str = "🤖 ", **kwargs
) -> Any:
    """
    Execute a function with rotating quotes in the background.

    Args:
        func: The function to execute
        *args: Positional arguments to pass to func
        interval: Seconds between quote rotations (default: 7.0)
        prefix: Prefix to show before each quote (default: "🤖 ")
        **kwargs: Keyword arguments to pass to func

    Returns:
        The return value from func

    Example:
        ```python
        result = with_quotes(slow_function, arg1, arg2, interval=5.0)
        ```
    """
    rotator = QuoteRotator(interval=interval, prefix=prefix)

    try:
        rotator.start()
        result = func(*args, **kwargs)
        return result
    finally:
        rotator.stop()


class QuoteContext:
    """Context manager for displaying rotating quotes during a code block."""

    def __init__(self, interval: float = 7.0, prefix: str = "🤖 "):
        """
        Initialize the quote context manager.

        Args:
            interval: Seconds between quote rotations (default: 7.0)
            prefix: Prefix to show before each quote (default: "🤖 ")
        """
        self.rotator = QuoteRotator(interval=interval, prefix=prefix)

    def __enter__(self):
        """Start rotating quotes."""
        self.rotator.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop rotating quotes."""
        self.rotator.stop()
        return False  # Don't suppress exceptions


# Convenience function for AI generation specifically
def with_ai_quotes(func: Callable, *args, **kwargs) -> Any:
    """
    Execute a function with AI-themed rotating quotes.

    This is a convenience wrapper around with_quotes() with AI-specific defaults.

    Args:
        func: The function to execute
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func

    Returns:
        The return value from func

    Example:
        ```python
        from souleyez.ui.progress_indicators import with_ai_quotes

        recommendation = with_ai_quotes(
            recommender.suggest_next_step,
            engagement_id
        )
        ```
    """
    return with_quotes(func, *args, interval=7.0, prefix="🤖 ", **kwargs)
