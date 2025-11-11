import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent / "data" / "careers.json"

def _load():
    if DATA_PATH.exists():
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def get_career_info(names):
    data = _load()
    idx = {item["name"]: item for item in data}
    out = []
    for n in names:
        if n in idx:
            out.append(idx[n])
        else:
            out.append({"name": n, "salary": "—", "demand": "—", "courses": []})
    return out
