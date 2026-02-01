"""Scaffolding module entry point.

Usage:
    python -m scaffolding create my_workflow --domain healthcare
    python -m scaffolding list-patterns

Copyright 2025 Smart AI Memory, LLC
Licensed under Fair Source 0.9
"""

from .cli import main

if __name__ == "__main__":
    main()
