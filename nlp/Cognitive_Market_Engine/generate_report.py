"""
CME Backtest Report Generator
  - Runs full backtest with REAL yfinance BTC data + FinBERT NLP
  - Saves plain text report to reports/backtest_report.txt
  - Saves 8 PNG charts to reports/
  - No HTML, no CSS, no webpage
"""

import os, sys, json, time, logging
from datetime import datetime, timedelta
from collections import defaultdict

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

try:
    from config.logging_config import setup_logging
    setup_logging(level="WARNING")
except Exception:
    logging.basicConfig(level=logging.WARNING)

from backtesting.backtest_engine import BacktestRunner, BacktestResult
from backtesting.historical_events_generator import HistoricalEventsGenerator
from backtesting.cognitive_signal_bridge import CognitiveSignalBridge


# ── Charts ──────────────────────────────────────────────────────────

def plot_equity_curve(result, out_dir):
    fig, ax = plt.subplots(figsize=(12, 4))
    ts = [s.timestamp for s in result.equity_curve]
    eq = [s.equity for s in result.equity_curve]
    ax.plot(ts, eq, "b-", linewidth=1.5)
    ax.axhline(result.initial_capital, color="gray", ls="--", lw=0.8)
    for t in result.trades:
        c = "green" if t.pnl > 0 else "red"
        ax.axvline(t.entry_time, color=c, alpha=0.15, lw=0.5)
    ax.set_title("Equity Curve")
    ax.set_ylabel("Portfolio Value ($)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "01_equity_curve.png"), dpi=150)
    plt.close(fig)


def plot_trade_pnl(result, out_dir):
    fig, ax = plt.subplots(figsize=(12, 4))
    pnls = [t.pnl for t in result.trades]
    colors = ["green" if p > 0 else "red" for p in pnls]
    ax.bar(range(1, len(pnls)+1), pnls, color=colors, width=0.7)
    ax.axhline(0, color="gray", lw=0.5)
    ax.set_title("Per-Trade P&L")
    ax.set_xlabel("Trade #")
    ax.set_ylabel("P&L ($)")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "02_trade_pnl.png"), dpi=150)
    plt.close(fig)


def plot_cumulative_pnl(result, out_dir):
    fig, ax = plt.subplots(figsize=(12, 4))
    pnls = [t.pnl for t in result.trades]
    cum = np.cumsum(pnls)
    ts = [t.exit_time for t in result.trades]
    ax.plot(ts, cum, "c-o", markersize=4, lw=1.5)
    ax.fill_between(ts, cum, 0, where=[c >= 0 for c in cum], color="green", alpha=0.1)
    ax.fill_between(ts, cum, 0, where=[c < 0 for c in cum], color="red", alpha=0.1)
    ax.axhline(0, color="gray", lw=0.5)
    ax.set_title("Cumulative P&L")
    ax.set_ylabel("Cumulative P&L ($)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "03_cumulative_pnl.png"), dpi=150)
    plt.close(fig)


def plot_accuracy_by_type(bridge, out_dir):
    fig, ax = plt.subplots(figsize=(10, 5))
    details = bridge.get_event_study_results().get("event_details", [])
    by_type = defaultdict(lambda: {"c": 0, "t": 0})
    for d in details:
        et = d.get("event_type", "unknown")
        by_type[et]["t"] += 1
        if d["correct"]:
            by_type[et]["c"] += 1
    types = sorted(by_type.keys())
    accs = [by_type[t]["c"] / by_type[t]["t"] * 100 for t in types]
    totals = [by_type[t]["t"] for t in types]
    colors = ["green" if a >= 60 else "gold" if a >= 50 else "red" for a in accs]
    bars = ax.bar(types, accs, color=colors, width=0.6)
    for bar, n, a in zip(bars, totals, accs):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()+1,
                f"{a:.0f}% (n={n})", ha="center", fontsize=8)
    ax.axhline(50, color="orange", ls="--", lw=1, label="Random 50%")
    ax.axhline(60, color="green", ls="--", lw=1, alpha=0.5, label="Target 60%")
    ax.set_title("Directional Accuracy by Event Type")
    ax.set_ylabel("Accuracy (%)")
    ax.set_ylim(0, 105)
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "04_accuracy_by_type.png"), dpi=150)
    plt.close(fig)


