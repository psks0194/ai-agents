"""Locate and import the system under test: the week-6 content-ops server.

The clean production pattern is a path dependency (uv add --editable
../week6-mcp-server). We use a path insert here to stay focused on eval
methodology rather than packaging plumbing.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SERVER_SRC = _REPO_ROOT / "week6-mcp-server" / "src"
if str(_SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(_SERVER_SRC))

from intellaigent_mcp.server import mcp  # noqa: E402

__all__ = ["mcp"]
