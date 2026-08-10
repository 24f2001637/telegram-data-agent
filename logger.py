import json
import os

from datetime import datetime, timezone


LOG_FILE = "logs/run.jsonl"


os.makedirs(
    "logs",
    exist_ok=True
)


def write_log(
    role,
    content
):

    obj = {
        "time": datetime.now(
            timezone.utc
        ).isoformat(),

        "role": role,

        "content": content
    }

    with open(
        LOG_FILE,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            json.dumps(
                obj,
                ensure_ascii=False
            )
            + "\n"
        )