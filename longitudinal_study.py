import argparse
import csv
from datetime import datetime
import os

import googlemaps
from dotenv import load_dotenv

from smtp import send_sms_via_email


# Configure environment
load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
WORK_ADDRESS = os.getenv("WORK_ADDRESS")
HOME_ADDRESS = os.getenv("HOME_ADDRESS")
CSV_FILE =os.getenv("CSV_FILE")
gmaps = googlemaps.Client(key=API_KEY)


def get_drive_time(origin: str, destination:str) -> str:
    """
    Given an origin and a destination, return Google Maps' drive time estimate.

    :param origin: starting point
    :param destination: ending point
    :return: a string specifying duration in seconds, e.g. "2837" -> 47.28 mins
    """
    directions = gmaps.directions(origin, destination, mode="driving", departure_time="now")
    duration = directions[0]['legs'][0]['duration']['value']
    return duration


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
        home_to_work = get_drive_time(HOME_ADDRESS, WORK_ADDRESS)
        work_to_home = get_drive_time(WORK_ADDRESS, HOME_ADDRESS)
    except Exception as e:
        print(f"Error fetching directions: {e}")
        return

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, weekday, home_to_work, work_to_home])


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
    send_sms_via_email(
        number=os.getenv("PHONE_NUMBER"),
        carrier_gateway=os.getenv("CARRIER_GATEWAY"),
        message=f"Your traffic data is ready for review!",
        sender_email=os.getenv("EMAIL"),
        sender_password=os.getenv("GOOGLE_TOKEN")
    )


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
