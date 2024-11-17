import requests, time, json
from fetcher import fetch_followers
from sender import mail_sender
from datetime import datetime
import pytz

with open("config.json", "r") as config_file:
    config = json.load(config_file)

TIMEZONE = pytz.timezone(config["timezone"])
SPOTIFY_USER_ID = config["spotify_configs"]["user_id_to_track"]
SPOTIFY_CLIENT_ID = config["spotify_configs"]["spotify_client_id"]
SPOTIFY_CLIENT_SECRET = config["spotify_configs"]["spotify_client_secret"]

fetcher = fetch_followers.FetchFollowers(SPOTIFY_USER_ID)

is_send_gmail = config["send_gmail"]
if is_send_gmail:
    gmail_sender_config = config["gmail_sender"]
    gmail_sender = mail_sender.GmailSender(gmail_sender_config)

def get_token():
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(token_url, data=payload, headers=headers)
    return response.json()["access_token"]

def monitor_error(error):
    with open("./logs/error.log", "a") as error_log:
        error_log.write(f"{datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} An error occurred: {str(error)}\n")
        if is_send_gmail:
            gmail_sender.send_message("Spotify - Error", f"An error occurred: {str(error)}")

SPOTIFY_ACCESS_TOKEN = get_token()

url = "https://api.spotify.com/v1/users/{user_id}"

headers = {
    "Authorization": f"Bearer {SPOTIFY_ACCESS_TOKEN}"
}

init_response = requests.get(url.format(user_id=SPOTIFY_USER_ID), headers=headers)
total_followers = init_response.json()["followers"]["total"]

time.sleep(.5)

with open("./logs/error.log", "a") as error_log:
    error_log.write(f"{datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} App started\n")

while True:
    try:
        response = requests.get(url.format(user_id=SPOTIFY_USER_ID), headers=headers)
        temp = response.json()["followers"]["total"]
    except KeyError as expired_token:
        with open("./logs/error.log", "a") as error_log:
            error_log.write(f"{datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} Token expired - getting new token\n")
        SPOTIFY_ACCESS_TOKEN = get_token()
        headers["Authorization"] = f"Bearer {SPOTIFY_ACCESS_TOKEN}"
        continue
    except json.decoder.JSONDecodeError as e:
        with open("./logs/error.log", "a") as error_log:
            error_log.write(f"{datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} API limit reached - retrying in 60s\n")
        time.sleep(60)
        continue
    except Exception as e:
        monitor_error(e)
        continue

    try:
        if temp != total_followers:
            print(f"Change in followers: {temp - total_followers}")
            new_followers, lost_followers = fetcher.compare_followers()

            if new_followers or lost_followers:
                message = ""
                if new_followers:
                    message += f"New followers: {', '.join(new_followers)}\n"
                if lost_followers:
                    message += f"Unfollowers: {', '.join(lost_followers)}\n"

                if is_send_gmail:
                    print(f"Sending email: {message}")  # Burada e-posta gönderimi öncesi print eklendi
                    gmail_sender.send_message("Spotify - Followed and Unfollowed", message)

            total_followers = temp

    except Exception as e:
        monitor_error(e)

    time.sleep(.9)  # wait to avoid spamming the API
