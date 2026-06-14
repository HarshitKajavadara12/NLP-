"""
DASHBOARD APP — Streamlit dashboard for the Cognitive Market Engine.

Run with:
    streamlit run dashboard/app.py          (auto-bootstraps)
    python main.py --dashboard              (bootstrapped by main.py)

Displays:
- System status and pipeline metrics
- Active narratives and hidden truth alerts
- Correlation matrix heatmap
- Signal history and accuracy
- Scenario analysis
- Model credibility rankings
"""

import os
import sys
import json
from datetime import datetime

# Ensure project root is on path so standalone `streamlit run` works
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Graceful import
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def create_dashboard(pipeline=None, feedback_loop=None,
                     correlation_engine=None, storage=None):
    """
    Create and run the Streamlit dashboard.
    
    Args:
        pipeline: StreamingPipeline instance
        feedback_loop: FeedbackLoop instance
        correlation_engine: CorrelationEngine instance
        storage: DatabaseManager instance
    """
    if not HAS_STREAMLIT:
        print("[DASHBOARD] Streamlit not installed. Install with: pip install streamlit")
        return
    
    st.set_page_config(
        page_title="Cognitive Market Engine",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    st.title("🧠 Cognitive Market Engine — Dashboard")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("Controls")
        page = st.selectbox("View", [
            "System Overview",
            "Signal Monitor",
            "Model Credibility",
            "Correlation Matrix",
            "Scenario Analysis",
            "Hidden Truth Alerts",
            "News Feed",
        ])
        
        st.markdown("---")
        st.markdown(f"**Last refresh:** {datetime.now().strftime('%H:%M:%S')}")
        
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # ================================================================
    # PAGES
    # ================================================================
    
    if page == "System Overview":
        _render_overview(pipeline, feedback_loop, storage)
    elif page == "Signal Monitor":
        _render_signals(storage)
    elif page == "Model Credibility":
        _render_credibility(feedback_loop)
    elif page == "Correlation Matrix":
        _render_correlations(correlation_engine)
    elif page == "Scenario Analysis":
        _render_scenarios(storage)
    elif page == "Hidden Truth Alerts":
        _render_hidden_truth(storage)
    elif page == "News Feed":
        _render_news_feed(pipeline, storage)


def _render_overview(pipeline, feedback_loop, storage):
    """Render system overview page."""
    st.header("📊 System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Pipeline metrics
    if pipeline:
        metrics = pipeline.get_metrics()
        col1.metric("Events Processed", metrics.get("events_processed", 0))
        col2.metric("Avg Latency", f"{metrics.get('avg_latency_ms', 0):.1f} ms")
        col3.metric("Errors", metrics.get("errors", 0))
        col4.metric("Status", metrics.get("pipeline_status", "unknown"))
    else:
        col1.metric("Events Processed", "N/A")
        col2.metric("Avg Latency", "N/A")
        col3.metric("Errors", "N/A")
        col4.metric("Status", "No pipeline")
    
    st.markdown("---")
    
    # Model Performance Summary
    if feedback_loop:
        st.subheader("Model Performance")
        report = feedback_loop.get_credibility_report()
        
        overall = report.get("overall", {})
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Validated", overall.get("total_validated", 0))
        c2.metric("Total Correct", overall.get("total_correct", 0))
        c3.metric("Overall Accuracy",
                  f"{overall.get('overall_accuracy', 0):.1%}")
        
        # Model weights table
        models = report.get("models", {})
        if models and HAS_PANDAS:
            df = pd.DataFrame(models.values())
            if not df.empty:
                st.dataframe(
                    df[["name", "accuracy_ema", "weight",
                        "direction_accuracy", "total_predictions"]],
                    use_container_width=True,
                )
    
    # Storage stats
    if storage and hasattr(storage, "get_stats"):
        st.subheader("Storage Statistics")
        try:
            stats = storage.get_stats()
            st.json(stats)
        except Exception:
            st.info("Storage stats unavailable")


def _render_signals(storage):
    """Render signal monitor page."""
    st.header("📡 Signal Monitor")
    
    if not storage:
        st.info("No storage connected. Signals will appear here when the system is running.")
        return
    
    try:
        if hasattr(storage, "get_recent_signals"):
            signals = storage.get_recent_signals(limit=20)
            if signals and HAS_PANDAS:
                df = pd.DataFrame(signals)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No signals recorded yet.")
    except Exception as e:
        st.error(f"Error loading signals: {e}")


def _render_credibility(feedback_loop):
    """Render model credibility page."""
    st.header("🏆 Model Credibility Rankings")
    
    if not feedback_loop:
        st.info("No feedback loop connected.")
        return
    
    report = feedback_loop.get_credibility_report()
    
    # Rankings
    rankings = report.get("rankings", {})
    if rankings.get("by_accuracy"):
        st.subheader("Accuracy Rankings")
        for i, name in enumerate(rankings["by_accuracy"], 1):
            model = report["models"].get(name, {})
            acc = model.get("accuracy_ema", 0)
            weight = model.get("weight", 1.0)
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            st.write(f"{medal} **{name}** — Accuracy: {acc:.1%}, Weight: {weight:.2f}")
    
    # Calibration
    calibration = report.get("calibration", {})
    if calibration:
        st.subheader("Confidence Calibration")
        st.markdown("*How well does confidence match actual accuracy?*")
        if HAS_PANDAS:
            cal_df = pd.DataFrame([
                {
                    "Confidence Bin": k,
                    "Expected Accuracy": v["expected"],
                    "Actual Accuracy": v["avg_accuracy"],
                    "Count": v["count"],
                    "Deviation": v["deviation"],
                }
                for k, v in sorted(calibration.items())
            ])
            st.dataframe(cal_df, use_container_width=True)
    
    # Ensemble weights
    st.subheader("Current Ensemble Weights")
    weights = feedback_loop.get_ensemble_weights()
    if weights and HAS_PANDAS:
        wdf = pd.DataFrame([
            {"Model": k, "Weight": f"{v:.1%}"}
            for k, v in sorted(weights.items(), key=lambda x: -x[1])
        ])
        st.dataframe(wdf, use_container_width=True)


def _render_correlations(correlation_engine):
    """Render correlation matrix page."""
    st.header("🔗 Correlation Matrix")
    
    if not correlation_engine:
        st.info("No correlation engine connected.")
        return
    
    try:
        if hasattr(correlation_engine, "get_correlation_matrix"):
            matrix = correlation_engine.get_correlation_matrix()
            if matrix and HAS_PANDAS:
                assets = matrix.get("assets", [])
                values = matrix.get("values", [])
                if assets and values:
                    df = pd.DataFrame(values, index=assets, columns=assets)
                    st.dataframe(df.style.background_gradient(cmap="RdYlGn"),
                                use_container_width=True)
        
        # Anomalies
        if hasattr(correlation_engine, "detect_anomalies"):
            anomalies = correlation_engine.detect_anomalies()
            if anomalies:
                st.subheader("⚠️ Correlation Anomalies")
                for a in anomalies:
                    st.warning(f"{a.get('pair', '')}: {a.get('message', '')}")
    except Exception as e:
        st.error(f"Error loading correlations: {e}")


def _render_scenarios(storage):
    """Render scenario analysis page."""
    st.header("🌳 Scenario Analysis")
    
    if not storage:
        st.info("No storage connected.")
        return
    
    try:
        if hasattr(storage, "get_recent_scenarios"):
            scenarios = storage.get_recent_scenarios(limit=5)
            for s in scenarios:
                with st.expander(f"Scenario: {s.get('event_type', 'Unknown')}"):
                    st.json(s)
    except Exception:
        st.info("No scenarios recorded yet. Process news events to generate scenarios.")


def _render_hidden_truth(storage):
    """Render hidden truth alerts page."""
    st.header("🔍 Hidden Truth Detection")
    
    st.info("Hidden truth alerts appear here when cross-source analysis, "
            "omission detection, or suspicious timing patterns are found.")
    
    if storage and hasattr(storage, "get_recent_alerts"):
        try:
            alerts = storage.get_recent_alerts(limit=20)
            if alerts:
                for a in alerts:
                    severity = a.get("severity", "info")
                    msg = a.get("message", "")
                    if severity == "high":
                        st.error(f"🚨 {msg}")
                    elif severity == "medium":
                        st.warning(f"⚠️ {msg}")
                    else:
                        st.info(f"ℹ️ {msg}")
        except Exception:
            pass


def _render_news_feed(pipeline, storage):
    """Render news feed page with manual input."""
    st.header("📰 News Feed")
    
    # Manual input
    st.subheader("Process News Manually")
    news_text = st.text_area(
        "Enter news text:",
        height=100,
        placeholder="Federal Reserve raises interest rates by 25 basis points...",
    )
    source = st.text_input("Source:", value="manual")
    
    if st.button("🚀 Process"):
        if news_text and pipeline:
            result = pipeline.process_news(news_text, source=source)
            st.success(f"Processing started. Event ID: {result.get('event_id', 'N/A')}")
            st.json(result)
        elif not pipeline:
            st.error("No pipeline connected.")
        else:
            st.warning("Enter news text first.")
    
    # Recent events
    st.markdown("---")
    st.subheader("Recent Events")
    if storage and hasattr(storage, "search_news"):
        try:
            events = storage.search_news("", limit=10)
            if events and HAS_PANDAS:
                df = pd.DataFrame(events)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No events recorded yet.")
        except Exception:
            st.info("No events yet.")


# ================================================================
# CLI Entry Point
# ================================================================

if __name__ == "__main__":
    if HAS_STREAMLIT:
        # Auto-bootstrap when run standalone
        try:
            from main import bootstrap
            _components = bootstrap(verbose=False)
            create_dashboard(
                pipeline=_components.get("pipeline"),
                feedback_loop=_components.get("feedback"),
                correlation_engine=(_components.get("multi_asset") or {}).get("correlation"),
                storage=_components.get("storage"),
            )
        except ImportError:
            create_dashboard()
    else:
        print("Install streamlit: pip install streamlit")
        print("Then run: streamlit run dashboard/app.py")
