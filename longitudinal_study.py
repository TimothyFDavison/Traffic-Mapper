import argparse
import csv
from datetime import datetime, timedelta, timezone
import logging
import os
import requests

from dotenv import load_dotenv
import googlemaps
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

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
        "departureTime": (datetime.now(timezone.utc)+timedelta(minutes=2)).isoformat(),  # offset, datetime.now fails
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


def plot_commute_times(df: pd.DataFrame, column: str, title: str, filename: str) -> None:
    """
    Will save an plot of the commute graph over each day, computed at the end of the week.
    Work in progress! Lots to refine here.

    TODO: known error with mdates as an x axis ticker, e.g.
    "ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))" yields
    2025-07-28 23:13:21,249 [WARNING] Locator attempting to generate 19272 ticks ([10155.041666666666, ...,
        11760.958333333334]), which exceeds Locator.MAXTICKS (1000).

    :return:
    """
    # Select data
    colors = {
        "Monday": "yellow",
        "Tuesday": "green",
        "Wednesday": "blue",
        "Thursday": "indigo",
        "Friday": "violet"
    }
    fig, ax = plt.subplots(figsize=(12, 6))
    for day in colors.keys():
        subset = df[df["day"] == day]
        if len(subset)==0:
            continue
        ax.plot(
            subset["time_of_day"],
            subset[column],
            label=day,
            color=colors[day],
            alpha=0.7,
        )

    # Set up plot
    ax.set_title(title)
    ax.set_xlabel("Time of Day")
    ax.set_ylabel("Drive Time (hours)")

    # Axis bounds and labels
    ax.set_ylim(0.5, 2)
    y_ticks = [0.5, 1.0, 1.5, 2.0]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([f"{int(t * 60)}" for t in y_ticks])
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    plt.xticks(rotation=45)

    # Finish plot and save
    ax.legend()
    plt.tight_layout()
    plt.savefig(filename)


def analyze_commute_times() -> None:
    """
    TODO: provide descriptive statistics and departure recommendation times based on discovered patterns.
    Work in progress! Lots to refine here.

    :return: empty, runs on --notify
    """
    # Read in the CSV
    df = pd.read_csv(CSV_FILE, header=None)
    df.columns = ["timestamp", "day", "home_to_work", "work_to_home"]

    # Data formatting
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["time_only"] = df["timestamp"].dt.time
    df["home_to_work"] = df["home_to_work"] / 3600
    df["work_to_home"] = df["work_to_home"] / 3600
    df["time_of_day"] = df["time_only"].apply(lambda t: datetime.combine(datetime(2000, 1, 1), t))

    # Save graphs
    # plot_commute_times(df, "home_to_work", "Home to Work",
    #                    f"home_to_work-{datetime.now().strftime('%B-%d-%Y').lower()}.jpeg")
    # plot_commute_times(df, "work_to_home", "Work to Home",
    #                    f"work_to_home-{datetime.now().strftime('%B-%d-%Y').lower()}.jpeg")


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
