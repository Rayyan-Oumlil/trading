# Kill Switch

How to halt all paper activity in under 30 seconds, without needing to understand the code.

## Freqtrade (crypto)

```bash
docker-compose -f "C:/Users/rayya/Desktop/Claude Trading/docker-compose.yml" stop
```

Verify via the FreqUI at http://localhost:8080 — status should be "stopped". All open trades remain as-is; they don't get force-closed. To force-close first:

```bash
# inside freqtrade container
freqtrade stop_entry   # stop new entries
freqtrade forceexit all   # close all open positions at market
```

## Alpaca (equities, when configured)

Two ways:

1. **Paper dashboard:** https://paper-trading.alpaca.markets/ -> Orders -> Cancel All, Positions -> Close All.
2. **API kill-switch file:** the strategy runner checks for `paper-trading/.HALT` on every loop and exits if present.

```bash
touch "C:/Users/rayya/Desktop/Claude Trading/paper-trading/.HALT"
```

Remove the file to resume.

## Sanity checks after a kill

- Confirm no open orders in the broker UI.
- Confirm no open positions (or that remaining positions are flat by intent).
- Write a `journal/` entry before restarting. Understand WHY you killed it before you restart it.

## When to pull the plug

- Strategy behaves differently from the spec (any trade outside the rules).
- Data feed hiccup (stale bars, NaN values).
- Market event the strategy wasn't designed for (FOMC, flash crash, exchange outage).
- You are emotionally activated (stress, excitement, FOMO) — yes, that alone is a valid reason.

## Fire drill — SOP (required before Stage 3)

The kill switch only counts as proven once it has been tested under fire conditions, not just unit-tested. Run this drill **between EOD runs** (i.e., after one EOD has succeeded and before the next is scheduled), so you don't fight a real signal.

### Procedure

1. **Confirm baseline state.** `git pull` to refresh; verify the most recent commit is a clean `routine: eod ...` from the bot. Confirm `paper-trading/.HALT` does **not** exist.
2. **Arm the switch.**
   ```powershell
   New-Item -ItemType File "C:/Users/rayya/Desktop/Claude Trading/paper-trading/.HALT" -Value "DRILL: $(Get-Date -Format o)"
   ```
3. **Trigger a manual EOD run** from the GitHub Actions tab (`daily-trade` → Run workflow → mode=`eod`).
4. **Verify the no-op.** Expected log line in `run_signal.py` step:
   ```
   HALTED — kill switch active. No orders placed.
   ```
   Expected confidence-log append: `YYYY-MM-DD | HALT | 0/10 | kill switch active`.
   No order should appear in the Alpaca paper activity feed for this run.
5. **Disarm the switch.**
   ```powershell
   Remove-Item "C:/Users/rayya/Desktop/Claude Trading/paper-trading/.HALT"
   ```
6. **Trigger one more manual EOD run.** Verify normal evaluation resumes (no HALT line; appropriate BUY/SELL/HOLD/FLAT confidence-log entry).
7. **Document the drill** in the day's journal entry: timestamp, what happened, what didn't.

### Pass criteria

- Step 4 produced the HALT line in the workflow log AND a `HALT` entry in `memory/confidence-log.md`.
- Step 4 produced **zero** new orders in the Alpaca activity feed.
- Step 6 produced a normal entry, confirming the system is unstuck.
- The drill is recorded in `journal/`.

### Fail handling

If the routine placed an order while `.HALT` existed: stop. Do not advance to Stage 3. Investigate where the kill-switch check was bypassed (likely cause: a routine added later that doesn't import `paper_trading.kill_switch.is_halted`). Fix, re-test, then re-drill.
