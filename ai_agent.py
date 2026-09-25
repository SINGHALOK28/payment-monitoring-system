import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

def diagnose_failure(query_name, error_message, sample_data=None):
    """
    Sends the failure details to Groq and returns an AI-generated
    root cause diagnosis + suggested fix.
    """
    prompt = f"""
You are an expert data engineer debugging a failure in an automated
payment transaction reporting pipeline. A SQL query failed while running
against a PostgreSQL database. Carefully analyze the error message and
explain it clearly for someone reviewing this in a dashboard.

Respond in EXACTLY this format, nothing else:

🔍 What Went Wrong: <Explain in plain, simple language what happened — avoid just repeating the raw error. Describe it like you're explaining to someone who didn't see the error themselves.>

📍 Affected Field: <The exact column/field name involved, if identifiable from the error or query name>

⚠️ Why This Happened: <The likely real-world reason this bad data got in — e.g. wrong data type, missing validation, unexpected value from a source system>

✅ How To Fix It: <A specific, actionable step to fix THIS particular issue — mention the exact field and what value/type it should have instead. Be concrete, not generic.>

Query Name: {query_name}
Error Message: {error_message}
Sample Data (if available): {sample_data}

Keep the entire response under 120 words. Do not include any text outside the format above.
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.3
        )
        diagnosis = response.choices[0].message.content
        return diagnosis.strip()
    except Exception as e:
        return f"AI diagnosis unavailable: {str(e)}"


# Quick standalone test
if __name__ == "__main__":
    test_result = diagnose_failure(
        query_name="avg_risk_score",
        error_message="invalid input syntax for type numeric: 'N/A'",
        sample_data="{'risk_score': 'N/A', 'transaction_id': 4521}"
    )
    print(test_result)