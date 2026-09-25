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
You are a data engineering assistant. A SQL query failed in an automated
payment transaction reporting pipeline. Analyze the failure and respond
concisely in this exact format:

Root Cause: <one or two lines>
Affected Field: <column/field name if identifiable>
Suggested Fix: <one line, actionable>

Query Name: {query_name}
Error Message: {error_message}
Sample Data (if available): {sample_data}
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
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