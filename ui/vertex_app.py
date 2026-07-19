"""Cloud Run / Vertex entrypoint. Serves the same Streamlit app on $PORT.

No logic here: it execs `streamlit run ui/streamlit_app.py` bound to the port
Cloud Run injects. Core and UI stay single-sourced.

    python ui/vertex_app.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from streamlit.web import cli as stcli

APP = Path(__file__).resolve().parent / "streamlit_app.py"


def main() -> None:
    port = os.environ.get("PORT", "8080")
    sys.argv = [
        "streamlit", "run", str(APP),
        "--server.port", port,
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
