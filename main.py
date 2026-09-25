import os
import logging
import psycopg2
import pandas as pd
from dotenv import load_dotenv
from ai_agent import diagnose_failure
from notify import send_slack_message, build_success_message, build_failure_message

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

logging.basicConfig(
    filename="logs.txt",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def get_total_sales(conn):
    query = """
        SELECT COUNT(*) AS total_transactions, SUM(amount) AS total_amount
        FROM transactions
        WHERE transaction_date::date = CURRENT_DATE - 1
        AND amount IS NOT NULL;
    """
    df = pd.read_sql(query, conn)
    return df.iloc[0]["total_transactions"], df.iloc[0]["total_amount"]

def get_top_city(conn):
    query = """
        SELECT city, COUNT(*) AS txn_count
        FROM transactions
        GROUP BY city
        ORDER BY txn_count DESC
        LIMIT 1;
    """
    df = pd.read_sql(query, conn)
    if df.empty:
        return None
    return df.iloc[0]["city"]

def get_top_payment_method(conn):
    query = """
        SELECT payment_method, COUNT(*) AS usage_count
        FROM transactions
        GROUP BY payment_method
        ORDER BY usage_count DESC
        LIMIT 1;
    """
    df = pd.read_sql(query, conn)
    if df.empty:
        return None
    return df.iloc[0]["payment_method"]

def get_failed_count(conn):
    query = """
        SELECT COUNT(*) AS failed_count
        FROM transactions
        WHERE transaction_status = 'Failed';
    """
    df = pd.read_sql(query, conn)
    return int(df.iloc[0]["failed_count"])

def get_avg_risk_score(conn):
    query = """
        SELECT AVG(risk_score) AS avg_risk_score
        FROM transactions
        WHERE risk_score IS NOT NULL;
    """
    df = pd.read_sql(query, conn)
    return df.iloc[0]["avg_risk_score"]

def save_failure_log(conn, query_name, error_message, ai_diagnosis):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO failure_logs (query_name, error_message, ai_diagnosis)
        VALUES (%s, %s, %s)
    """, (query_name, error_message, ai_diagnosis))
    conn.commit()
    cur.close()

def run_daily_report():
    conn = get_connection()
    report_data = {}
    failures = []

    tasks = {
        "total_sales": get_total_sales,
        "top_city": get_top_city,
        "top_payment_method": get_top_payment_method,
        "failed_count": get_failed_count,
        "avg_risk_score": get_avg_risk_score,
    }

    for name, func in tasks.items():
        try:
            result = func(conn)
            report_data[name] = result
            logging.info(f"Query '{name}' succeeded: {result}")

        except Exception as e:
            error_message = str(e)
            logging.error(f"Query '{name}' failed: {error_message}")

            ai_diagnosis = diagnose_failure(
                query_name=name,
                error_message=error_message
            )
            logging.info(f"AI Diagnosis for '{name}': {ai_diagnosis}")

            failures.append({
                "query_name": name,
                "error_message": error_message,
                "ai_diagnosis": ai_diagnosis
            })

            conn.rollback()
            save_failure_log(conn, name, error_message, ai_diagnosis)

    conn.close()

    print("---- Report Data ----")
    print(report_data)

    if failures:
        print("---- Failures ----")
        print(failures)

    if failures:
        slack_msg = build_failure_message(failures)
    else:
        slack_msg = build_success_message(report_data)

    send_slack_message(slack_msg)

    return report_data, failures

if __name__ == "__main__":
    run_daily_report()