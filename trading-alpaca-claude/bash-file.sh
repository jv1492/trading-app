#!/bin/bash

# Alpaca Paper Trading - Bash Scripts
# Account: trade-app | Mode: paper
# Config: trading-alpaca-claude/alpaca-config.json

BASE_URL="https://paper-api.alpaca.markets/v2"
API_KEY="PK5TSOUE524H625IZGF3BJZEBF"
SECRET_KEY="HbQseBQaXpEFHDE21zZCSQUi2GhhWfWnmUKZqC1Vvh2x"

# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────

# Create project folder
# mkdir -p trading-alpaca-claude


# ─────────────────────────────────────────────
# ORDERS
# ─────────────────────────────────────────────

# Buy 1 share of Tesla (market order)
# curl -s -X POST "$BASE_URL/orders" \
#   -H "APCA-API-KEY-ID: $API_KEY" \
#   -H "APCA-API-SECRET-KEY: $SECRET_KEY" \
#   -H "Content-Type: application/json" \
#   -d '{
#     "symbol": "TSLA",
#     "qty": "1",
#     "side": "buy",
#     "type": "market",
#     "time_in_force": "day"
#   }' | python3 -m json.tool


# ─────────────────────────────────────────────
# TRAILING STOP STRATEGY — TSLA
# Script: strategy_tsla.py
# ─────────────────────────────────────────────

# Run setup only (places buy + ladder orders, prints summaries, no monitoring loop)
# python3 strategy_tsla.py --setup-only

# Run full strategy (setup + live price monitoring + auto stop execution)
# python3 strategy_tsla.py

# Strategy rules:
#   Entry      : Buy 10 shares at market
#   Stop floor : Sell ALL if price drops 10% from peak (floor never goes down)
#   Trailing   : Once up +10% from entry, trail 5% below peak price
#   Ladder #1  : Buy 20 shares at -20% from entry (GTC limit order)
#   Ladder #2  : Buy 10 shares at -30% from entry (GTC limit order)

# Last run (2026-04-29):
#   Entry price : $371.94
#   Stop floor  : $334.75  (-10%)
#   Trail on at : $409.13  (+10%)
#   Ladder #1   : $297.55  (-20%) → 20 shares  | Order: 479564af
#   Ladder #2   : $260.36  (-30%) → 10 shares  | Order: 9d463fda


# ─────────────────────────────────────────────
# FUTURE CODE GOES BELOW
# ─────────────────────────────────────────────
