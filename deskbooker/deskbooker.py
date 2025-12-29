#!/usr/bin/env python
"""
Deskbooker CLI
Author: Hai Dinh Tuan <me@haidinhtuan.de>
"""
import argparse
import json
import os
import sys
from datetime import datetime

import dateutil.parser
from .deskbird_client import DeskbirdClient
from dotenv import load_dotenv
from prettytable import PrettyTable

load_dotenv()


def get_deskbird_client():
    return DeskbirdClient(
        refresh_token=os.environ["REFRESH_TOKEN"],
        token_key=os.environ["TOKEN_KEY"],
        resource_id=os.environ["RESOURCE_ID"],
        zone_item_id=os.environ.get("ZONE_ITEM_ID"),
        workspace_id=os.environ["WORKSPACE_ID"],
        start_hour=int(os.environ.get("START_HOUR", 9)),
        end_hour=int(os.environ.get("END_HOUR", 17)),
    )


def perform_checkin(client):
    return client.checkin()


def perform_cancel(client, from_date, to_date):
    client.cancel_booking(from_date, to_date)


def perform_get_bookings(client, limit=60):
    response = client.get_bookings(limit=limit)
    return json.loads(response.text)


def perform_book(client, from_date, to_date, zone=None, desk_number=None):
    if (zone is None) != (desk_number is None):
        raise ValueError("either of the following arguments are required: -z/--zone, -d/--desk")
    
    if zone is not None and desk_number is not None:
        client.set_zone_item_id(zone_name=zone, desk_id=desk_number)
        
    response = client.book_desk(from_date=from_date, to_date=to_date)
    return json.loads(response.text)


def checkin_cmd(args):
    client = get_deskbird_client()
    perform_checkin(client)


def cancel_cmd(args):
    client = get_deskbird_client()
    if args.from_date is None and args.to_date is None:
        from_date = to_date = datetime.today()
    elif args.from_date and args.to_date:
        try:
            from_date = dateutil.parser.parse(args.from_date)
        except dateutil.parser._parser.ParserError:
            print(f"{args.from_date} is not a valid date format")
            sys.exit(1)
        try:
            to_date = dateutil.parser.parse(args.to_date)
        except dateutil.parser._parser.ParserError:
            print(f"{args.to_date} is not a valid date format")
            sys.exit(1)
    else:
        print("the following arguments are required: -f/--from, -t/--to")
        sys.exit(1)
    perform_cancel(client, from_date, to_date)


def bookings_cmd(args):
    client = get_deskbird_client()
    limit = int(os.environ.get("BOOKING_RANGE_DAYS", 60))
    bookings = perform_get_bookings(client, limit=limit)
    bookings_table = PrettyTable(["Date", "Zone", "Desk", "Check-in"])

    for booking in bookings["results"]:
        booking_list = [
            datetime.fromtimestamp(int(booking["bookingStartTime"] / 1000)).date(),
            booking["workspace"]["name"],
            f"{booking['zone']['name']} {booking['zoneItemName']}",
            "✅" if booking["checkInStatus"] == "checkedIn" else "❌",
        ]
        bookings_table.add_row(booking_list)
    print(bookings_table)


def book_cmd(args):
    client = get_deskbird_client()
    try:
        from_date = dateutil.parser.parse(args.from_date)
    except dateutil.parser._parser.ParserError:
        print(f"{args.from_date} is not a valid date format")
        sys.exit(1)
    try:
        to_date = dateutil.parser.parse(args.to_date)
    except dateutil.parser._parser.ParserError:
        print(f"{args.to_date} is not a valid date format")
        sys.exit(1)

    try:
        data_response = perform_book(client, from_date, to_date, args.zone, args.desk_number)
    except ValueError as e:
        print(str(e))
        sys.exit(1)
    except KeyError as e:
        print(str(e))
        sys.exit(1)
    
    # New response structure handling
    successful = data_response.get("successfulBookings", [])
    failed = data_response.get("failedBookings", [])
    
    all_bookings = []
    for b in successful:
        # Successful bookings are just the booking objects
        all_bookings.append(b)
        
    for f in failed:
        # Failed bookings have a 'booking' key and an 'error' key
        b = f["booking"]
        b["errorMessage"] = f["error"].get("message", "Unknown error")
        all_bookings.append(b)

    all_bookings = sorted(all_bookings, key=lambda booking: booking["bookingStartTime"])
    for booking in all_bookings:
        status_icon = "❌" if "errorMessage" in booking else "✅"
        msg = booking.get("errorMessage", booking.get("bookingStatus", "Success"))
        date_str = str(datetime.fromtimestamp(booking["bookingStartTime"] / 1000).date())
        print(f"{status_icon} | {date_str} | {msg}")


arg_parser = argparse.ArgumentParser()
subparsers = arg_parser.add_subparsers(help="sub-command help")

book_parser = subparsers.add_parser("book", help="book help")
book_parser.set_defaults(func=book_cmd)
book_parser.add_argument(
    "-f", "--from", dest="from_date", help="From date", required=True
)
book_parser.add_argument("-t", "--to", dest="to_date", help="To date", required=True)
book_parser.add_argument("-d", "--desk", dest="desk_number", help="Desk number")
book_parser.add_argument("-z", "--zone", dest="zone", help="Set zone")

checkin_parser = subparsers.add_parser("checkin", help="checkin help")
checkin_parser.set_defaults(func=checkin_cmd)

bookings_parser = subparsers.add_parser("bookings", help="bookings help")
bookings_parser.set_defaults(func=bookings_cmd)

cancel_parser = subparsers.add_parser("cancel", help="cancel help")
cancel_parser.add_argument(
    "-f", "--from", dest="from_date", help="From date", required=False
)
cancel_parser.add_argument("-t", "--to", dest="to_date", help="To date", required=False)
cancel_parser.set_defaults(func=cancel_cmd)


def main():
    try:
        args = arg_parser.parse_args()
        if hasattr(args, "func"):
            args.func(args)
        else:
            arg_parser.print_help()
    except KeyboardInterrupt:
        print("Stopping...")


if __name__ == "__main__":
    main()
