import json
import time
from pathlib import Path

import psycopg2

# Configuration
# -------------------------

BASE_DIR = Path(__file__).resolve().parent
SD_CARD_FOLDER = BASE_DIR / "SD_CARD"
SD_CARD_ID = "SD001"
POLL_INTERVAL_SECONDS = 5
STATE_FILE = BASE_DIR / ".processed_images.json"
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")


def load_processed_state():
    if not STATE_FILE.exists():
        return {}

    try:
        with STATE_FILE.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {}


def save_processed_state(state):
    with STATE_FILE.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)


def get_image_files(folder=None):
    if folder is None:
        folder = SD_CARD_FOLDER

    if not folder.exists():
        return []

    return sorted(
        entry.name
        for entry in folder.iterdir()
        if entry.is_file() and entry.name.lower().endswith(IMAGE_EXTENSIONS)
    )


def get_new_image_files(known_files, folder=None):
    if folder is None:
        folder = SD_CARD_FOLDER
    if not isinstance(folder, Path):
        folder = Path(folder)

    current_files = set(get_image_files(folder))
    return [name for name in sorted(current_files) if name not in known_files]


def load_metadata(folder=SD_CARD_FOLDER):
    gps_file = folder / "gps.json"
    time_file = folder / "timestamp.json"

    if not gps_file.exists():
        raise FileNotFoundError(f"Missing required file: {gps_file}")
    if not time_file.exists():
        raise FileNotFoundError(f"Missing required file: {time_file}")

    with gps_file.open("r", encoding="utf-8") as handle:
        gps = json.load(handle)

    with time_file.open("r", encoding="utf-8") as handle:
        ts = json.load(handle)

    return {
        "latitude": gps["latitude"],
        "longitude": gps["longitude"],
        "altitude": gps["altitude"],
        "capture_timestamp": ts["capture_timestamp"],
    }


def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="Samala@8352",
        dbname="sd_stick",
    )


def ensure_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sd_card_data
        (
            record_id SERIAL PRIMARY KEY,
            sd_card_id TEXT,
            image_name TEXT,
            image_path TEXT,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            altitude DOUBLE PRECISION,
            capture_timestamp TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def ingest_new_images(image_names, metadata):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        ensure_table(cursor)

        for image_name in image_names:
            image_path = str(SD_CARD_FOLDER / image_name)
            cursor.execute(
                """
                INSERT INTO sd_card_data
                (
                    sd_card_id,
                    image_name,
                    image_path,
                    latitude,
                    longitude,
                    altitude,
                    capture_timestamp
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    SD_CARD_ID,
                    image_name,
                    image_path,
                    metadata["latitude"],
                    metadata["longitude"],
                    metadata["altitude"],
                    metadata["capture_timestamp"],
                ),
            )
            print(f"Processed new image: {image_name}")

        conn.commit()
    finally:
        conn.close()


def watch_for_new_images():
    if not SD_CARD_FOLDER.exists():
        raise FileNotFoundError(
            f"The folder '{SD_CARD_FOLDER}' was not found. Create it and place gps.json, timestamp.json, and your image files inside it."
        )

    processed = load_processed_state()
    print("Watching for new images in", SD_CARD_FOLDER)
    print("Press Ctrl+C to stop.")

    while True:
        try:
            metadata = load_metadata()
            new_images = get_new_image_files(set(processed.keys()))

            if new_images:
                ingest_new_images(new_images, metadata)
                for image_name in new_images:
                    processed[image_name] = True
                save_processed_state(processed)

            time.sleep(POLL_INTERVAL_SECONDS)
        except FileNotFoundError as exc:
            print(exc)
            time.sleep(POLL_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("Stopping watcher.")
            break


if __name__ == "__main__":
    watch_for_new_images()