"""
Deskbird API Client
Author: Hai Dinh Tuan <me@haidinhtuan.de>
"""
import json
from datetime import datetime, timedelta
from typing import Optional

import requests
from .auth import get_access_token
from .logger import setup_logger

logger = setup_logger(__name__)


class DeskbirdClient:
    access_token: Optional[str] = None
    refresh_token: str
    token_key: str
    resource_id: str
    zone_item_id: Optional[str]
    workspace_id: str
    start_hour: int
    end_hour: int
    API_BASE_URL = "https://api.deskbird.com/v1.1"
    APP_BASE_URL = "https://web.deskbird.app/api/v1.1"

    def __init__(
        self,
        refresh_token: str,
        token_key: str,
        resource_id: str,
        workspace_id: str,
        zone_item_id: Optional[str] = None,
        start_hour: int = 9,
        end_hour: int = 17,
    ):
        self.refresh_token = refresh_token
        self.token_key = token_key
        self.resource_id = resource_id
        self.workspace_id = workspace_id
        self.zone_item_id = zone_item_id
        self.start_hour = start_hour
        self.end_hour = end_hour
        self.access_token = get_access_token(self.token_key, self.refresh_token)

    def set_zone_item_id(self, zone_name: str, desk_id: str) -> None:
        url = (
            f"{self.API_BASE_URL}/internalWorkspaces/"
            f"{self.workspace_id}/zones?internal"
        )
        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }
        response = json.loads(requests.get(url=url, headers=headers).text)
        for zone in response["results"]:
            if zone_name == zone["name"]:
                for desk in zone["availability"]["zoneItems"]:
                    if desk_id == desk["name"].split(" ")[-1]:
                        self.zone_item_id = desk["id"]
                        return
                raise KeyError(f"desk_id: {desk_id} not found in {zone_name}")
        raise KeyError(f"zone_name: {zone_name} does not exists")

    def find_zone_item_id(self, desk_name: str) -> None:
        """Search all zones for a desk by its full name."""
        url = (
            f"{self.API_BASE_URL}/internalWorkspaces/"
            f"{self.workspace_id}/zones?internal"
        )
        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }
        response = json.loads(requests.get(url=url, headers=headers).text)
        for zone in response["results"]:
            for desk in zone["availability"]["zoneItems"]:
                if desk_name == desk["name"]:
                    self.zone_item_id = desk["id"]
                    logger.info(f"Found desk '{desk_name}' in zone '{zone['name']}' (zone_item_id: {desk['id']})")
                    return
        raise KeyError(f"desk '{desk_name}' not found in any zone")

    def book_desk(self, from_date: datetime, to_date: datetime) -> requests.Response:
        url = f"{self.API_BASE_URL}/bookings"
        if not self.zone_item_id:
            raise Exception("ZONE_ITEM_ID missing from environment")
        body = {
            "bookings": [],
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        current_date = from_date
        while current_date <= to_date:
            if current_date.weekday() < 5:
                start_time = end_time = current_date
                start_time = start_time.replace(hour=self.start_hour, minute=0, second=0, microsecond=0)
                end_time = end_time.replace(hour=self.end_hour, minute=0, second=0, microsecond=0)
                body["bookings"].append(
                    {
                        "bookingStartTime": int(start_time.timestamp() * 1000),
                        "bookingEndTime": int(end_time.timestamp() * 1000),
                        "isAnonymous": False,
                        "isDayPass": True,
                        "resourceId": self.resource_id,
                        "zoneItemId": self.zone_item_id,
                        "workspaceId": self.workspace_id,
                    }
                )
            current_date = current_date + timedelta(days=1)

        return requests.post(url, headers=headers, data=json.dumps(body))

    def get_bookings(self, limit: int = 10) -> requests.Response:
        url = f"{self.API_BASE_URL}/user/bookings?upcoming=true&skip=0&limit={limit}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        return requests.get(url, headers=headers)

    def _parse_bookings_list(self, data: dict) -> Optional[list]:
        if "results" in data:
            return data["results"]
        elif "data" in data and "bookings" in data["data"]:
            return data["data"]["bookings"]
        logger.error("Could not find bookings list in response")
        return None

    def checkin(self) -> Optional[requests.Response]:
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        response = self.get_bookings(limit=10)
        bookings_list = self._parse_bookings_list(json.loads(response.text))
        if bookings_list is None:
            return None

        checked_in_any = False
        for booking in bookings_list:
            is_today = (
                datetime.fromtimestamp(int(booking["bookingStartTime"] / 1000)).date()
                == datetime.today().date()
            )
            if is_today:
                zone_name = booking.get('zoneItemName', 'unknown')
                if booking["checkInStatus"] == "checkedIn":
                    logger.info(
                        f"Already checked in to {zone_name}!"
                    )
                    checked_in_any = True
                else:
                    url = f"{self.API_BASE_URL}/bookings/{booking['id']}/check-in"
                    zone_item_id = booking.get("zoneItemId", self.zone_item_id)
                    body = {"qrCodeZoneItemId": zone_item_id}
                    response = requests.patch(
                        url, headers=headers, data=json.dumps(body)
                    )
                    if response.status_code == 200:
                        logger.info(f"Checked in to {zone_name} successfully! ✅")
                    else:
                        logger.error(f"Failed to check in to {zone_name}: {response.status_code} {response.text}")
                    checked_in_any = True
        if not checked_in_any:
            logger.info("You don't have any valid bookings for today.")
        return None

    def cancel_booking(self, from_date: datetime, to_date: datetime) -> None:
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        response = self.get_bookings(limit=100)
        bookings_list = self._parse_bookings_list(json.loads(response.text))
        if bookings_list is None:
            return

        current_date = from_date
        while current_date <= to_date:
            if current_date.weekday() < 5:
                for booking in bookings_list:
                    booking_date = datetime.fromtimestamp(
                        int(booking["bookingStartTime"] / 1000)
                    ).date()
                    if booking_date == current_date.date():
                        url = f"{self.API_BASE_URL}/bookings/{booking['id']}/cancel"
                        res = requests.patch(url=url, headers=headers)
                        if res.status_code in (200, 204):
                            logger.info(f"✅ {current_date.date()} canceled")
                        else:
                            logger.error(f"❌ Failed to cancel {current_date.date()}: {res.status_code}")
                        break
            current_date += timedelta(days=1)
