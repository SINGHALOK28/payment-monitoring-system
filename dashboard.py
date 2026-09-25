import os
import psycopg2
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime

# ---------- SETUP ----------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

st.set_page_config(
    page_title="Payment Monitoring Dashboard",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- CUSTOM CSS (visual polish only, no logic change) ----------
st.markdown("""
<style>
    /* Page background (correct selector for current Streamlit versions) */
    [data-testid="stAppViewContainer"] {
        background-color: #f7f8fa;
    }
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
    }

    /* Header */
    .dashboard-title {
        font-size: 2.1rem;
        font-weight: 800;
        margin-bottom: 0;
        background: linear-gradient(90deg, #4F46E5, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .dashboard-subtitle {
        color: #6b7280;
        font-size: 0.95rem;
        margin-top: -6px;
    }

    /* Metric cards — explicit text colors so they stay readable
       regardless of the viewer's light/dark Streamlit theme */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #eceff3;
        border-radius: 14px;
        padding: 16px 18px 14px 18px;
        box-shadow: 0 1px 3px rgba(16, 24, 40, 0.06);
    }
    div[data-testid="stMetricLabel"] > div {
        font-weight: 600 !important;
        color: #4b5563 !important;
    }
    div[data-testid="stMetricValue"] > div {
        font-weight: 700 !important;
        color: #111827 !important;
    }
    div[data-testid="stMetricDelta"] > div {
        font-weight: 600 !important;
    }

    /* Section headers */
    h3 {
        font-weight: 700 !important;
    }

    /* Make normal body text readable on the light background too */
    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] span,
    [data-testid="stAppViewContainer"] label {
        color: #1f2937;
    }

    /* Sidebar stays dark for contrast */
    section[data-testid="stSidebar"] {
        background-color: #111827;
    }
    section[data-testid="stSidebar"] * {
        color: #f3f4f6 !important;
    }

    /* Download / regular buttons — visible by default, not just on hover */
    div[data-testid="stDownloadButton"] button,
    div[data-testid="stButton"] button {
        background-color: #4F46E5 !important;
        color: #ffffff !important;
        border: 1px solid #4F46E5 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stDownloadButton"] button p,
    div[data-testid="stButton"] button p {
        color: #ffffff !important;
    }
    div[data-testid="stDownloadButton"] button:hover,
    div[data-testid="stButton"] button:hover {
        background-color: #4338CA !important;
        border-color: #4338CA !important;
        color: #ffffff !important;
    }
    div[data-testid="stDownloadButton"] button:focus,
    div[data-testid="stButton"] button:focus {
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.35) !important;
    }

    /* Inputs, dropdowns, search box, radio — consistent light styling
       with visible text, so they match the buttons/cards instead of
       inheriting the dark theme's near-invisible colors */
    div[data-testid="stTextInput"] input,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #111827 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
    }
    div[data-testid="stTextInput"] input::placeholder {
        color: #9ca3af !important;
    }
    div[data-testid="stSelectbox"] label,
    div[data-testid="stMultiSelect"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stRadio"] label,
    div[data-testid="stSlider"] label {
        color: #1f2937 !important;
        font-weight: 600 !important;
    }
    /* Dropdown menu + options list */
    div[data-baseweb="popover"] li,
    div[data-baseweb="popover"] div {
        color: #111827 !important;
    }
    div[data-baseweb="popover"] {
        background-color: #ffffff !important;
    }
    /* Radio button option text (e.g. "All reports" / "Single report") */
    div[data-testid="stRadio"] div[role="radiogroup"] label p {
        color: #1f2937 !important;
        font-weight: 500 !important;
    }
    /* Selected value text inside selectbox */
    div[data-testid="stSelectbox"] span,
    div[data-testid="stMultiSelect"] span {
        color: #111827 !important;
    }

    /* Sliders (Overview tab: date range, top-N cities) */
    div[data-testid="stSlider"] div[data-testid="stTickBarMin"],
    div[data-testid="stSlider"] div[data-testid="stTickBarMax"],
    div[data-testid="stSlider"] div[data-baseweb="slider"] div {
        color: #1f2937 !important;
    }
    div[data-testid="stThumbValue"] {
        color: #ffffff !important;
        background-color: #4F46E5 !important;
    }

    /* Expanders (e.g. "Show transaction count trend", "View all fields") */
    div[data-testid="stExpander"] summary {
        background-color: #ffffff !important;
        border-radius: 8px !important;
    }
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span {
        color: #111827 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
        background-color: #ffffff !important;
    }

    /* Captions (tab descriptions, "Showing N of M rows", timestamps, etc.) */
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p {
        color: #6b7280 !important;
    }

    /* Tab labels (Overview / Raw Data / Failures & AI Diagnosis / History) */
    button[data-baseweb="tab"] p {
        color: #374151 !important;
        font-weight: 600 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #4F46E5 !important;
    }

    /* Info / success / warning / error boxes text */
    div[data-testid="stAlert"] p {
        color: #111827 !important;
    }

    /* Status pill */
    .status-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .status-ok { background: #dcfce7; color: #166534; }
    .status-bad { background: #fee2e2; color: #991b1b; }

    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def get_connection():
    return psycopg2.connect(DATABASE_URL)

# ---------- DATA FETCH FUNCTIONS (UNCHANGED LOGIC) ----------
# Wrapped with st.cache_data so repeated renders/tab switches don't
# re-hit the DB every time. TTL keeps data reasonably fresh.

@st.cache_data(ttl=60, show_spinner=False)
def fetch_reports():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM reports ORDER BY report_date DESC;", conn)
    conn.close()
    return df

@st.cache_data(ttl=60, show_spinner=False)
def fetch_failure_logs():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM failure_logs ORDER BY failure_date DESC;", conn)
    conn.close()
    return df

@st.cache_data(ttl=60, show_spinner=False)
def fetch_transactions_summary():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT transaction_date::date AS date, COUNT(*) AS total_txns, SUM(amount::NUMERIC) AS total_amount
        FROM transactions
        WHERE amount ~ '^-?[0-9]+(\\.[0-9]+)?$'
        GROUP BY transaction_date::date
        ORDER BY date ASC;
    """, conn)
    conn.close()
    return df

@st.cache_data(ttl=60, show_spinner=False)
def fetch_city_distribution():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT city, COUNT(*) AS txn_count
        FROM transactions
        GROUP BY city
        ORDER BY txn_count DESC;
    """, conn)
    conn.close()
    return df

@st.cache_data(ttl=60, show_spinner=False)
def fetch_payment_method_distribution():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT payment_method, COUNT(*) AS usage_count
        FROM transactions
        GROUP BY payment_method
        ORDER BY usage_count DESC;
    """, conn)
    conn.close()
    return df

