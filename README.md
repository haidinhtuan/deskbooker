# Deskbooker

A Python tool to automate desk bookings on Deskbird, manage check-ins based on network location, and handle daily booking routines.

**Author:** Hai Dinh Tuan ([me@haidinhtuan.de](mailto:me@haidinhtuan.de))

## Features

*   **Bulk Booking:** Book a specific desk or zone for a date range.
*   **Multi-Workspace Booking:** Automatically book desks across multiple workspaces with dynamic desk lookup.
*   **Auto-Check-in:** Automatically check in to all of today's bookings across all workspaces. Supports both WiFi-based detection and force mode.
*   **Auto-Cancellation:** Automatically cancel today's booking if not at the office (based on WiFi SSID).
*   **Auto-Booking Routine:** Automatically book your configured desks for the next 60 days (or configured range) to ensure you always have a seat.

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

3.  **Configure environment variables:**
    ```bash
    cp .env.example .env
    ```
    Edit `.env` with your Deskbird credentials and preferences. See [Configuration](#configuration) for details.

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `REFRESH_TOKEN` | Yes | - | Firebase refresh token for authentication |
| `TOKEN_KEY` | Yes | - | Firebase API key |
| `RESOURCE_ID` | Yes | - | Deskbird resource ID for primary workspace |
| `WORKSPACE_ID` | Yes | - | Deskbird workspace ID for primary workspace |
| `ZONE_ITEM_ID` | No | - | Desk zone item ID for primary workspace (used by CLI and daily runner) |
| `OFFICE_WIFIS` | Yes* | - | Comma-separated WiFi SSIDs for office detection (*required for daily runner without `--force`) |
| `BOOKING_RANGE_DAYS` | No | `60` | Number of days ahead to auto-book |
| `START_HOUR` | No | `9` | Booking start hour |
| `END_HOUR` | No | `17` | Booking end hour |

### Extra Bookings

To book desks in additional workspaces, edit the `EXTRA_BOOKINGS` list in `auto_book.py`:

```python
EXTRA_BOOKINGS = [
    ("Label", "workspace_id", "resource_id", "desk name"),
]
```

The desk name is looked up dynamically across all zones in the workspace via the Deskbird API, so you don't need to know the `zone_item_id` upfront. If you change desks, just update the desk name.

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

Checks if you are at the office (based on WiFi SSID) and manages check-ins.

*   **If at office:** Checks in to all of today's bookings across all workspaces.
*   **If NOT at office:** Cancels today's booking to free up the spot.
*   **Force check-in (`--force`):** Skips WiFi detection and checks in to all of today's bookings immediately. Recommended for cron usage.

```bash
deskbooker-daily --force
```

**Cron Setup (e.g., force check-in every weekday at 10:00 AM):**
```bash
0 10 * * 1-5 cd /path/to/deskbooker && poetry run deskbooker-daily --force >> cron_daily.log 2>&1
```

#### 2. Auto Booker (`deskbooker-auto`)

Automatically books your primary desk (from `.env`) and any extra desks (from `EXTRA_BOOKINGS` in `auto_book.py`) for the configured range. Skips weekends. Extra desks are resolved dynamically by name, so no hardcoded zone item IDs are needed.

```bash
deskbooker-auto
```

**Cron Setup (e.g., every Monday at 11:30 AM):**
```bash
30 11 * * 1 cd /path/to/deskbooker && poetry run deskbooker-auto >> cron_auto.log 2>&1
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
