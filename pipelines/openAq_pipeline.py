import pandas as pd
import requests
import time

from utils.constants import (
    OPENAQ_API_KEY,
    OPENAQ_BASE_URL,
    OUTPUT_PATH
)


def connect_openaq():
    headers = {
        "X-API-Key": OPENAQ_API_KEY
    }
    return headers


def extract_locations(headers, limit: int = 100, page: int = 1, iso: str = "FR"):
    url = f"{OPENAQ_BASE_URL}/locations"

    params = {
        "limit": limit,
        "page": page,
        "iso": iso
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()
    return data.get("results", [])


def extract_sensors_by_location(headers, location_id: int):
    url = f"{OPENAQ_BASE_URL}/locations/{location_id}/sensors"

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    return data.get("results", [])


def extract_measurements_by_sensor(headers, sensor_id: int, limit: int = 100, page: int = 1):
    url = f"{OPENAQ_BASE_URL}/sensors/{sensor_id}/measurements"

    params = {
        "limit": limit,
        "page": page
    }
    time.sleep(2)

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()
    return data.get("results", [])


def transform_data(measurements):
    rows = []

    for m in measurements:
        parameter = m.get("parameter") or {}
        period = m.get("period") or {}
        datetime_from = period.get("datetimeFrom") or {}
        datetime_to = period.get("datetimeTo") or {}

        row = {
            "location_id": m.get("location_id"),
            "location_name": m.get("location_name"),
            "sensor_id": m.get("sensor_id"),

            "parameter_id": parameter.get("id"),
            "parameter_name": parameter.get("name"),
            "parameter_units": parameter.get("units"),

            "value": m.get("value"),

            "datetime_from_utc": datetime_from.get("utc"),
            "datetime_from_local": datetime_from.get("local"),
            "datetime_to_utc": datetime_to.get("utc"),
            "datetime_to_local": datetime_to.get("local")
        }

        rows.append(row)

    return pd.DataFrame(rows)


def load_data_to_csv(df, file_path):
    df.to_csv(file_path, index=False)


def openAq_pipeline(file_name: str, limit: int = 100, page: int = 1, iso: str = "FR"):
    headers = connect_openaq()

    locations = extract_locations(
        headers=headers,
        limit=limit,
        page=page,
        iso=iso
    )

    all_measurements = []

    for location in locations:
        location_id = location.get("id")
        location_name = location.get("name")

        if location_id is None:
            continue

        sensors = extract_sensors_by_location(
            headers=headers,
            location_id=location_id
        )

        for sensor in sensors:
            sensor_id = sensor.get("id")

            if sensor_id is None:
                continue

            measurements = extract_measurements_by_sensor(
                headers=headers,
                sensor_id=sensor_id,
                limit=limit,
                page=page
            )

            for measurement in measurements:
                measurement["location_id"] = location_id
                measurement["location_name"] = location_name
                measurement["sensor_id"] = sensor_id

            all_measurements.extend(measurements)

    measurements_df = transform_data(all_measurements)

    file_path = f"{OUTPUT_PATH}/{file_name}.csv"
    load_data_to_csv(measurements_df, file_path)

    return file_path