@st.cache_data(ttl=60, show_spinner=False)
def fetch_raw_transactions():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM transactions ORDER BY transaction_date DESC LIMIT 500;", conn)
    conn.close()
    return df


# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### 💳 Payment Monitor")
    st.caption("AI-powered reporting & anomaly diagnosis")
    st.divider()

    if st.button("🔄 Refresh data now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    auto_refresh = st.toggle("Auto-refresh every 60s", value=False)
    if auto_refresh:
        st.caption("Dashboard will auto-refresh.")

    st.divider()
    st.caption(f"Last loaded: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")

if auto_refresh:
    # Lightweight auto-refresh without extra dependencies
    st.markdown('<meta http-equiv="refresh" content="60">', unsafe_allow_html=True)


# ---------- HEADER ----------
st.markdown('<p class="dashboard-title">💳 Payment Transaction Monitoring Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="dashboard-subtitle">AI-powered daily reporting and anomaly diagnosis system</p>', unsafe_allow_html=True)
st.write("")

# ---------- KPI CARDS ----------
try:
    reports_df = fetch_reports()
    if not reports_df.empty:
        latest = reports_df.iloc[0]
        prev = reports_df.iloc[1] if len(reports_df) > 1 else None

        def delta(col, is_currency=False):
            if prev is None or pd.isnull(prev[col]) or pd.isnull(latest[col]):
                return None
            diff = latest[col] - prev[col]
            return f"₹{diff:,.0f}" if is_currency else f"{diff:,.0f}"

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric(
            "Total Transactions",
            int(latest["total_transactions"]) if pd.notnull(latest["total_transactions"]) else "N/A",
            delta=delta("total_transactions"),
        )
        col2.metric(
            "Total Amount",
            f"₹{latest['total_amount']:,.2f}" if pd.notnull(latest["total_amount"]) else "N/A",
            delta=delta("total_amount", is_currency=True),
        )
        col3.metric("Top City", latest["top_city"] if pd.notnull(latest["top_city"]) else "N/A")
        col4.metric("Top Payment Method", latest["top_payment_method"] if pd.notnull(latest["top_payment_method"]) else "N/A")
        col5.metric(
            "Failed Transactions",
            int(latest["failed_count"]) if pd.notnull(latest["failed_count"]) else "N/A",
            delta=delta("failed_count"),
            delta_color="inverse",
        )


# ---------- TABS ----------
tab_overview, tab_data, tab_failures, tab_history = st.tabs(
    ["📈 Overview", "📋 Raw Data", "⚠️ Failures & AI Diagnosis", "🕒 Report History"]
)

# ----- OVERVIEW TAB -----
with tab_overview:
    st.subheader("📈 Sales Trend")
    try:
        trend_df = fetch_transactions_summary()
        if not trend_df.empty:
            unique_dates = sorted(trend_df["date"].unique())
            date_min, date_max = unique_dates[0], unique_dates[-1]

            if len(unique_dates) > 1:
                date_range = st.slider(
                    "Filter date range",
                    min_value=date_min, max_value=date_max,
                    value=(date_min, date_max),
                    format="DD MMM",
                )
                filtered_trend = trend_df[(trend_df["date"] >= date_range[0]) & (trend_df["date"] <= date_range[1])]
            else:
                # Only one day of data — a slider has nothing to filter,
                # so just show that day's numbers instead of a broken slider.
                st.caption(f"Only one day of data available so far: {date_min}")
                filtered_trend = trend_df

            c1, c2 = st.columns(2)
            c1.metric("Txns in range", int(filtered_trend["total_txns"].sum()))
            c2.metric("Amount in range", f"₹{filtered_trend['total_amount'].sum():,.2f}")

            st.line_chart(filtered_trend.set_index("date")["total_amount"])
            with st.expander("Show transaction count trend"):
                st.bar_chart(filtered_trend.set_index("date")["total_txns"])
        else:
            st.info("No transaction data available yet.")
    except Exception as e:
        st.error(f"Could not load sales trend: {e}")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🏙️ City-wise Transactions")
        try:
            city_df = fetch_city_distribution()
            if not city_df.empty:
                top_n = st.slider("Show top N cities", 3, min(20, len(city_df)), min(10, len(city_df)))
                st.bar_chart(city_df.set_index("city")["txn_count"].head(top_n))
            else:
                st.info("No city data available.")
        except Exception as e:
            st.error(f"Could not load city data: {e}")

    with col_b:
        st.subheader("💳 Payment Method Split")
        try:
            pm_df = fetch_payment_method_distribution()
            if not pm_df.empty:
                st.bar_chart(pm_df.set_index("payment_method")["usage_count"])
            else:
                st.info("No payment method data available.")
        except Exception as e:
            st.error(f"Could not load payment method data: {e}")

# ----- RAW DATA TAB -----
with tab_data:
    st.subheader("📋 Raw Transaction Data (latest 500)")
    try:
        raw_df = fetch_raw_transactions()

        # Quick status metrics — transaction-level "Failed" status is normal
        # business/chaos-injected data (not a pipeline crash), so it lives
        # here rather than in the Failure Log & AI Diagnosis tab.
        if "transaction_status" in raw_df.columns:
            status_counts = raw_df["transaction_status"].value_counts()
            m1, m2, m3 = st.columns(3)
            m1.metric("Total (latest 500)", len(raw_df))
            m2.metric("✅ Success", int(status_counts.get("Success", 0)))
            m3.metric("❌ Transaction Failed", int(status_counts.get("Failed", 0)))
            st.write("")

        search_col, filter_col, status_col = st.columns([2, 1, 1])
        with search_col:
            search_term = st.text_input("🔍 Search in table (any column)", "")
        with filter_col:
            if "payment_method" in raw_df.columns:
                methods = ["All"] + sorted(raw_df["payment_method"].dropna().unique().tolist())
                method_filter = st.selectbox("Filter by payment method", methods)
            else:
                method_filter = "All"
        with status_col:
            if "transaction_status" in raw_df.columns:
                statuses = ["All"] + sorted(raw_df["transaction_status"].dropna().unique().tolist())
                status_filter = st.selectbox("Filter by status", statuses)
            else:
                status_filter = "All"

        display_df = raw_df.copy()
        if method_filter != "All":
            display_df = display_df[display_df["payment_method"] == method_filter]
        if status_filter != "All":
            display_df = display_df[display_df["transaction_status"] == status_filter]
        if search_term:
            mask = display_df.astype(str).apply(lambda row: row.str.contains(search_term, case=False, na=False)).any(axis=1)
            display_df = display_df[mask]

        st.caption(f"Showing {len(display_df)} of {len(raw_df)} rows")
        st.dataframe(display_df, use_container_width=True, height=420)

        csv_raw = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Transactions (CSV)",
            data=csv_raw,
            file_name="raw_transactions.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Could not load raw transactions: {e}")

