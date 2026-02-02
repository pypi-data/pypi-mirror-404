"""Entry point for running nspec validator as a module.

Usage:
    python -m src.tools.nspec --validate
    python -m src.tools.nspec --generate
    python -m src.tools.nspec --progress 124
"""

import sys

from nspec.cli import main

if __name__ == "__main__":
    sys.exit(main())
