# ----------------------------------------------------------------------------------------
#   __main__
#   --------
#
#   Entry point for python -m cal_gitlab_mirror.
#
#   License
#   -------
#   MIT License - Copyright 2026 Cyber Assessment Labs
#
#   Authors
#   -------
#   bena (via claude)
#
#   Version History
#   ---------------
#   Jan 2026 - Created
#   Feb 2026 - Simplified to delegate to cli.main()
# ----------------------------------------------------------------------------------------

import sys

MIN_PYTHON = (3, 14)
if sys.version_info < MIN_PYTHON:
    print(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required.", file=sys.stderr)
    sys.exit(1)

from cal_gitlab_mirror.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
