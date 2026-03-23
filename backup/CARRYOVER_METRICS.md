# Carryover Metrics (`이월수`) Notes

## What was added
- `lottery/analyzer.py`
  - computes historical carryover metrics between consecutive rounds
  - stores repeat distribution / average repeat count / recent pair samples
- `lottery/engine.py`
  - scoring now supports:
    - `carryover_weight`
    - `bonus_carryover_weight`
  - repository recommendations apply dynamic overdue + carryover bonuses consistently
- `api/index.py`
  - recommendation response now includes carryover context based on the latest round
- `lottery/backtest.py`
  - backtests now use the immediately previous draw as carryover source per target round
  - round-level reports store the carryover source numbers used for scoring
- `lottery/top_picks.py`
  - weekly/stable/high-hit top picks now score and tag carryover candidates
- `scripts/analyze_carryover.py`
  - quick CLI for verifying historical carryover statistics

## Current historical finding
Using the current `winningNumbers.xlsx` history:
- average direct carryover count: about `0.8254`
- average carryover count including previous bonus number: about `0.9621`
- distribution of direct carryover count across consecutive round pairs:
  - 0개: 470
  - 1개: 514
  - 2개: 204
  - 3개: 24
  - 4개: 2

Interpretation:
- `이월수 1개` is the most common case.
- `이월수 2개` is not rare enough to ignore.
- aggressive reuse of 3개+ is historically uncommon, so weight helps but hard-fixing many carryovers is usually too strong.

## Suggested operating stance
- stable mode: modest carryover bias
- high_hit mode: slightly stronger carryover bias
- do not force carryovers as mandatory numbers by default
- continue keeping overlap/diversification controls to avoid weekly recommendations collapsing onto the same anchors

## Quick check
```bash
cd FortunaPick
python3 scripts/analyze_carryover.py
```
