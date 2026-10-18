# Prompt — Kill the Idea (red-team a strategy)

Use this BEFORE committing a strategy to paper or live. This is the adversarial review.

---

```
I am about to ship <strategy-name> to <paper/live>.

Before I do, role-play as:

1. **A skeptical quant.** What is the most likely way this strategy is
   overfit? Specifically check: how many parameters? How many trades in
   the backtest? Was there any hyperparameter tuning on the same data
   it was tested on?
2. **A risk manager.** What is the worst realistic loss? Not the
   backtest max drawdown — a worse one. What events would trigger it?
   What happens if the data feed dies mid-trade? If the broker API is
   rate-limited?
3. **A market maker.** If everyone ran this exact strategy, would it
   still work? What is the capacity? At what size does the edge decay?
4. **An efficient-market evangelist.** Why hasn't this edge been
   arbitraged away already? What am I seeing that pros with more data
   and lower costs aren't?

For each role, give me the top concern and a concrete mitigation.
If the mitigations are expensive or don't exist, say "kill the idea".
```

---

## Why this prompt

- Split-role adversarial review (per global `agents.md`): a factual reviewer, a risk expert, a markets expert.
- Forces the capacity question — the one beginners never ask.
- Names the EMH elephant — if you can't answer "why hasn't this been arbitraged", you don't have an edge, you have noise.
