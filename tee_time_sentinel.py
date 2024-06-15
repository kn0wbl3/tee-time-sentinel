
# import requests
import os
from bs4 import BeautifulSoup
# import datetime as dt
# import csv
# import time
import logging
import logging.config
import re

logging.config.fileConfig('config/logging.conf')
logger = logging.getLogger(__name__)

BASE_URL = "https://westchestercountyph.ezlinksgolf.com/"
LOCAL_HOST = "http://127.0.0.1:5000"
DEBUG_MODE = os.getenv("DEBUG_MODE")
GOLF_USERNAME = os.getenv("GOLF_USERNAME")
GOLF_PASSWORD = os.getenv("GOLF_PASSWORD")
# OIL_FILE = "data/oil_levels.csv"

"""
TODOs
- figure out logging in
- email me all tee times
- keep track of already found tee times
- only update me when new tee times become available
- now we need a way to have this run for multiple searches
- figure out way to communicate with app from texting
    - text new search, kicks off new sentinel, gets emailed with new tee times
"""

def main(debug_mode):
    """
    grab the data from westchester golf (WG)
        log into WG
        get data from dashboard
    catalog data and date
    email me all tee times
    """
    data = {}
    base_url = get_base_url(debug_mode)
    soup = log_into_website_and_grab_data(base_url, GOLF_USERNAME, GOLF_PASSWORD)

    tee_times = get_tee_times_from_soup(soup)

    as_of_date, num_of_players = get_date_and_players_from_soup(soup)

    data.update({
        "tee_times": tee_times,
        "as_of_date": as_of_date,
        "players": num_of_players
    })

    send_email(data)


def get_base_url(debug_mode):
    """
    when debugging, we want to go to localhost for webpage requests.
    otherwise, go to the interwebs
    """
    return LOCAL_HOST if debug_mode else BASE_URL


def log_into_website_and_grab_data(base_url, username, password):
    # Fill in your details here to be posted to the login form.
    return BeautifulSoup(open("tests/webpage.html"), "html.parser")
    payload = {
        "email_check": username,
        "password_check": password,
        "cmdLogin": "Login"
    }

    # Use 'with' to ensure the session context is closed after use.
    with requests.Session() as s:
        p = s.post(f"{base_url}/login", data=payload)
        page = s.get(f"{base_url}/user-home")
    
    soup = BeautifulSoup(page.content, "html.parser")
    return soup


def get_tee_times_from_soup(soup):
    tee_times = []
    
    tee_time_block = soup.find_all("ul", class_="tee-time-block")[0]
    tee_time_data = [x.text.strip() for x in tee_time_block]

    for tee_time in tee_time_data:
        clean = {}
        if not tee_time:
            continue
        clean_data = tee_time.split("\n")
        for item in clean_data:
            if not item:
                continue
            elif re.search("\w+\sGolf Course", item):
                clean.update({"course": item})
            elif re.search("\d:\d\d\s(A|P)M", item):
                clean.update({"time": item})
            elif re.search("\$\d{2}\.\d{2}", item):
                clean.update({"price": item})
            elif re.search("\d–\d\sPlayers", item):
                clean.update({"players": item})
        tee_times.append(clean)
    return tee_times


def get_date_and_players_from_soup(soup):
    # first we get the raw data from the soup
    raw_date_and_players = bird_soup(
        soup,
        (
            ("div", "col-xs-12 col-sm-9 content top-menu xs-nopadding-x"),
            ("nav", "top-nav col-xs-12"),
            ("div", "search-result-data col-sm-7 col-xs-12 ng-scope"),
            ("strong", None)
        )
    )

    # then we clean the raw data
    return re.split("\s\/\s", raw_date_and_players)


def bird_soup(soup, paths):
    """
    cheeky function that grabs the data you want from a nested soup.
    Nested soup... bird soup, get itt???
    """
    head_position = soup
    for item, path in paths:
        if not path:
            head_position = head_position.find(item)    
        else:
            head_position = head_position.find(item, class_=path)
    return head_position.text


def send_email(data):
    logger.warning(f"data: {data}")


if __name__ == "__main__":
    main(DEBUG_MODE)