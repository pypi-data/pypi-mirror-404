# ----------------------------------------------------------------------------------------
#   version
#   -------
#
#   Version string handling - imports from generated _version.py at build time,
#   falls back to "dev" when not built.
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
#   Version
# ----------------------------------------------------------------------------------------


def _get_version() -> str:
    try:
        from ._version import (  # pyright: ignore[reportMissingImports]
            __version__ as _v,  # pyright: ignore[reportUnknownVariableType]
        )

        return str(_v)  # pyright: ignore[reportUnknownArgumentType]
    except ImportError:
        return "dev"


VERSION_STR: str = _get_version()
