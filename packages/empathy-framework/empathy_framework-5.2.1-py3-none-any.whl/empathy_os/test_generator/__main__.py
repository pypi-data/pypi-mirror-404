"""Make test_generator runnable as a module.

Usage:
    python -m test_generator generate soap_note --patterns linear_flow,approval
    python -m test_generator analyze debugging --patterns code_analysis_input

Copyright 2025 Smart AI Memory, LLC
Licensed under Fair Source 0.9
"""

from .cli import main

if __name__ == "__main__":
    main()
