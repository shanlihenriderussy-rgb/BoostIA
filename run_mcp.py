#!/usr/bin/env python3
"""Point d'entrée pour le serveur MCP BoostIA."""

import asyncio
import sys
from pathlib import Path

# Ensure app module is importable
sys.path.insert(0, str(Path(__file__).parent))

from app.mcp_server import main


if __name__ == "__main__":
    asyncio.run(main())
