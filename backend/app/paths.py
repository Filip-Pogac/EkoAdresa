"""Location of the committed data snapshots (repo-root data/).

Locally this file is backend/app/paths.py, so parents[2] is the repo root. In the Docker
image it is /app/app/paths.py, so parents[2] is / and data/ is the /data volume mounted
by docker-compose. DATA_DIR overrides both (e.g. on a hosting platform).
"""

import os
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR") or Path(__file__).resolve().parents[2] / "data")
