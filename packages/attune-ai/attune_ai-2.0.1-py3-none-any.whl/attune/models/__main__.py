"""Enable running the models CLI as a module.

Usage:
    python -m attune.models registry
    python -m attune.models tasks
    python -m attune.models validate config.yaml
    python -m attune.models costs
"""

from .cli import main

if __name__ == "__main__":
    exit(main())
