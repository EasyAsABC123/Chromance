"""Engineering CAD workflow; model source remains the editable master."""

import os
from pathlib import Path
import tempfile

# Keep caches and the bundled CAD kernel's font discovery local to this process.
# OCCT's bundled fontconfig may predate distribution-specific XML extensions.
_cache = Path(tempfile.gettempdir()) / f"fdm-cad-cache-{os.getuid() if hasattr(os, 'getuid') else 'user'}"
os.environ.setdefault("XDG_CACHE_HOME", str(_cache))
os.environ.setdefault("MPLCONFIGDIR", str(_cache / "matplotlib"))
if os.name == "posix":
    os.environ.setdefault("FONTCONFIG_FILE", str(Path(__file__).with_name("fonts.conf")))

__version__ = "0.1.0"
