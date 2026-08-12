from openai import OpenAI
import os
import json
from dotenv import load_dotenv

load_dotenv()

def get_client():
    token = os.getenv("AIPIPE_TOKEN") or os.getenv("OPENAI_API_KEY")
    return OpenAI(
        api_key=token,
        base_url="https://aipipe.org/openai/v1"
    )

def ask_ai(question, dataframe=None, log_url=None):

    if not log_url:
        port = os.getenv("PORT", "10000")
        base_url = (os.getenv("BASE_URL") or os.getenv("RENDER_EXTERNAL_URL") or f"http://localhost:{port}").rstrip("/")
        log_url = f"{base_url}/logs/run.jsonl"

    prompt = f"""You are an expert data analyst AI.

Answer the user's question accurately and clearly.

Return ONLY a single valid JSON object with NO markdown formatting, NO backticks (```json), and NO extra text outside the JSON.

Required JSON Structure:
{{
  "answer": "Your calculated or textual answer to the question",
  "log_url": "{log_url}"
}}
"""

    if dataframe is not None:

        prompt += "\n\nDataset Information:\n"
        prompt += f"Rows: {len(dataframe)}\n"
        prompt += f"Columns: {list(dataframe.columns)}\n\n"
        prompt += "Sample Data:\n"
        prompt += dataframe.head(10).to_string(index=False)

    client = get_client()

    response = client.chat.completions.create(
        model=os.getenv("AI_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    raw_content = response.choices[0].message.content.strip()

    # Clean markdown code fences if present
    if raw_content.startswith("```"):
        lines = raw_content.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw_content = "\n".join(lines).strip()

    try:
        data = json.loads(raw_content)
        if data.get("answer") is None:
            data["answer"] = raw_content
        data["log_url"] = log_url
        return json.dumps(data)
    except Exception:
        return json.dumps({
            "answer": raw_content,
            "log_url": log_url
        })