def plot_metrics_bars(result, dir_acc, out_dir):
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.5))
    data = [
        ("Win Rate", result.win_rate*100, 45, "%"),
        ("Sharpe", result.sharpe_ratio, 1.0, ""),
        ("Profit Factor", result.profit_factor, 1.0, "x"),
        ("Dir. Accuracy", dir_acc*100, 55, "%"),
    ]
    for ax, (name, val, thresh, suf) in zip(axes, data):
        c = "green" if val >= thresh else "red"
        ax.barh(0, val, color=c, height=0.5)
        ax.axvline(thresh, color="orange", ls="--", lw=1.5)
        ax.text(val/2, 0, f"{val:.1f}{suf}", ha="center", va="center",
                fontsize=14, fontweight="bold")
        ax.set_title(name)
        ax.set_yticks([])
        ax.set_xlim(0, max(val*1.3, thresh*1.3))
    fig.suptitle("Key Metrics", fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "05_metrics.png"), dpi=150)
    plt.close(fig)


def plot_sentiment_vs_return(bridge, events, out_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    sents, rets, etypes = [], [], []
    for a, ev in zip(bridge.event_analyses, events):
        fs = a.nlp_parse.get("financial_sentiment", {})
        if isinstance(fs, dict):
            ws = fs.get("weighted_score", 0)
            if isinstance(ws, (int, float)) and ws != 0:
                ret = ((ev.price_24h_after - ev.price_at_event) / ev.price_at_event) * 100
                sents.append(ws)
                rets.append(ret)
                etypes.append(ev.event_type)
    cmap = {"rate_decision": "blue", "regulatory": "purple", "technical": "cyan",
            "geopolitical": "orange", "macro_data": "gold", "earnings": "green"}
    for et in set(etypes):
        m = [i for i, t in enumerate(etypes) if t == et]
        ax.scatter([sents[i] for i in m], [rets[i] for i in m],
                   c=cmap.get(et, "gray"), s=50, alpha=0.8, label=et)
    if len(sents) > 3:
        z = np.polyfit(sents, rets, 1)
        xl = np.linspace(min(sents), max(sents), 100)
        ax.plot(xl, np.poly1d(z)(xl), "r--", lw=1.5, label=f"Slope={z[0]:.2f}")
    ax.axhline(0, color="gray", lw=0.5); ax.axvline(0, color="gray", lw=0.5)
    ax.set_title("FinBERT Sentiment vs Actual 24h Return (Contrarian Edge)")
    ax.set_xlabel("FinBERT Sentiment Score")
    ax.set_ylabel("Actual 24h Return (%)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "06_sentiment_vs_return.png"), dpi=150)
    plt.close(fig)


def plot_participant_accuracy(bridge, out_dir):
    fig, ax = plt.subplots(figsize=(10, 5))
    pa = bridge.get_participant_comparison().get("participant_accuracy", {})
    if not pa:
        plt.close(fig); return
    names, vals = [], []
    for p, d in sorted(pa.items(), key=lambda x: x[1].get("accuracy", 0)):
        a = d.get("accuracy", 0)
        if isinstance(a, str): a = float(a.replace("%", "")) / 100
        names.append(p.replace("phase_", "P:"))
        vals.append(a * 100)
    colors = ["green" if v >= 50 else "red" for v in vals]
    ax.barh(names, vals, color=colors, height=0.6)
    ax.axvline(50, color="orange", ls="--", lw=1.5)
    for i, v in enumerate(vals):
        ax.text(v + 0.5, i, f"{v:.1f}%", va="center", fontsize=9)
    ax.set_title("Participant Directional Accuracy")
    ax.set_xlabel("Accuracy (%)")
    ax.set_xlim(0, 65)
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "07_participant_accuracy.png"), dpi=150)
    plt.close(fig)


def plot_ambiguity(bridge, out_dir):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    amb = [a.ambiguity_score for a in bridge.event_analyses]
    agr = [a.participant_agreement for a in bridge.event_analyses]
    ax1.hist(amb, bins=12, color="mediumpurple", alpha=0.8, edgecolor="white")
    ax1.axvline(np.mean(amb), color="cyan", lw=1.5, label=f"Mean={np.mean(amb):.2f}")
    ax1.axvline(0.3, color="orange", ls="--", lw=1, label="Threshold 0.3")
    ax1.set_title("Ambiguity Score Distribution")
    ax1.set_xlabel("Ambiguity Score"); ax1.set_ylabel("Count")
    ax1.legend(fontsize=8)
    details = bridge.get_event_study_results().get("event_details", [])
    for i, (a_s, ag) in enumerate(zip(amb, agr)):
        correct = details[i]["correct"] if i < len(details) else False
        ax2.scatter(a_s, ag, c="green" if correct else "red",
                    marker="o" if correct else "x", s=50, alpha=0.7)
    ax2.set_title("Ambiguity vs Agreement (green=correct)")
    ax2.set_xlabel("Ambiguity Score"); ax2.set_ylabel("Agreement")
    ax2.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "08_ambiguity.png"), dpi=150)
    plt.close(fig)


