import os
import random
import psycopg2
from faker import Faker
from dotenv import load_dotenv
from datetime import datetime, timedelta

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
        "transaction_date": datetime.now() - timedelta(days=random.randint(0, 1))
    }

def generate_bad_transaction():
    """Chaos-injection: intentionally creates anomalous data"""
    txn = generate_normal_transaction()
    anomaly_type = random.choice(["bad_amount", "null_risk", "negative_amount", "bad_payment_method"])

    if anomaly_type == "bad_amount":
        txn["amount"] = "N/A"  # non-numeric value in numeric field
    elif anomaly_type == "null_risk":
        txn["risk_score"] = None
    elif anomaly_type == "negative_amount":
        txn["amount"] = -round(random.uniform(50, 500), 2)
    elif anomaly_type == "bad_payment_method":
        txn["payment_method"] = "CryptoTransfer"  # unexpected/unknown value

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

def generate_daily_batch(num_records=50, chaos_probability=0.12):
    conn = get_connection()
    success_count = 0
    bad_count = 0

    for _ in range(num_records):
        if random.random() < chaos_probability:
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
    print(f"Batch complete: {success_count} normal, {bad_count} chaos-injected records attempted")

if __name__ == "__main__":
    generate_daily_batch()