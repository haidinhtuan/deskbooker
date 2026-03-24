import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

from deskbooker.deskbooker import get_deskbird_client, perform_book
from deskbooker.logger import setup_logger

# Load environment variables
load_dotenv()
logger = setup_logger("auto_book")

def _log_booking_results(label, data_response):
    successful = data_response.get("successfulBookings", [])
    failed = data_response.get("failedBookings", [])

    all_bookings = []
    for b in successful:
        all_bookings.append(b)

    for f in failed:
        b = f["booking"]
        b["errorMessage"] = f["error"].get("message", "Unknown error")
        all_bookings.append(b)

    all_bookings = sorted(all_bookings, key=lambda booking: booking["bookingStartTime"])

    logger.info(f"Output ({label}):")
    for booking in all_bookings:
        status_icon = "❌" if "errorMessage" in booking else "✅"
        msg = booking.get("errorMessage", booking.get("bookingStatus", "Success"))
        date_str = str(datetime.fromtimestamp(booking["bookingStartTime"] / 1000).date())
        logger.info(f"{status_icon} | {date_str} | {msg}")


# Additional bookings: list of (label, workspace_id, resource_id, desk_name)
# desk_name is matched against the full desk name in Deskbird
EXTRA_BOOKINGS = [
    ("Berlin-DSTRCT 04.15.1", "16697", "181223", "04 . 15 . 1"),
]


def auto_book_max_range():
    # Calculate dates
    today = datetime.now()
    days_range = int(os.environ.get("BOOKING_RANGE_DAYS", 60))
    max_date = today + timedelta(days=days_range)

    start_date_str = today.strftime('%Y-%m-%d')
    end_date_str = max_date.strftime('%Y-%m-%d')

    logger.info(f"--- Auto-Booking Routine ---")
    logger.info(f"Attempting to book from {start_date_str} to {end_date_str}")

    try:
        client = get_deskbird_client()

        # Book default spot (Revaler Spitze)
        data_response = perform_book(client, today, max_date)
        _log_booking_results("Revaler Spitze", data_response)

        # Book extra spots (different workspaces)
        for label, ws_id, res_id, desk_name in EXTRA_BOOKINGS:
            logger.info(f"--- Booking {label} ---")
            client.workspace_id = ws_id
            client.resource_id = res_id
            client.find_zone_item_id(desk_name)
            data_response = perform_book(client, today, max_date)
            _log_booking_results(label, data_response)

    except Exception as e:
        logger.error("Error occurred:")
        logger.error(e)

if __name__ == "__main__":
    auto_book_max_range()
