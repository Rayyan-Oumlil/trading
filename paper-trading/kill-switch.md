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
2. **API kill-switch file:** the strategy runner checks for `.HALT` at the **repository root** on every loop and exits if present. Path is `<repo>/.HALT` — NOT `paper-trading/.HALT` (that subfolder is documentation only). Source of truth: `paper_trading/kill_switch.py` → `HALT_FILE = PROJECT_ROOT / ".HALT"`.

```bash
# Preferred (handles timestamp + reason atomically):
python -c "from paper_trading.kill_switch import create_halt; create_halt('reason here')"

# Or manually:
touch "C:/Users/rayya/Desktop/Claude Trading/.HALT"
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

1. **Confirm baseline state.** `git pull` to refresh; verify the most recent commit is a clean `routine: eod ...` from the bot. Confirm `.HALT` does **not** exist.
2. **Arm the switch.** Use the helper to get a timestamped halt file, then commit + push so GHA sees it:
   ```bash
   python -c "from paper_trading.kill_switch import create_halt; create_halt('fire drill')"
   git add .HALT && git commit -m "halt: fire drill" && git push
   ```
3. **Trigger a manual EOD run** from the GitHub Actions tab (`daily-trade` → Run workflow → mode=`eod`).
4. **Verify the no-op.** Expected log line in `run_signal.py` step:
   ```
   HALTED — kill switch active. No orders placed.
   ```
   Expected confidence-log append: `YYYY-MM-DD | HALT | 0/10 | kill switch active`.
   No order should appear in the Alpaca paper activity feed for this run.
5. **Disarm the switch.**
   ```bash
   python -c "from paper_trading.kill_switch import remove_halt; remove_halt()"
   git add -A && git commit -m "halt: cleared" && git push
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
