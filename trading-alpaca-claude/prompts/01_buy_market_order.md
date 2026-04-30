# Prompt: Buy Market Order

## Purpose
Place a market buy order for a single stock via the Alpaca paper trading API using curl.

## Prompt

```
Buy one share of [SYMBOL] using my Alpaca paper trading account.

Account: trade-app
Endpoint: https://paper-api.alpaca.markets/v2
Key: [API_KEY]
Secret: [SECRET_KEY]
```

## Curl Template

```bash
curl -s -X POST "$BASE_URL/orders" \
  -H "APCA-API-KEY-ID: $API_KEY" \
  -H "APCA-API-SECRET-KEY: $SECRET_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "TSLA",
    "qty": "1",
    "side": "buy",
    "type": "market",
    "time_in_force": "day"
  }' | python3 -m json.tool
```

## First Use
- Symbol: TSLA
- Qty: 1 share
- Order ID: a6b8d53b-ee83-49b4-9788-256ce6b8b9a4
- Status: accepted
- Date: 2026-04-29
