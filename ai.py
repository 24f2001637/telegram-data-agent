from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("AIPIPE_TOKEN"),
    base_url="https://aipipe.org/openai/v1"
)

def ask_ai(question, dataframe=None):

    prompt = """
You are a data analyst.

Answer ONLY with valid JSON.

Never write markdown.

Never explain.

Return exactly:

{
  "answer": ...,
  "log_url": "http://localhost/run.jsonl"
}
"""

    if dataframe is not None:

        prompt += "\n\nDataset Information:\n"

        prompt += f"Rows: {len(dataframe)}\n"
        prompt += f"Columns: {list(dataframe.columns)}\n\n"

        prompt += "Sample Data:\n"
        prompt += dataframe.head(10).to_string(index=False)

    response = client.chat.completions.create(
        model="gpt-5-nano",
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

    return response.choices[0].message.content