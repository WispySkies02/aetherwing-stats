import json
from datetime import datetime, timezone

STATS_FILE = "iracing-stats.json"

CATEGORY_TEMPLATE = {
    "label": "—",
    "licenseClass": "—",
    "safetyRating": "—",
    "irating": "—",
    "starts": "—",
    "wins": "—",
    "top5s": "—",
    "top10s": "—",
    "avgFinish": "—",
    "lastResult": "—"
}

CATEGORY_LABELS = {
    "oval": "Oval",
    "sportsCar": "Sports Car",
    "formula": "Formula",
    "dirtOval": "Dirt Oval",
    "dirtRoad": "Dirt Road"
}

with open(STATS_FILE, "r", encoding="utf-8") as file:
    data = json.load(file)

data["updated"] = datetime.now(timezone.utc).isoformat()

for driver in data.get("drivers", []):
    driver.setdefault("categories", {})

    for category_key, category_label in CATEGORY_LABELS.items():
        driver["categories"].setdefault(category_key, {})

        category_data = driver["categories"][category_key]

        for field, default_value in CATEGORY_TEMPLATE.items():
            category_data.setdefault(field, default_value)

        category_data["label"] = category_label

    # Remove old top-level stat fields if they exist from the older version
    for old_field in [
        "license",
        "irating",
        "starts",
        "wins",
        "top5s",
        "top10s",
        "avgFinish",
        "lastResult",
        "stats"
    ]:
        driver.pop(old_field, None)

with open(STATS_FILE, "w", encoding="utf-8") as file:
    json.dump(data, file, indent=2)
    file.write("\n")
