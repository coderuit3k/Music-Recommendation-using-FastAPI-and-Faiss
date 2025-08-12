import json
from datetime import datetime

def save_res(results: list, query: str, file_name="results.jsonl") -> None:
    data = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "results": results
    }

    with open(file_name, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")