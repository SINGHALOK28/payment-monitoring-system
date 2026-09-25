import os
import psycopg2
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# ---------- SETUP ----------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

st.set_page_config(page_title="Payment Monitoring Dashboard", layout="wide")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

# ---------- DATA FETCH FUNCTIONS ----------

def fetch_reports():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM reports ORDER BY report_date DESC;", conn)
    conn.close()
    return df

def fetch_failure_logs():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM failure_logs ORDER BY failure_date DESC;", conn)
    conn.close()
    return df

def fetch_transactions_summary():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT transaction_date::date AS date, COUNT(*) AS total_txns, SUM(amount) AS total_amount
        FROM transactions
        WHERE amount IS NOT NULL
        GROUP BY transaction_date::date
        ORDER BY date ASC;
    """, conn)
    conn.close()
    return df

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

def fetch_raw_transactions():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM transactions ORDER BY transaction_date DESC LIMIT 500;", conn)
    conn.close()
    return df

# ---------- HEADER ----------

st.title("💳 Payment Transaction Monitoring Dashboard")
st.caption("AI-powered daily reporting and anomaly diagnosis system")

# ---------- KPI CARDS ----------

try:
    reports_df = fetch_reports()
    if not reports_df.empty:
        latest = reports_df.iloc[0]
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Transactions", int(latest["total_transactions"]) if pd.notnull(latest["total_transactions"]) else "N/A")
        col2.metric("Total Amount", f"₹{latest['total_amount']:,.2f}" if pd.notnull(latest["total_amount"]) else "N/A")
        col3.metric("Top City", latest["top_city"] if pd.notnull(latest["top_city"]) else "N/A")
        col4.metric("Top Payment Method", latest["top_payment_method"] if pd.notnull(latest["top_payment_method"]) else "N/A")
        col5.metric("Failed Transactions", int(latest["failed_count"]) if pd.notnull(latest["failed_count"]) else "N/A")
    else:
        st.info("No reports generated yet. Run the pipeline at least once.")
except Exception as e:
    st.error(f"Could not load KPI data: {e}")

st.divider()

# ---------- CHARTS ----------

st.subheader("📈 Sales Trend")
try:
    trend_df = fetch_transactions_summary()
    if not trend_df.empty:
        st.line_chart(trend_df.set_index("date")["total_amount"])
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
            st.bar_chart(city_df.set_index("city")["txn_count"])
    except Exception as e:
        st.error(f"Could not load city data: {e}")

with col_b:
    st.subheader("💳 Payment Method Split")
    try:
        pm_df = fetch_payment_method_distribution()
        if not pm_df.empty:
            st.bar_chart(pm_df.set_index("payment_method")["usage_count"])
    except Exception as e:
        st.error(f"Could not load payment method data: {e}")

st.divider()

# ---------- RAW DATA TABLE ----------

st.subheader("📋 Raw Transaction Data (latest 500)")
try:
    raw_df = fetch_raw_transactions()
    st.dataframe(raw_df, use_container_width=True)

    csv_raw = raw_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Raw Transactions (CSV)",
        data=csv_raw,
        file_name="raw_transactions.csv",
        mime="text/csv"
    )
except Exception as e:
    st.error(f"Could not load raw transactions: {e}")

st.divider()

# ---------- FAILURE LOG + AI DIAGNOSIS ----------

st.subheader("⚠️ Failure Log & AI Diagnosis")
try:
    failure_df = fetch_failure_logs()
    if failure_df.empty:
        st.success("✅ No failures recorded yet.")
    else:
        st.dataframe(failure_df, use_container_width=True)
        csv_failures = failure_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Failure Log (CSV)",
            data=csv_failures,
            file_name="failure_logs.csv",
            mime="text/csv"
        )
except Exception as e:
    st.error(f"Could not load failure logs: {e}")

st.divider()

# ---------- RUN HISTORY ----------

st.subheader("🕒 Report History")
try:
    if not reports_df.empty:
        st.dataframe(reports_df, use_container_width=True)
        csv_reports = reports_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Report History (CSV)",
            data=csv_reports,
            file_name="report_history.csv",
            mime="text/csv"
        )
    else:
        st.info("No report history yet.")
except Exception as e:
    st.error(f"Could not load report history: {e}")