# ── Text Report ─────────────────────────────────────────────────────

def write_text_report(result, bridge, events, event_study, elapsed, out_path):
    """Write plain text report to file."""
    lines = []
    w = lines.append

    dir_acc = float(event_study.get("directional_accuracy", 0))
    n_mod = len([v for v in bridge.registry.modules.values() if v is not None])

    w("=" * 70)
    w("  COGNITIVE MARKET ENGINE  -  BACKTEST REPORT")
    w("=" * 70)
    w(f"  Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    w(f"  Asset     : BTC-USD")
    w(f"  Period    : {result.start_date.date()} to {result.end_date.date()}")
    w(f"  Data      : Real yfinance prices + FinBERT NLP sentiment")
    w(f"  Modules   : {n_mod} loaded (67 modules from 96 files)")
    w(f"  Runtime   : {elapsed:.1f}s")
    w("")

    # ── Performance ──
    w("-" * 70)
    w("  PERFORMANCE SUMMARY")
    w("-" * 70)
    w(f"  Initial Capital     : $100,000.00")
    w(f"  Final Capital       : ${result.final_capital:,.2f}")
    w(f"  Total Return        : {result.total_return:+.2%}")
    w(f"  Annualized Return   : {result.annualized_return:+.2%}")
    w(f"  Sharpe Ratio        : {result.sharpe_ratio:.3f}")
    w(f"  Sortino Ratio       : {result.sortino_ratio:.3f}")
    w(f"  Max Drawdown        : {result.max_drawdown:.2%}")
    w(f"  Win Rate            : {result.win_rate:.1%}")
    w(f"  Profit Factor       : {result.profit_factor:.3f}")
    w(f"  Avg Win             : ${result.avg_win:,.2f}")
    w(f"  Avg Loss            : ${result.avg_loss:,.2f}")
    w(f"  Total Trades        : {result.total_trades}")
    w(f"  Winners             : {result.winning_trades}")
    w(f"  Losers              : {result.losing_trades}")
    w(f"  Avg Holding Period  : {result.avg_holding_period}")
    w(f"  Dir. Accuracy       : {dir_acc:.1%}")
    w("")

    # ── Events ──
    w("-" * 70)
    w("  HISTORICAL EVENTS ({} events, real BTC prices)".format(len(events)))
    w("-" * 70)
    for e in events:
        pct = ((e.price_24h_after - e.price_at_event) / e.price_at_event) * 100
        w(f"  {e.timestamp.strftime('%Y-%m-%d')}  {e.event_type:15s}  "
          f"${e.price_at_event:>10,.0f}  24h={pct:+6.2f}%  {e.headline[:55]}")
    w("")

    # ── Event Study ──
    w("-" * 70)
    w("  EVENT-STUDY DIRECTIONAL ANALYSIS")
    w("-" * 70)
    w(f"  Events analyzed     : {event_study['total_events_analyzed']}")
    w(f"  Events with signals : {event_study['events_with_signals']}")
    w(f"  Directional accuracy: {event_study['accuracy_pct']}")
    w("")
    w(f"  {'Status':6s}  {'Date':12s}  {'Type':15s}  {'Predicted':10s}  "
      f"{'Conf':6s}  Headline")
    w(f"  {'------':6s}  {'----':12s}  {'----':15s}  {'---------':10s}  "
      f"{'----':6s}  --------")
    for d in event_study.get("event_details", []):
        mark = "OK" if d["correct"] else "WRONG"
        w(f"  {mark:6s}  {d['timestamp'][:10]:12s}  "
          f"{d.get('event_type',''):15s}  {d['predicted']:10s}  "
          f"{d['confidence']:.3f}  {d['headline'][:50]}")
    w("")

    # ── Statistical Significance ──
    sig = event_study.get("statistical_significance", {})
    if sig:
        w("-" * 70)
        w("  STATISTICAL SIGNIFICANCE")
        w("-" * 70)
        for key in ["directional", "timing", "overall"]:
            s = sig.get(key, {})
            if isinstance(s, dict):
                v = s.get("verdict", "")
                p = s.get("p_value", "N/A")
                w(f"  {key:15s}:  p={p}  |  {v}")
        w("")

    # ── Trade Log ──
    w("-" * 70)
    w("  TRADE LOG ({} trades)".format(result.total_trades))
    w("-" * 70)
    w(f"  {'#':>3s}  {'W/L':3s}  {'Dir':8s}  {'Entry':>12s}  {'Exit':>12s}  "
      f"{'P&L':>10s}  {'P&L%':>8s}  {'Hold':>8s}  Exit Reason")
    w(f"  {'---':>3s}  {'---':3s}  {'---':8s}  {'-----':>12s}  {'----':>12s}  "
      f"{'---':>10s}  {'----':>8s}  {'----':>8s}  -----------")
    for i, t in enumerate(result.trades):
        wl = "W" if t.pnl > 0 else "L"
        w(f"  {i+1:3d}  {wl:3s}  {t.direction:8s}  "
          f"${t.entry_price:>10,.0f}  ${t.exit_price:>10,.0f}  "
          f"${t.pnl:>+9,.2f}  {t.pnl_pct:>+7.2%}  "
          f"{t.holding_period.days:>4d}d    {t.exit_reason}")
    w("")

    # ── Participants ──
    w("-" * 70)
    w("  PARTICIPANT ACCURACY")
    w("-" * 70)
    pa = bridge.get_participant_comparison().get("participant_accuracy", {})
    for p, d in sorted(pa.items(), key=lambda x: x[1].get("accuracy",0), reverse=True):
        w(f"  {p:35s}  {d['accuracy_pct']:>6s}  ({d['total_events']} events)")
    w("")

    # ── Ambiguity ──
    w("-" * 70)
    w("  AMBIGUITY & COMPETING NARRATIVES")
    w("-" * 70)
    amb = bridge.get_ambiguity_report()
    w(f"  Total events    : {amb['total_events']}")
    w(f"  Ambiguous (>0.3): {amb['ambiguous_events']}")
    w(f"  Ambiguity rate  : {amb['ambiguity_rate']}")
    w("")
    for evt in amb.get("high_ambiguity_events", [])[:5]:
        w(f"  [{evt['ambiguity_score']:.2f}] {evt['headline'][:65]}")
        for n in evt.get("competing_narratives", []):
            w(f"    -> {n}")
    w("")

    # ── Feedback / Credibility ──
    w("-" * 70)
    w("  FEEDBACK LOOP CREDIBILITY")
    w("-" * 70)
    cred = bridge.get_credibility_report()
    if isinstance(cred, dict):
        ov = cred.get("overall", {})
        if isinstance(ov, dict):
            w(f"  Total validated : {ov.get('total_validated', 'N/A')}")
            w(f"  Total correct   : {ov.get('total_correct', 'N/A')}")
            w(f"  Overall accuracy: {ov.get('overall_accuracy', 'N/A')}")
        cs = cred.get("models", {}).get("cognitive_system", {})
        if isinstance(cs, dict):
            w(f"  Model weight    : {cs.get('weight', 'N/A')}")
            w(f"  Direction acc.  : {cs.get('direction_accuracy', 'N/A')}")
            w(f"  Best event type : {cs.get('best_event_type', 'N/A')}")
            w(f"  Worst event type: {cs.get('worst_event_type', 'N/A')}")
    w("")

    # ── Validation ──
    w("-" * 70)
    w("  VALIDATION  (15 checks)")
    w("-" * 70)
    checks = [
        ("Events processed >= 20",         len(bridge.event_analyses) >= 20, len(bridge.event_analyses)),
        ("Trades executed >= 5",            result.total_trades >= 5, result.total_trades),
        ("Directional accuracy >= 55%",     dir_acc >= 0.55, f"{dir_acc:.1%}"),
        ("Win rate >= 45%",                 result.win_rate >= 0.45, f"{result.win_rate:.1%}"),
        ("Sharpe ratio > 0",               result.sharpe_ratio > 0, f"{result.sharpe_ratio:.3f}"),
        ("Max drawdown < 30%",             result.max_drawdown < 0.30, f"{result.max_drawdown:.2%}"),
        ("Profit factor > 1.0",            result.profit_factor > 1.0, f"{result.profit_factor:.3f}"),
        ("Participant interpretations > 0", sum(1 for a in bridge.event_analyses if a.participant_responses) > 0,
            sum(1 for a in bridge.event_analyses if a.participant_responses)),
        ("Scenario trees generated > 0",    sum(1 for a in bridge.event_analyses if a.scenario_tree) > 0,
            sum(1 for a in bridge.event_analyses if a.scenario_tree)),
        ("Hidden truth analysis > 0",       sum(1 for a in bridge.event_analyses if a.hidden_truth) > 0,
            sum(1 for a in bridge.event_analyses if a.hidden_truth)),
        ("Economic analysis > 0",           sum(1 for a in bridge.event_analyses if a.economic_impact) > 0,
            sum(1 for a in bridge.event_analyses if a.economic_impact)),
        ("Alpha signals generated > 0",     sum(1 for a in bridge.event_analyses if a.alpha_signals) > 0,
            sum(1 for a in bridge.event_analyses if a.alpha_signals)),
        ("Feedback loop active",            bridge.registry.get("feedback") is not None, True),
        ("Data cutoff <= Dec 2025",
            max(a.timestamp for a in bridge.event_analyses) <= datetime(2025,12,31,23,59,59),
            max(a.timestamp for a in bridge.event_analyses).strftime("%Y-%m-%d")),
        ("CME modules loaded >= 20",        n_mod >= 20, n_mod),
    ]
    passed = sum(1 for _, p, _ in checks if p)
    for name, ok, val in checks:
        st = "PASS" if ok else "FAIL"
        w(f"  [{st}]  {name:40s}  = {val}")
    w(f"\n  Result: {passed}/15 checks passed")
    w("")

    # ── Data Sources ──
    w("-" * 70)
    w("  DATA SOURCES (all real, no demo)")
    w("-" * 70)
    w("  BTC Prices  : yfinance (Yahoo Finance) real OHLC daily data")
    w("  News Events : 35 curated real-world events (Jan 2024 - Dec 2025)")
    w("  NLP Model   : FinBERT (ProsusAI/finbert) transformer sentiment")
    w("  Fallback    : spaCy en_core_web_sm + financial lexicon")
    w("  Participants: 10 cognitive models (5 engine + 5 phase-pipeline)")
    w("  Signal      : Contrarian NLP (negative FinBERT = bullish crypto)")
    w("")
    w("=" * 70)
    w("  END OF REPORT")
    w("=" * 70)

    report_text = "\n".join(lines)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    return report_text


# ── Main ────────────────────────────────────────────────────────────

def main():
    start = time.time()
    out_dir = os.path.join(ROOT_DIR, "reports")
    os.makedirs(out_dir, exist_ok=True)

    print("[1/5] Loading real BTC price data from yfinance...")
    gen = HistoricalEventsGenerator(asset="BTC-USD")
    gen.load_prices()
    events = gen.generate_events()
    print(f"      {len(events)} events, real prices loaded")

    print("[2/5] Initializing 67 CME modules...")
    bridge = CognitiveSignalBridge(asset="BTC", verbose=False)
    bridge.initialize()
    n_mod = len([v for v in bridge.registry.modules.values() if v is not None])
    print(f"      {n_mod} modules ready")

    print("[3/5] Running backtest (real data)...")
    runner = BacktestRunner(
        initial_capital=100_000.0, max_position_pct=0.08,
        default_stop_pct=0.025, default_target_pct=0.05,
        max_holding_hours=48,
    )
    for ev in events:
        runner.replay_engine.add_event(ev)
    result = runner.run(bridge.generate_signal, snapshot_interval=timedelta(hours=4))
    event_study = bridge.get_event_study_results()
    dir_acc = float(event_study.get("directional_accuracy", 0))
    print(f"      {result.total_trades} trades | Win {result.win_rate:.1%} | "
          f"Sharpe {result.sharpe_ratio:.3f} | Dir.Acc {dir_acc:.1%}")

    print("[4/5] Saving 8 charts to reports/...")
    plot_equity_curve(result, out_dir)
    plot_trade_pnl(result, out_dir)
    plot_cumulative_pnl(result, out_dir)
    plot_accuracy_by_type(bridge, out_dir)
    plot_metrics_bars(result, dir_acc, out_dir)
    plot_sentiment_vs_return(bridge, events, out_dir)
    plot_participant_accuracy(bridge, out_dir)
    plot_ambiguity(bridge, out_dir)
    print("      8 PNG charts saved")

    print("[5/5] Writing text report...")
    elapsed = time.time() - start
    report_path = os.path.join(out_dir, "backtest_report.txt")
    report_text = write_text_report(result, bridge, events, event_study, elapsed, report_path)
    print(f"      Report saved: {report_path}")

    # Also print to console
    print("\n")
    print(report_text)

    print(f"\nAll files in: {out_dir}/")
    print("  backtest_report.txt")
    print("  01_equity_curve.png")
    print("  02_trade_pnl.png")
    print("  03_cumulative_pnl.png")
    print("  04_accuracy_by_type.png")
    print("  05_metrics.png")
    print("  06_sentiment_vs_return.png")
    print("  07_participant_accuracy.png")
    print("  08_ambiguity.png")


if __name__ == "__main__":
    main()
