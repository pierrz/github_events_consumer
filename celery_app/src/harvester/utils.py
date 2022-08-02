"""
Module containing core functions
"""

import re

import aiohttp
# import requests
from config import harvester_config

# async def get_session(url):
#
#     print(f"Start downloading {url}")
#     async with aiohttp.ClientSession() as session:
#         resp = await session.get(url)
#         data = await resp.json()


async def get_session_data(url):

    print(f"Start downloading {url}")
    async with aiohttp.ClientSession() as session:
        resp = await session.get(url)
        data = await resp.json()
    print(f"Done downloading {url}")
    return data


async def get_events_urls():

    base_url = f"https://api.github.com/events?per_page={harvester_config.PER_PAGE}"
    # response = requests.get(base_url)
    async with aiohttp.ClientSession() as session:
        response = await session.get(base_url)

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
    print(urls)

    return urls
