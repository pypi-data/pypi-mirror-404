"""sageLLM Developer Tools.

Unified toolkit for sageLLM multi-repository development workflow.

CLI Tool: sage-dev

Examples:
    $ sage-dev init          # Clone all repos
    $ sage-dev sync          # Sync all repos
    $ sage-dev check         # Run checks
    $ sage-dev hooks install # Install git hooks
    $ sage-dev gh list <repo> # List open issues
"""

from __future__ import annotations

__version__ = "0.2.2.0"

__all__ = ["__version__"]
