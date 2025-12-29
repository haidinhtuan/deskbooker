# Deskbooker

A Python tool to automate desk bookings on Deskbird, manage check-ins based on network location, and handle daily booking routines.

**Author:** Hai Dinh Tuan ([me@haidinhtuan.de](mailto:me@haidinhtuan.de))

## Features

*   **Bulk Booking:** Book a specific desk or zone for a date range.
*   **Auto-Check-in:** Automatically check in when connected to office WiFi.
*   **Auto-Cancellation:** Automatically cancel today's booking if not at the office (and not connected to office WiFi).
*   **Auto-Booking Routine:** Automatically book your favorite spot for the next 60 days (or configured range) to ensure you always have a seat.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd deskbooker
    ```

2.  **Install dependencies and CLI tools using [Poetry](https://python-poetry.org/):**
    ```bash
    poetry install
    ```
    This will install the package in a virtual environment and register the CLI commands.

## Usage

You can run the following commands using `poetry run <command>` or by activating the environment with `poetry shell`.

### CLI Tool (`deskbooker`)

The main CLI for manual interactions.

*   **Book a desk for a range:**
    ```bash
    # Uses ZONE_ITEM_ID from .env if desk/zone not specified
    deskbooker book --from 2024-01-01 --to 2024-01-05
    
    # Specify zone and desk manually
    deskbooker book --from 2024-01-01 --to 2024-01-05 --zone "Growth" --desk "18"
    ```

*   **Check in manually:**
    ```bash
    deskbooker checkin
    ```

*   **View upcoming bookings:**
    ```bash
    deskbooker bookings
    ```

*   **Cancel bookings:**
    ```bash
    # Cancel specific range
    deskbooker cancel --from 2024-01-01 --to 2024-01-02
    
    # Cancel today (default if no dates provided)
    deskbooker cancel
    ```

### Automation Commands

#### 1. Daily Runner (`deskbooker-daily`)
Checks if you are at the office (based on WiFi SSID).
*   **If at office:** Checks you in.
*   **If NOT at office:** Cancels today's booking to free up the spot.
*   **Force check-in:** Use `--force` to skip the WiFi check and check in immediately.

**Manual Force Check-in:**
```bash
deskbooker-daily --force
```

**Cron Setup (e.g., run every weekday at 8:55 AM):**
```bash
55 8 * * 1-5 cd /path/to/deskbooker && poetry run deskbooker-daily
```

#### 2. Auto Booker (`deskbooker-auto`)
Automatically books your configured `ZONE_ITEM_ID` for the maximum configured range (default 60 days) to keep your schedule full. It skips weekends.

**Cron Setup (e.g., run every Monday at 8:00 AM):**
```bash
0 8 * * 1 cd /path/to/deskbooker && poetry run deskbooker-auto
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.