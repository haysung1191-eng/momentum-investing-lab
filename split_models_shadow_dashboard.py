from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
SHADOW_DIR = ROOT / "output" / "split_models_shadow"
ARCHIVE_DIR = ROOT / "output" / "split_models_shadow_archive"


st.set_page_config(
    page_title="Split Models Shadow Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=60)
def _load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


@st.cache_data(ttl=60)
def _load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def _metric_pct(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):.2%}"


def _metric_float(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):.4f}"


def _metric_money(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):,.0f}"


def _badge(label: str, value: str) -> str:
    color = {
        "GO": "green",
        "PASS": "green",
        "HOLD": "orange",
        "FAIL": "red",
    }.get(str(value), "gray")
    return f"**{label}:** :{color}[`{value}`]"


def _load_optional_archive_manifest() -> pd.DataFrame:
    path = ARCHIVE_DIR / "archive_manifest.csv"
    if not path.exists():
        return pd.DataFrame()
    return _load_csv(str(path))


def _load_optional_archive_delta() -> dict:
    path = ARCHIVE_DIR / "archive_latest_delta.json"
    if not path.exists():
        return {}
    return _load_json(str(path))


def render_header(summary: dict, readiness: dict, drift: dict) -> None:
    st.title("Split Models Shadow Dashboard")
    st.markdown(
        " | ".join(
            [
                _badge("Baseline", summary.get("baseline_variant", "N/A")),
                _badge("Readiness", readiness.get("live_readiness_verdict", "N/A")),
                _badge("Drift", drift.get("drift_verdict", "N/A")),
                _badge("Health", summary.get("health_verdict", "N/A")),
            ]
        )
    )
    st.caption(
        f"Recent window: {summary.get('recent_start', 'N/A')} to {summary.get('recent_end', 'N/A')} | "
        f"Holdings: {summary.get('current_holdings', 'N/A')} | "
        f"Dominant sector: {summary.get('current_dominant_sector', 'N/A')}"
    )


def render_metrics(backtest: dict, summary: dict, readiness: dict, transition: dict) -> None:
    cols = st.columns(4)
    cols[0].metric("CAGR", _metric_pct(backtest.get("CAGR")))
    cols[1].metric("MDD", _metric_pct(backtest.get("MDD")))
    cols[2].metric("Sharpe", _metric_float(backtest.get("Sharpe")))
    cols[3].metric("Annual Turnover", _metric_float(backtest.get("AnnualTurnover")))

    cols = st.columns(4)
    cols[0].metric("Recent CAGR Proxy", _metric_pct(summary.get("recent_cagr_proxy")))
    cols[1].metric("Recent Avg Turnover", _metric_float(summary.get("recent_avg_turnover")))
    cols[2].metric("Transition Turnover", _metric_pct(transition.get("weight_turnover")))
    cols[3].metric("Actionable Rows", str(readiness.get("actionable_rows", "N/A")))


def render_readiness_checks(readiness: dict) -> None:
    st.subheader("Readiness Checks")
    checks = pd.DataFrame(readiness.get("checks", []))
    if checks.empty:
        st.info("No readiness checks available.")
        return
    st.dataframe(checks, width="stretch", height=280)


def render_orders(market_summary: pd.DataFrame, orders: pd.DataFrame) -> None:
    st.subheader("Execution Summary")
    left, right = st.columns([1, 2])
    with left:
        st.dataframe(market_summary, width="stretch", height=220)
    with right:
        actionable = orders[orders["ExecutionSide"] != "HOLD"].copy()
        st.dataframe(actionable, width="stretch", height=320)


def render_current_book(book: pd.DataFrame, sector_mix: pd.DataFrame) -> None:
    st.subheader("Current Book")
    left, right = st.columns([2, 1])
    with left:
        st.dataframe(book, width="stretch", height=320)
    with right:
        st.dataframe(sector_mix, width="stretch", height=220)


def render_archive(manifest: pd.DataFrame) -> None:
    st.subheader("Operator Archive")
    if manifest.empty:
        st.info("No archived handoff runs yet.")
        return
    display = manifest.copy()
    if "RunId" in display.columns:
        display = display.sort_values("RunId", ascending=False)
    st.dataframe(display, width="stretch", height=240)


def render_archive_delta(delta: dict) -> None:
    st.subheader("Latest Archive Delta")
    if not delta:
        st.info("No archive delta found.")
        return
    if not delta.get("comparison_available", False):
        st.info("Archive delta needs at least two handoff runs.")
        return

    left, right, third = st.columns(3)
    left.metric("Latest Run", str(delta.get("latest_run_id", "N/A")))
    right.metric("Prior Run", str(delta.get("prior_run_id", "N/A")))
    third.metric("Holdings Change", str(delta.get("holdings_change", "N/A")))

    change_flags = [
        ("Baseline Changed", bool(delta.get("baseline_variant_changed", False))),
        ("Readiness Changed", bool(delta.get("live_readiness_changed", False))),
        ("Operator Gate Changed", bool(delta.get("operator_gate_changed", False))),
        ("Health Changed", bool(delta.get("health_changed", False))),
        ("Drift Changed", bool(delta.get("drift_changed", False))),
        ("Sector Changed", bool(delta.get("dominant_sector_changed", False))),
    ]
    st.markdown(
        " | ".join(
            [
                _badge(label, "YES" if changed else "NO")
                for label, changed in change_flags
            ]
        )
    )
    st.caption(
        f"Transition turnover change: {float(delta.get('transition_turnover_change', 0.0)):.6f}"
    )
    st.code(json.dumps(delta, indent=2), language="json")


def render_packet(packet_path: Path) -> None:
    st.subheader("Operator Packet")
    if not packet_path.exists():
        st.info("No operator packet found.")
        return
    st.code(packet_path.read_text(encoding="utf-8"), language="markdown")


def main() -> None:
    st.sidebar.header("Controls")
    if st.sidebar.button("Refresh"):
        st.cache_data.clear()

    summary = _load_json(str(SHADOW_DIR / "shadow_summary.json"))
    backtest_summary = _load_json(str(SHADOW_DIR / "split_models_backtest_summary.json"))
    readiness = _load_json(str(SHADOW_DIR / "shadow_live_readiness.json"))
    drift = _load_json(str(SHADOW_DIR / "shadow_drift_report.json"))
    transition = _load_json(str(SHADOW_DIR / "shadow_live_transition_summary.json"))
    market_summary = _load_csv(str(SHADOW_DIR / "shadow_rebalance_market_summary.csv"))
    orders = _load_csv(str(SHADOW_DIR / "shadow_rebalance_orders.csv"))
    book = _load_csv(str(SHADOW_DIR / "shadow_current_book.csv"))
    sector_mix = _load_csv(str(SHADOW_DIR / "shadow_current_sector_mix.csv"))
    archive_manifest = _load_optional_archive_manifest()
    archive_delta = _load_optional_archive_delta()
    packet_path = SHADOW_DIR / "shadow_live_transition_packet.md"

    render_header(summary, readiness, drift)
    render_metrics(backtest_summary.get("trading_book", {}), summary, readiness, transition)

    tab1, tab2, tab3, tab4 = st.tabs(["Readiness", "Orders", "Current Book", "Archive"])
    with tab1:
        render_readiness_checks(readiness)
        render_packet(packet_path)
    with tab2:
        render_orders(market_summary, orders)
    with tab3:
        render_current_book(book, sector_mix)
    with tab4:
        render_archive_delta(archive_delta)
        render_archive(archive_manifest)


if __name__ == "__main__":
    main()
