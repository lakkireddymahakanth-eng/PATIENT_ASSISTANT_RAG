import ollama


def analyze_medical_report(report_text):

    prompt = f"""
You are a medical assistant helping summarize patient reports.

Analyze the following medical report and produce a clear summary.

Report:
{report_text}

Provide output in this format:

Key Findings:
- finding 1
- finding 2

Possible Concerns:
- concern 1
- concern 2

Recommendations:
- recommendation 1
- recommendation 2
"""

    response = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]