# ----- FAILURES TAB -----
# Scope: this tab is strictly about PIPELINE-level failures — i.e. cases
# where the automation script/SQL query itself errored out and Groq AI
# was invoked to diagnose the root cause (per the architecture doc).
# It reads only the `failure_logs` table. Transaction-level "Failed"
# status rows are normal chaos-injected business data and are shown in
# the Raw Data tab instead, not here.
with tab_failures:
    st.subheader("⚠️ Failure Log & AI Diagnosis")
    st.caption("Pipeline/query execution failures diagnosed by the Groq AI agent — not individual failed payment transactions (see Raw Data tab for those).")
    try:
        failure_df = fetch_failure_logs()
        if failure_df.empty:
            st.success("✅ No pipeline failures recorded yet — every run completed successfully.")
        else:
            for _, row in failure_df.iterrows():
                with st.expander(f"🔴 {row['query_name']} — {row['failure_date']}"):
                    st.markdown(f"**Error:** `{row['error_message']}`")
                    st.markdown("---")
                    st.markdown(row['ai_diagnosis'])

            st.divider()
            st.dataframe(failure_df, use_container_width=True, height=300)
            csv_failures = failure_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Failure Log (CSV)",
                data=csv_failures,
                file_name="failure_logs.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.error(f"Could not load failure logs: {e}")

