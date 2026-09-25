import os
import requests
from dotenv import load_dotenv

load_dotenv()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def send_slack_message(message):
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json={"text": message})
        if response.status_code != 200:
            print(f"Slack notification failed: {response.text}")
    except Exception as e:
        print(f"Slack notification error: {e}")


def build_success_message(report_data):
    total_txn, total_amount = report_data.get("total_sales", (0, 0))
    top_city = report_data.get("top_city", "N/A")
    top_payment = report_data.get("top_payment_method", "N/A")
    failed_count = report_data.get("failed_count", 0)

    return f"""✅ *Daily Payment Report*
Total Transactions: {total_txn} | Total Amount: ₹{total_amount}
Top City: {top_city} | Top Payment Method: {top_payment}
Failed Transactions: {failed_count}"""


def build_failure_message(failures):
    lines = ["⚠️ *Query Failures Detected*"]
    for f in failures:
        lines.append(f"""
Query: {f['query_name']}
Error: {f['error_message']}
AI Diagnosis: {f['ai_diagnosis']}""")
    return "\n".join(lines)


# Quick standalone test
if __name__ == "__main__":
    send_slack_message("🔔 Test message from Payment Monitoring System")