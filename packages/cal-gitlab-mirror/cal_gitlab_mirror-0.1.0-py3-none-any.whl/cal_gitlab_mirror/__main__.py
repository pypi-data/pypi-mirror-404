# ----------------------------------------------------------------------------------------
#   __main__
#   --------
#
#   Entry Point - Verifies correct Python version and starts main
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
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
#   Imports
# ----------------------------------------------------------------------------------------

from __future__ import annotations
import sys
import traceback
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

# ----------------------------------------------------------------------------------------
#   Constants
# ----------------------------------------------------------------------------------------

MIN_PYTHON = (3, 14)

# ----------------------------------------------------------------------------------------
#   Entry
# ----------------------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    if sys.version_info < MIN_PYTHON:
        print("Requires python 3.14 or greater", file=sys.stderr)
        return 1

    if argv is None:
        argv_list = sys.argv[1:]
    else:
        argv_list = list(argv)

    from . import main as cli_main

    try:
        return int(cli_main.main(argv_list))
    except KeyboardInterrupt:
        # Avoids a messy exception dump when ctrl-c pressed
        print()
        print("---- Manually Terminated ----")
        print("")
        return 1
    except SystemExit:
        raise
    except BaseException as e:
        t = "-----------------------------------------------------------------------------\n"
        t += "UNHANDLED EXCEPTION OCCURRED!!\n"
        t += "\n"
        t += traceback.format_exc()
        t += "\n"
        t += f"EXCEPTION: {type(e)} {e}\n"
        t += "-----------------------------------------------------------------------------\n"
        t += "\n"
        print(t, file=sys.stderr)
        return -1


if __name__ == "__main__":
    raise SystemExit(main())
