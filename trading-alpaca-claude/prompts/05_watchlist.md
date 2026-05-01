# Prompt: Watchlists

## Purpose
Create and manage Alpaca watchlists for personal holdings, top semiconductors, and top AI companies.

---

## Prompt

```
Create Alpaca watchlists for the following:

1. Personal Watchlist: TSM, TSLA, V, MC, NVDA, AAPL, FB
2. Top 5 semiconductor companies with the most trading activity
3. Top 5 AI companies
```

---

## Ticker Notes

| Requested | Actual  | Reason                                           |
|-----------|---------|--------------------------------------------------|
| FB        | META    | Meta Platforms renamed ticker from FB → META in 2021 |
| MC        | N/A     | LVMH's ticker on Euronext Paris — not listed on US markets. US OTC alternative: LVMUY |

---

## Watchlists Created (2026-04-29)

### 1. Personal Watchlist
**Alpaca ID:** `843c1330-1571-4340-8643-dcdf2c5a3315`

| Symbol | Company                        |
|--------|-------------------------------|
| TSM    | Taiwan Semiconductor (TSMC)   |
| TSLA   | Tesla                         |
| V      | Visa                          |
| NVDA   | NVIDIA                        |
| AAPL   | Apple                         |
| META   | Meta Platforms (formerly FB)  |

---

### 2. Top Semiconductors
**Alpaca ID:** `d37bb6cf-079d-4d43-aed8-ba286f95a3d9`

Ranked by average daily trading volume and market activity:

| Symbol | Company                    | Why Top 5                                      |
|--------|---------------------------|------------------------------------------------|
| NVDA   | NVIDIA                    | #1 by volume; AI chip dominance drives massive activity |
| AMD    | Advanced Micro Devices    | High volume; direct NVDA competitor in CPUs/GPUs |
| INTC   | Intel                     | Large cap; high retail + institutional volume  |
| QCOM   | Qualcomm                  | Mobile chip leader; consistent high activity   |
| MU     | Micron Technology         | Memory chip leader; volatile = high activity   |

**Honorable mentions:** AVGO (Broadcom), AMAT (Applied Materials), ASML

---

### 3. Top AI Companies
**Alpaca ID:** `325354c0-cd8b-4dcf-801f-4b6dd4f9a6aa`

| Symbol | Company   | AI Angle                                              |
|--------|-----------|-------------------------------------------------------|
| MSFT   | Microsoft | Azure AI, OpenAI partnership, Copilot across products |
| GOOGL  | Alphabet  | Gemini, DeepMind, Google Cloud AI                     |
| META   | Meta      | LLaMA open-source models, AI-powered ads, Ray-Ban AI  |
| AMZN   | Amazon    | AWS Bedrock, Alexa, Anthropic investment              |
| PLTR   | Palantir  | Pure-play AI/data platform for enterprise & government|

**Honorable mentions:** ORCL (Oracle Cloud AI), IBM, SNOW (Snowflake AI)

---

## API Reference

```bash
# Create a watchlist
curl -s -X POST "$BASE_URL/watchlists" \
  -H "APCA-API-KEY-ID: $API_KEY" \
  -H "APCA-API-SECRET-KEY: $SECRET_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "My List", "symbols": ["TSLA", "NVDA"]}' | python3 -m json.tool

# List all watchlists
curl -s "$BASE_URL/watchlists" \
  -H "APCA-API-KEY-ID: $API_KEY" \
  -H "APCA-API-SECRET-KEY: $SECRET_KEY" | python3 -m json.tool

# Add a symbol to existing watchlist
curl -s -X POST "$BASE_URL/watchlists/{watchlist_id}" \
  -H "APCA-API-KEY-ID: $API_KEY" \
  -H "APCA-API-SECRET-KEY: $SECRET_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL"}' | python3 -m json.tool

# Delete a symbol from watchlist
curl -s -X DELETE "$BASE_URL/watchlists/{watchlist_id}/{symbol}" \
  -H "APCA-API-KEY-ID: $API_KEY" \
  -H "APCA-API-SECRET-KEY: $SECRET_KEY"
```
