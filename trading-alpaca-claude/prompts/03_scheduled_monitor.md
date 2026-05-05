# Prompt: Scheduled Strategy Monitor (Remote Agent)

## Purpose
A self-contained prompt for a remote Claude agent that monitors an active trailing stop strategy
every hour during market hours. The agent checks price, manages the floor, detects stop triggers,
and reports on ladder order fills.

## Schedule Details

| Field       | Value                                              |
|-------------|---------------------------------------------------|
| Routine ID  | trig_01WCU6eUiUCxeVmp9gMYsDVj                    |
| Cron (UTC)  | `0 14,15,16,17,18,19,20 * * 1-5`                |
| Human time  | Every hour 10am–4pm EDT, Mon–Fri                 |
| Model       | claude-sonnet-4-6                                 |
| Manage at   | https://claude.ai/code/routines/trig_01WCU6eUiUCxeVmp9gMYsDVj |

## Prompt

```
You are a TSLA trailing stop strategy monitor. Run the Python script below using Bash and report results.

## Alpaca Paper Trading Credentials
- Base URL: https://paper-api.alpaca.markets/v2
- Data URL: https://data.alpaca.markets/v2
- API Key: PK74KUHTNG2CYS3WDRU6WH5VC5
- Secret Key: 4xGmMFCxq98tp9uENPt5ASNdzsjjLG53PxiZGBSZm59i

## Strategy Parameters
- Symbol: TSLA
- Entry price: $371.94
- Initial stop floor: $334.75 (10% below entry — floor never goes down)
- Trailing activates when price >= $409.13 (+10% from entry)
- Once trailing: floor = 5% below today's HIGH (so floor only goes up)
- Ladder Buy #1: 20 shares limit at $297.55 (-20% from entry)
- Ladder Buy #2: 10 shares limit at $260.36 (-30% from entry)

## Actions the script takes:
1. Fetch current TSLA price from Alpaca data API
2. Fetch today's high bar (used as peak for trailing floor calc)
3. Check current position (shares held, avg cost)
4. Check open orders (are ladders still open or filled?)
5. Apply strategy logic:
   - If price <= floor: sell all shares at market + cancel open orders
   - If trailing active: calculate new floor (5% below today's high), log if raised
   - If ladder filled: log fill details
6. Print structured summary

Save the script to /tmp/tsla_monitor.py and run: python3 /tmp/tsla_monitor.py
If the script errors, diagnose and fix it inline. Report the full output.
```

## Output Format

```
==================================================
  TSLA Strategy Monitor — YYYY-MM-DD HH:MM UTC
==================================================
  Price        : $X.XX  (+X.XX% from entry)
  Today High   : $X.XX
  Position     : X shares @ avg $X.XX
  Active Floor : $X.XX
  Trail Mode   : ON / OFF (triggers at $409.13)
  Ladder #1    : OPEN / FILLED @ $X.XX
  Ladder #2    : OPEN / FILLED @ $X.XX
  Action       : NONE / STOP TRIGGERED / FLOOR RAISED
==================================================
```

## Notes
- Peak is approximated using today's high bar since the agent has no persistent memory between runs.
- Floor is the max of the initial floor ($334.75) and any raised trailing floor.
- To update strategy params (new entry, new floor), update the routine prompt at the link above.
