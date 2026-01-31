"""Entry point for folderbot: python -m folderbot"""

import sys

from .cli import main


if __name__ == "__main__":
    sys.exit(main())
