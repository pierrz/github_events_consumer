"""
Module containing core functions
"""

import re

import requests
from config import harvester_config


def get_events_urls():

    base_url = f"https://api.github.com/events?per_page={harvester_config.PER_PAGE}"
    response = requests.get(base_url)
    links = response.headers["Link"].split(",")

    for link in links:
        if "last" in link:
            link_match = re.search(" <.*>", link)
            last_page = int(link_match.group()[-2])
            break

    urls = []

    for page in list(range(1, last_page + 1)):
        url = f"{base_url}&page={page}"
        urls.append(url)

    return urls
