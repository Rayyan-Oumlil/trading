from routines_pkg.desk_merge_guard import blocked_paths


def test_desk_output_paths_are_mergeable():
    paths = ["journal/2026-10-05.md", "memory/desk-notes.md", "memory/desk-alert.txt",
             "research/queue.md", "backtests/momentum/results/run.json", "backtests/registry.md", ".HALT"]
    assert blocked_paths(paths) == []


def test_code_and_workflows_are_blocked():
    paths = ["journal/x.md", "run_signal.py", ".github/workflows/daily-trade.yml", "paper_trading/guards.py"]
    assert blocked_paths(paths) == ["run_signal.py", ".github/workflows/daily-trade.yml", "paper_trading/guards.py"]


def test_desk_may_not_rewrite_robot_state_or_strategy_specs():
    paths = ["memory/confidence-log.md", "memory/portfolio-state.md", "strategies/ma_crossover/STRATEGY.md", "CLAUDE.md"]
    assert blocked_paths(paths) == paths


def test_lookalike_paths_are_blocked():
    assert blocked_paths(["journal_evil.py", ".HALT.sh", "memory/../run_signal.py"]) == [
        "journal_evil.py", ".HALT.sh", "memory/../run_signal.py"]


def test_empty_diff_is_mergeable():
    assert blocked_paths([]) == []


def test_python_under_backtests_is_blocked_because_ci_runs_it_with_secrets():
    paths = ["backtests/momentum/backtest.py", "backtests/test_leak.py", "backtests/conftest.py", "backtests/momentum/results/x.py"]
    assert blocked_paths(paths) == paths
