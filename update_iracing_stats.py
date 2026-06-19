import json
import os
from datetime import datetime, timezone

from iracingdataapi.client import irDataClient

STATS_FILE = "iracing-stats.json"

CATEGORY_INFO = {
    "oval": {
        "label": "Oval",
        "categoryId": 1
    },
    "sportsCar": {
        "label": "Sports Car",
        "categoryId": 5
    },
    "formula": {
        "label": "Formula",
        "categoryId": 6
    },
    "dirtOval": {
        "label": "Dirt Oval",
        "categoryId": 3
    },
    "dirtRoad": {
        "label": "Dirt Road",
        "categoryId": 4
    }
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

LICENSE_CLASS_MAP = {
    "1": "R",
    "2": "D",
    "3": "C",
    "4": "B",
    "5": "A",
    "6": "Pro",
    "7": "Pro/WC"
}


def car_number_sort_value(driver):
    try:
        return int(driver.get("number", 9999))
    except (TypeError, ValueError):
        return 9999


def clean_value(value):
    if value is None:
        return "—"

    value = str(value).strip()

    if value == "":
        return "—"

    return value


def get_latest_chart_value(chart_data):
    chart_rows = chart_data.get("data", [])

    if not chart_rows:
        return None

    return chart_rows[-1].get("value")


def decode_safety_rating(raw_value):
    if raw_value is None:
        return {
            "licenseClass": "—",
            "safetyRating": "—"
        }

    raw = str(raw_value).strip()

    if not raw:
        return {
            "licenseClass": "—",
            "safetyRating": "—"
        }

    license_class = LICENSE_CLASS_MAP.get(raw[0], "—")
    rating_digits = raw[1:].zfill(3)

    safety_rating = f"{rating_digits[0]}.{rating_digits[1:]}"

    return {
        "licenseClass": license_class,
        "safetyRating": safety_rating
    }


def find_driver_row(driver_rows, cust_id):
    wanted = str(cust_id).strip()

    for row in driver_rows:
        row_cust_id = str(row.get("cust_id", "")).strip()

        if row_cust_id == wanted:
            return row

    return None


def first_available(row, keys):
    if not row:
        return "—"

    for key in keys:
        if key in row and str(row.get(key, "")).strip() != "":
            return clean_value(row.get(key))

    return "—"


def update_category_from_driver_list(category_data, driver_row):
    if not driver_row:
        return

    category_data["starts"] = first_available(driver_row, [
        "starts",
        "num_starts",
        "race_starts",
        "races",
        "race_count"
    ])

    category_data["wins"] = first_available(driver_row, [
        "wins",
        "num_wins",
        "race_wins"
    ])

    category_data["top5s"] = first_available(driver_row, [
        "top5",
        "top_5",
        "top5s",
        "top_5s"
    ])

    category_data["top10s"] = first_available(driver_row, [
        "top10",
        "top_10",
        "top10s",
        "top_10s"
    ])

    category_data["avgFinish"] = first_available(driver_row, [
        "avg_finish",
        "average_finish",
        "avg_fin",
        "avgfinish"
    ])


def update_category_from_charts(idc, category_data, cust_id, category_id):
    irating_chart = idc.member_chart_data(
        cust_id=int(cust_id),
        category_id=category_id,
        chart_type=1
    )

    safety_chart = idc.member_chart_data(
        cust_id=int(cust_id),
        category_id=category_id,
        chart_type=3
    )

    irating_value = get_latest_chart_value(irating_chart)
    safety_value = get_latest_chart_value(safety_chart)

    category_data["irating"] = clean_value(irating_value)

    decoded_safety = decode_safety_rating(safety_value)
    category_data["licenseClass"] = decoded_safety["licenseClass"]
    category_data["safetyRating"] = decoded_safety["safetyRating"]


def load_driver_lists(idc):
    driver_lists = {}

    for category_key, category_info in CATEGORY_INFO.items():
        category_id = category_info["categoryId"]

        try:
            driver_lists[category_key] = idc.driver_list(category_id=category_id)
            print(f"Loaded driver list for {category_info['label']}")
        except Exception as error:
            driver_lists[category_key] = []
            print(f"Could not load driver list for {category_info['label']}: {error}")

    return driver_lists


def main():
    iracing_email = os.environ.get("IRACING_EMAIL")
    iracing_password = os.environ.get("IRACING_PASSWORD")

    if not iracing_email or not iracing_password:
        raise RuntimeError("Missing IRACING_EMAIL or IRACING_PASSWORD repository secrets.")

    with open(STATS_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    idc = irDataClient(
        username=iracing_email,
        password=iracing_password,
        silent=True
    )

    driver_lists = load_driver_lists(idc)

    for driver in data.get("drivers", []):
        cust_id = driver.get("iracingId")

        if not cust_id:
            print(f"Skipping {driver.get('displayName', 'Unknown Driver')} because no iRacing ID is set.")
            continue

        driver.setdefault("categories", {})

        for category_key, category_info in CATEGORY_INFO.items():
            driver["categories"].setdefault(category_key, {})
            category_data = driver["categories"][category_key]

            category_data["label"] = category_info["label"]

            for field, default_value in CATEGORY_FIELDS.items():
                category_data.setdefault(field, default_value)

            try:
                update_category_from_charts(
                    idc=idc,
                    category_data=category_data,
                    cust_id=cust_id,
                    category_id=category_info["categoryId"]
                )

                driver_row = find_driver_row(
                    driver_rows=driver_lists.get(category_key, []),
                    cust_id=cust_id
                )

                update_category_from_driver_list(
                    category_data=category_data,
                    driver_row=driver_row
                )

                print(f"Updated {driver.get('displayName', cust_id)} - {category_info['label']}")

            except Exception as error:
                print(f"Could not update {driver.get('displayName', cust_id)} - {category_info['label']}: {error}")

        for old_field in OLD_TOP_LEVEL_FIELDS:
            driver.pop(old_field, None)

    data["drivers"] = sorted(data.get("drivers", []), key=car_number_sort_value)
    data["updated"] = datetime.now(timezone.utc).isoformat()

    with open(STATS_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.write("\n")


if __name__ == "__main__":
    main()
