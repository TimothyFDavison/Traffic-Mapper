import os

import googlemaps
from dotenv import load_dotenv

from smtp import send_sms_via_email


# Configure environment
load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(key=API_KEY)

if __name__ == '__main__':
    # Retrieve locations from env variables, compute drive time
    origin = os.getenv("WORK_ADDRESS")
    destination = os.getenv("HOME_ADDRESS")
    directions_result = gmaps.directions(origin, destination, mode="driving", departure_time="now")
    duration = directions_result[0]['legs'][0]['duration']['text']
    print(f"Driving time from A to B: {duration}")

    # Notify myself via text
    send_sms_via_email(
        number=os.getenv("PHONE_NUMBER"),
        carrier_gateway=os.getenv("CARRIER_GATEWAY"),
        message=f"Traffic estimate is {duration}",
        sender_email=os.getenv("EMAIL"),
        sender_password=os.getenv("GOOGLE_TOKEN")
    )
