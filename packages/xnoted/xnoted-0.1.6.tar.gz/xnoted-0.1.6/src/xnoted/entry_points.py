"""Main entry point for xnoted when run as a module."""

from xnoted.app import XNotedApp


def xnoted():
    """Run the xnoted application."""
    app = XNotedApp()
    app.run()

