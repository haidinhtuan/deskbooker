"""
Daily runner for automated check-in and cancellation.

Designed to run as a cron job on weekdays. Determines whether the user is
at the office by checking the current WiFi SSID against a configured list.

Behavior:
  - At office (WiFi matches):  Check in to all of today's bookings.
  - Not at office:             Cancel today's bookings to free up the spots.
  - Force mode (--force):      Skip WiFi detection, always check in.
                                Recommended for cron usage.
"""
import argparse
import os
import subprocess
from datetime import datetime

from .deskbird_client import DeskbirdClient
from .logger import setup_logger
from dotenv import load_dotenv

load_dotenv()
logger = setup_logger(__name__)

try:
    office_wifis = os.environ["OFFICE_WIFIS"].split(",")
except KeyError:
    logger.error("Can't find OFFICE_WIFIS in .env file")
    raise SystemExit


def get_wifi_info():
    """Detect the currently connected WiFi SSID.

    Tries Linux (nmcli) first, then falls back to macOS (airport utility).
    Returns a dict with an "SSID" key (None if no WiFi detected).
    """
    # Try Linux (nmcli) - parses terse output for the active connection
    try:
        process = subprocess.Popen(
            ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = process.communicate()
        if process.returncode == 0:
            for line in out.decode("utf-8").split("\n"):
                if line.startswith("yes:"):
                    return {"SSID": line.split(":")[1]}
    except FileNotFoundError:
        pass

    # Fallback to macOS (airport utility)
    try:
        process = subprocess.Popen(
            [
                (
                    "/System/Library/PrivateFrameworks/Apple80211.framework"
                    "/Versions/Current/Resources/airport"
                ),
                "-I",
            ],
            stdout=subprocess.PIPE,
        )
        out, err = process.communicate()
        wifi_info = {}
        for line in out.decode("utf-8").split("\n"):
            if ": " in line:
                key, val = line.split(": ")
                key = key.replace(" ", "")
                val = val.strip()
                wifi_info[key] = val
        return wifi_info
    except FileNotFoundError:
        return {"SSID": None}


# Initialize the Deskbird client from environment variables.
# This client is used for both check-in and cancellation.
db_client = DeskbirdClient(
    refresh_token=os.environ["REFRESH_TOKEN"],
    token_key=os.environ["TOKEN_KEY"],
    resource_id=os.environ["RESOURCE_ID"],
    zone_item_id=os.environ["ZONE_ITEM_ID"] if "ZONE_ITEM_ID" in os.environ else None,
    workspace_id=os.environ["WORKSPACE_ID"],
    start_hour=int(os.environ.get("START_HOUR", 9)),
    end_hour=int(os.environ.get("END_HOUR", 17)),
)


def main():
    parser = argparse.ArgumentParser(description="Daily runner for deskbooker.")
    parser.add_argument("--force", action="store_true", help="Force check-in without checking WiFi.")
    args = parser.parse_args()

    if args.force:
        logger.info("Force mode enabled. Skipping WiFi check and checking in...")
        db_client.checkin()
        return

    wifi_info = get_wifi_info()

    if wifi_info["SSID"] in office_wifis:
        logger.info("At the office! Checking in....")
        db_client.checkin()
    else:
        logger.info("Not at the office. Canceling booking...")
        today = datetime.now()
        db_client.cancel_booking(from_date=today, to_date=today)


if __name__ == "__main__":
    main()
