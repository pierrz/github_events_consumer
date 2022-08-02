"""
Module containing core functions
"""

import aiohttp
from config import harvester_config
from src.harvester.errors import APILimitError, GenericError


async def get_session_data(url, auth: bool = True, mode: str = None):

    print(f"Start downloading {url}")
    try:
        async with aiohttp.ClientSession() as client:

            if auth:
                params = {
                    "Authorization": f"token {harvester_config.GITHUB_TOKEN}",
                    "Accept": "application/vnd.github+json",
                }
                response = await client.get(url, headers=params)

            else:
                response = await client.get(url)
            print(f"Done downloading {url}")

            if mode == "response":
                return response
            return await response.json()

    except KeyError as e:
        APILimitError(e)
    except Exception as e:
        GenericError(e)


async def get_events_urls():

    base_url = f"https://api.github.com/events?per_page={harvester_config.PER_PAGE}"
    response = await get_session_data(base_url, mode="response")

    try:
        last_page = int(str(response.links["last"]["url"])[-1])
        urls = []
        for page in list(range(1, last_page + 1)):
            url = f"{base_url}&page={page}"
            urls.append(url)

        return urls

    except KeyError as e:
        APILimitError(e)
    except Exception as e:
        GenericError(e)
