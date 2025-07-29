import argparse
import csv
from datetime import datetime, timedelta, timezone
import logging
import os
import requests

import googlemaps
from dotenv import load_dotenv

from smtp import send_sms_via_email


# Configure environment
load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
WORK_ADDRESS = os.getenv("WORK_ADDRESS")
HOME_ADDRESS = os.getenv("HOME_ADDRESS")
CSV_FILE = os.getenv("CSV_FILE")
gmaps = googlemaps.Client(key=API_KEY)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.getenv("LOGFILE")),
        logging.StreamHandler()
    ]
)


def get_drive_time(origin: str, destination:str) -> str:
    """
    Given an origin and a destination, return Google Maps' drive time estimate.

    :param origin: starting point
    :param destination: ending point
    :return: a string specifying duration in seconds, e.g. "2837" -> 47.28 mins
    """
    directions = gmaps.directions(
        origin,
        destination,
        mode="driving",
        departure_time="now",
    )
    duration = directions[0]['legs'][0]['duration']['value']
    logging.info(f"Drive time retrieved: {duration} seconds")
    return duration


def get_drive_time_routes_api(origin: str, destination: str) -> str:
    """
    Use the Routes API instead of the Maps API (possibly more accurate, still testing.)

    :param origin: starting point
    :param destination: ending point
    :return: a string specifying duration in seconds, e.g. "2837" -> 47.28 mins
    """
    # Parameters - move to a config or env file?
    endpoint = "https://routes.googleapis.com/directions/v2:computeRoutes"

    # Prepare request
    payload = {
        "origin": {
            "address": origin
        },
        "destination": {
            "address": destination
        },
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE_OPTIMAL",
        "departureTime": (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat(),  # offset, datetime.now fails
        "computeAlternativeRoutes": False
    }

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "routes.duration"
    }

    # Send the request
    response = requests.post(endpoint, headers=headers, json=payload)
    if response.status_code != 200:
        logging.error(f"Routes API request failed: {response.status_code} - {response.text}")
        raise Exception("Failed to get drive time from Routes API")

    # Handle response
    data = response.json()
    duration = data["routes"][0]["duration"]
    duration_seconds = int(duration.rstrip("s"))
    logging.info(f"Drive time retrieved: {duration_seconds} seconds")
    return duration_seconds


def log_commute_times() -> None:
    """
    Runs a check for drive time from work to home and from home to work.
    Stores CSV log in the form of, [<timestamp>, <weekday>, <home-to-work>, <work-to-home>]

    :return: empty. Writes commute logs to a CSV file.
    """
    now = datetime.now()
    timestamp = now.isoformat()
    weekday = now.strftime("%A")

    try:
        logging.info("Getting drive time from home to work...")
        home_to_work = get_drive_time_routes_api(HOME_ADDRESS, WORK_ADDRESS)
        logging.info("Getting drive time from work to home...")
        work_to_home = get_drive_time_routes_api(WORK_ADDRESS, HOME_ADDRESS)
    except Exception as e:
        logging.error(f"Error fetching directions: {e}", exc_info=True)
        return

    try:
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, weekday, home_to_work, work_to_home])
        logging.info("Successfully logged commute times.")
    except Exception as e:
        logging.error(f"Failed to write to CSV: {e}", exc_info=True)


def analyze_commute_times() -> None:
    """
    TODO: provide descriptive statistics and departure recommendation times based on discovered patterns.

    :return: empty, runs on --notify
    """


def notify() -> None:
    """
    Send myself an SMS when data has been collected at the end of the week.
    :return: empty, runs on --notify
    """
    try:
        logging.info("Sending notification SMS...")
        send_sms_via_email(
            number=os.getenv("PHONE_NUMBER"),
            carrier_gateway=os.getenv("CARRIER_GATEWAY"),
            message=f"Your traffic data is ready for review!",
            sender_email=os.getenv("EMAIL"),
            sender_password=os.getenv("GOOGLE_TOKEN")
        )
        logging.info("SMS sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send SMS: {e}", exc_info=True)


if __name__ == '__main__':
    # Retrieve arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--notify", action="store_true", help="Send SMS instead of computing commute time.")
    args = parser.parse_args()

    # Depending on args, run commute log or notify myself of commute analysis
    if args.notify:
        analyze_commute_times()
        notify()
    else:
        log_commute_times()
