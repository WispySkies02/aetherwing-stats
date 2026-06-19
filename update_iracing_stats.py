import json
from datetime import datetime, timezone

STATS_FILE = "iracing-stats.json"

with open(STATS_FILE, "r", encoding="utf-8") as file:
    data = json.load(file)

data["updated"] = datetime.now(timezone.utc).isoformat()

for driver in data.get("drivers", []):
    driver.setdefault("license", "—")
    driver.setdefault("irating", "—")
    driver.setdefault("starts", "—")
    driver.setdefault("wins", "—")
    driver.setdefault("top5s", "—")
    driver.setdefault("top10s", "—")
    driver.setdefault("avgFinish", "—")
    driver.setdefault("lastResult", "—")

with open(STATS_FILE, "w", encoding="utf-8") as file:
    json.dump(data, file, indent=2)
    file.write("\n")
