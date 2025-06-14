import os

import googlemaps
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(key=API_KEY)

"""
directions_result = gmaps.directions(
    origin,
    destination,
    mode="driving",
    departure_time=your_future_time,
    traffic_model="best_guess"  # options: "best_guess", "pessimistic", "optimistic"
)
"""
origin = os.getenv("WORK_ADDRESS")
destination = os.getenv("HOME_ADDRESS")
directions_result = gmaps.directions(origin, destination, mode="driving", departure_time="now")
duration = directions_result[0]['legs'][0]['duration']['text']
print(f"Driving time from A to B: {duration}")


import smtplib
from email.message import EmailMessage

def send_sms_via_email(number, carrier_gateway, message, sender_email, sender_password):
    to_number = f"{number}@{carrier_gateway}"

    msg = EmailMessage()
    msg.set_content(message)
    msg["Subject"] = ""
    msg["From"] = sender_email
    msg["To"] = to_number

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)

# Example usage
send_sms_via_email(
    number=os.getenv("PHONE_NUMBER"),
    carrier_gateway="vtext.com",
    message=f"Traffic estimate is {duration}",
    sender_email="timothyfdavison@gmail.com",
    sender_password=os.getenv("GOOGLE_MAPS_TOKEN")
)