#!/usr/bin/env python3
"""
Loads Alpaca credentials from .env (never committed to git).
All strategy files import from here instead of hardcoding keys.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # fall back to existing env vars if dotenv not installed

BASE_URL   = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets/v2")
DATA_URL   = os.environ.get("ALPACA_DATA_URL", "https://data.alpaca.markets/v2")
API_KEY    = os.environ.get("ALPACA_API_KEY",    "")
SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY", "")

if not API_KEY or not SECRET_KEY:
    raise EnvironmentError(
        "Alpaca credentials not found. "
        "Copy .env.example to .env and fill in your keys."
    )

HEADERS = {
    "APCA-API-KEY-ID":     API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
    "Content-Type":        "application/json",
}
