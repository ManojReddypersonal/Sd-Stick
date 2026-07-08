import os
import json
import psycopg2

# Configuration
# -------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SD_CARD_FOLDER = os.path.join(BASE_DIR, "SD_CARD")
SD_CARD_ID = "SD001"

if not os.path.isdir(SD_CARD_FOLDER):
    raise FileNotFoundError(
        f"The folder '{SD_CARD_FOLDER}' was not found. Create it and place gps.json, timestamp.json, and your image files inside it."
    )

# Connect Database
#-------------------------

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",
    password="Samala@8352",
    dbname="sd_stick"
)
cursor = conn.cursor()

# Create Table
# -------------------------

cursor.execute("""
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
""")

# Read GPS
# -------------------------

gps_file = os.path.join(SD_CARD_FOLDER, "gps.json")

if not os.path.exists(gps_file):
    raise FileNotFoundError(f"Missing required file: {gps_file}")

with open(gps_file) as f:
    gps = json.load(f)

latitude = gps["latitude"]
longitude = gps["longitude"]
altitude = gps["altitude"]

# Read Timestamp
# -------------------------

time_file = os.path.join(SD_CARD_FOLDER, "timestamp.json")

if not os.path.exists(time_file):
    raise FileNotFoundError(f"Missing required file: {time_file}")

with open(time_file) as f:
    ts = json.load(f)

capture_timestamp = ts["capture_timestamp"]

# Read Images
# -------------------------

for file in os.listdir(SD_CARD_FOLDER):

    if file.lower().endswith((".jpg", ".jpeg", ".png")):

        image_name = file
        image_path = os.path.join(SD_CARD_FOLDER, file)

        cursor.execute("""
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

        VALUES
        (%s, %s, %s, %s, %s, %s, %s)
        """,

        (
            SD_CARD_ID,
            image_name,
            image_path,
            latitude,
            longitude,
            altitude,
            capture_timestamp
        ))

conn.commit()
conn.close()

print("SD Card Ingestion Completed Successfully.")