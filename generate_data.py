import os
import random
import psycopg2
import pytz
from faker import Faker
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

fake = Faker('en_IN')  # Indian locale for realistic names/cities

cities = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Pune", "Kolkata"]
merchants = {
    "E-commerce": ["Amazon", "Flipkart", "Myntra"],
    "Food": ["Swiggy", "Zomato", "EatSure"],
    "Travel": ["MakeMyTrip", "IRCTC", "RedBus"],
    "Utilities": ["Airtel", "Jio", "BSES"]
}
payment_methods = ["UPI", "Credit Card", "Debit Card", "Wallet", "Net Banking"]
statuses = ["Success", "Failed", "Pending"]
transaction_types = ["Debit", "Credit", "Refund"]
device_types = ["Mobile", "Web"]

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def generate_normal_transaction():
    category = random.choice(list(merchants.keys()))
    merchant = random.choice(merchants[category])
    return {
        "user_id": random.randint(1000, 9999),
        "merchant_name": merchant,
        "merchant_category": category,
        "amount": round(random.uniform(50, 5000), 2),
        "currency": "INR",
        "payment_method": random.choice(payment_methods),
        "transaction_status": random.choices(statuses, weights=[85, 10, 5])[0],
        "transaction_type": random.choice(transaction_types),
        "city": random.choice(cities),
        "device_type": random.choice(device_types),
        "risk_score": round(random.uniform(0.01, 0.5), 2),
        "transaction_date": datetime.now(pytz.timezone("Asia/Kolkata"))
    }

def generate_bad_transaction():
    """Chaos-injection: only uses anomaly types that genuinely trigger a query failure
    (amount and risk_score are the only fields cast to NUMERIC in main.py's queries)"""
    txn = generate_normal_transaction()

    anomaly_type = random.choice([
        "amount_as_text",
        "risk_score_as_text",
    ])

    if anomaly_type == "amount_as_text":
        txn["amount"] = random.choice(["N/A", "unknown", "ERROR", "pending"])
    elif anomaly_type == "risk_score_as_text":
        txn["risk_score"] = random.choice(["high", "N/A", "???"])

    return txn


def insert_transaction(conn, txn):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions
        (user_id, merchant_name, merchant_category, amount, currency, payment_method,
         transaction_status, transaction_type, city, device_type, risk_score, transaction_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        txn["user_id"], txn["merchant_name"], txn["merchant_category"], txn["amount"],
        txn["currency"], txn["payment_method"], txn["transaction_status"], txn["transaction_type"],
        txn["city"], txn["device_type"], txn["risk_score"], txn["transaction_date"]
    ))
    conn.commit()
    cur.close()

def generate_daily_batch(num_records=50, chaos_probability=0.20, max_bad_records=1):
    conn = get_connection()
    success_count = 0
    bad_count = 0

    # Decide ONCE for the whole batch: is today a "chaos day" or a "clean day"?
    is_chaos_day = random.random() < chaos_probability

    # Agar chaos day hai, toh sirf 1 (ya max_bad_records tak) record ko bad banao
    bad_indices = set()
    if is_chaos_day:
        num_bad = random.randint(1, max_bad_records)
        bad_indices = set(random.sample(range(num_records), num_bad))

    for i in range(num_records):
        if i in bad_indices:
            txn = generate_bad_transaction()
            bad_count += 1
        else:
            txn = generate_normal_transaction()
            success_count += 1

        try:
            insert_transaction(conn, txn)
        except Exception as e:
            print(f"Insert failed (expected for some bad data): {e}")
            conn.rollback()

    conn.close()
    print(f"Batch complete: {success_count} normal, {bad_count} chaos-injected records. Chaos day: {is_chaos_day}")

if __name__ == "__main__":
    generate_daily_batch()