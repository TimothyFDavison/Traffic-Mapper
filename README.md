# Traffic-Mapper

A quick script to familiarize myself with the Google Maps API, as well as to brush up on how to 
send emails and text programmatically. When run, `main.py` will estimate the driving time between my office and my home. 

I'm exploring tracking commute estimates longitudinally to minimize my overall drive time, or to provide myself 
with ad-hoc notifications of when traffic is worse than usual. For example, if there is an accident on a nearby highway,
I could continue working at the office until traffic returns to normal levels. Looking at setting the script to run 
autonomously at specific times or intervals and notify me under certain conditions. 

## Usage
This script was written in Python 3.12, and can be run via `uv`:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
uv run main.py
```

Importantly, `main.py` expects the following environment variables to be set or managed in a 
`.env` file:
```bash
export GOOGLE_MAPS_API_KEY=<...>
export GOOGLE_TOKEN=<...>
export HOME_ADDRESS=<...>
export WORK_ADDRESS=<...>
export PHONE_NUMBER=<...>
export EMAIL=<...>
CSV_FILE=<...>
LOGFILE=<...>
```

## API references
Dropping these here for my own benefit, to remind myself of how to leverage Google Maps and SMTP.
```python
import googlemaps

gmaps = googlemaps.Client(key=<API_KEY>)
directions_result = gmaps.directions(
    <origin>,
    <destination>,
    mode="driving",
    departure_time=<some_future_time>,
    traffic_model="best_guess"  # options include "best_guess", "pessimistic", "optimistic"
)
```
```python
import smtplib
from email.message import EmailMessage

to_number = f"<phone_number>@<carrier_gateway>"
msg = EmailMessage()
msg.set_content(<message>)
msg["Subject"] = ""
msg["From"] = <sender_email>
msg["To"] = <to_number>

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(<sender_email>, <sender_password>)
    server.send_message(msg)
```

## Longitudinal Analysis
I created an additional entitled `longitudinal_analysis.py` to log commute times to/from work at regular intervals each 
work day. I'm running these in a cron job from my laptop using,
```cron
*/30 * * * 1-5  /bin/bash -c 'cd <directory> && <directory>/.local/bin/uv run <directory>/longitudinal_study.py'
0 16 * * 5 /bin/bash -c 'cd  <directory> &&  <directory>/.local/bin/uv run  <directory>/longitudinal_study.py --notify'
```
Every 30 minutes, the script will record the commute times and save it to a CSV specified in my `.env` file. Then,
on Fridays at 4 PM, the script will send me a summary of the commute time fluctuation throughout the week 
alongside recommendations to minimize my time spent in the car. 
