#!/usr/bin/env python
"""Django administrative command-line entrypoint."""

import os
import sys


def main() -> None:
    """Configure default Django settings and dispatch CLI arguments."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
