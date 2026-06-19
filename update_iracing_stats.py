import json
from datetime import datetime, timezone

STATS_FILE = "iracing-stats.json"

CATEGORY_LABELS = {
    "oval": "Oval",
    "sportsCar": "Sports Car",
    "formula": "Formula",
    "dirtOval": "Dirt Oval",
    "dirtRoad": "Dirt Road"
}

CATEGORY_FIELDS = {
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

OLD_TOP_LEVEL_FIELDS = [
    "license",
    "irating",
    "starts",
    "wins",
    "top5s",
    "top10s",
    "avgFinish",
    "lastResult",
    "stats"
]


def car_number_sort_value(driver):
    try:
        return int(driver.get("number", 9999))
    except ValueError:
        return 9999


with open(STATS_FILE, "r", encoding="utf-8") as file:
    data = json.load(file)

data["updated"] = datetime.now(timezone.utc).isoformat()

for driver in data.get("drivers", []):
    driver.setdefault("categories", {})

    for category_key, category_label in CATEGORY_LABELS.items():
        driver["categories"].setdefault(category_key, {})
        category_data = driver["categories"][category_key]

        category_data["label"] = category_label

        for field, default_value in CATEGORY_FIELDS.items():
            category_data.setdefault(field, default_value)

    for old_field in OLD_TOP_LEVEL_FIELDS:
        driver.pop(old_field, None)

data["drivers"] = sorted(data.get("drivers", []), key=car_number_sort_value)

with open(STATS_FILE, "w", encoding="utf-8") as file:
    json.dump(data, file, indent=2)
    file.write("\n")
