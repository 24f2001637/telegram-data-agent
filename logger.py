import json
import os
from datetime import datetime

LOG_FILE = "logs/run.jsonl"

os.makedirs("logs", exist_ok=True)

def write_log(role, content):

    with open(LOG_FILE, "a", encoding="utf-8") as f:

        obj = {
            "time": datetime.now().isoformat(),
            "role": role,
            "content": content
        }

        f.write(json.dumps(obj) + "\n")