# ----- REPORT HISTORY TAB -----
with tab_history:
    st.subheader("🕒 Report History")
    try:
        if not reports_df.empty:
            view_mode = st.radio(
                "View mode",
                ["📋 All reports (table)", "🔎 Single report (detail view)"],
                horizontal=True,
            )

            if view_mode == "📋 All reports (table)":
                st.dataframe(reports_df, use_container_width=True, height=420)
                csv_reports = reports_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Report History (CSV)",
                    data=csv_reports,
                    file_name="report_history.csv",
                    mime="text/csv"
                )

            else:
                # Build a readable label for each report row to pick from
                if "report_date" in reports_df.columns:
                    labels = reports_df["report_date"].astype(str)
                else:
                    labels = reports_df.index.astype(str)

                selected_label = st.selectbox(
                    "Select a report to view",
                    options=labels,
                    index=0,
                )
                selected_row = reports_df[labels == selected_label].iloc[0]

                st.markdown(f"#### Report — {selected_label}")

                r1, r2, r3 = st.columns(3)
                if "total_transactions" in selected_row and pd.notnull(selected_row["total_transactions"]):
                    r1.metric("Total Transactions", int(selected_row["total_transactions"]))
                if "total_amount" in selected_row and pd.notnull(selected_row["total_amount"]):
                    r2.metric("Total Amount", f"₹{selected_row['total_amount']:,.2f}")
                if "failed_count" in selected_row and pd.notnull(selected_row["failed_count"]):
                    r3.metric("Failed Transactions", int(selected_row["failed_count"]))

                r4, r5 = st.columns(2)
                if "top_city" in selected_row and pd.notnull(selected_row["top_city"]):
                    r4.metric("Top City", selected_row["top_city"])
                if "top_payment_method" in selected_row and pd.notnull(selected_row["top_payment_method"]):
                    r5.metric("Top Payment Method", selected_row["top_payment_method"])

                with st.expander("View all fields for this report"):
                    st.dataframe(
                        selected_row.to_frame(name="value"),
                        use_container_width=True,
                    )

                csv_single = selected_row.to_frame().T.to_csv(index=False)
                st.download_button(
                    label="📥 Download This Report (CSV)",
                    data=csv_single,
                    file_name=f"report_{selected_label}.csv",
                    mime="text/csv",
                )

                # Quick prev/next navigation between reports
                idx_list = list(labels)
                current_idx = idx_list.index(selected_label)
                nav_prev, nav_info, nav_next = st.columns([1, 2, 1])
                with nav_prev:
                    st.caption("⬅️ Newer reports are lower index" if current_idx == 0 else "")
                with nav_info:
                    st.caption(f"Report {current_idx + 1} of {len(idx_list)}")
        else:
            st.info("No report history yet.")
    except Exception as e:
        st.error(f"Could not load report history: {e}")

st.divider()
st.caption("Built with Streamlit · Data refreshes from PostgreSQL")