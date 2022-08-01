"""
Module dedicated to all Asyncio functions
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import aiohttp
import pandas as pd
from config import harvester_config


async def get_session(url):

    print(f"Start downloading {url}")
    async with aiohttp.ClientSession() as session:
        resp = await session.get(url)
        data = await resp.json()
    print(f"Done downloading {url}")
    return data


def download_aio(func):
    """
    Async loop to download a list of urls
    :param func: the function actually cleaning the parsed data
    :return: the retrieved data as an array
    """

    async def fetch(url):
        data = await get_session(url)
        return await func(data)

    async def inner(urls: Iterable[str], **kwargs) -> List[Tuple[str, bytes]]:
        return await asyncio.gather(*[fetch(url) for url in urls])

    return inner


@download_aio
async def download_test(data) -> Iterable[Dict]:
    """
    For testing purpose (passthrough)
    :param data: the received data
    :return: the received data
    """

    return data


@download_aio
async def download_github_events(data, filtered: bool = True, output: str = "json") -> Iterable[Dict]:
    """
    Handles downloads from the GitHub Events API
    :param data: the received data
    :param filtered: allow for production data cleaning (enabled by default)
    :param output: how the data is exported (json array per default)
    :return: the filtered data
    """

    raw_df = pd.DataFrame(data)
    if filtered:
        mask = raw_df["type"].isin(harvester_config.EVENTS)
        df = raw_df[mask].to_dict("records")
    else:
        df = raw_df.to_dict("records")

    if output == "df":
        return df
    return df.to_dict("records")


# async def download_aio(urls: Iterable[str]) -> List[Tuple[str, bytes]]:
#     """
#     Async loop to download a list of urls
#     :param urls: the list of urls to download
#     :return: the retrieved data as an array
#     """
#     return await asyncio.gather(*[download_github_events(url) for url in urls])
#
#
# async def download_aio_test(urls: Iterable[str]) -> List[Tuple[str, bytes]]:
#     """
#     Async loop to download a list of urls
#     :param urls: the list of urls to download
#     :return: the retrieved data as an array
#     """
#     return await asyncio.gather(*[download_test(url) for url in urls])


async def write(
    idx: int, page: Dict, timestamp: str, output_dir: Path = None, path: Path = None
):
    """

    :param idx: page position
    :param page: page data
    :param output_dir: directory where to save the files
    :param timestamp: timestamp string for this batch
    :param path: for testing purpose, used to bypass the file naming pattern
    :return: write the file
    """
    print(f"Start writing page {idx}")
    if path is None:
        path = Path(output_dir, f"{timestamp}_page-{idx}.json")
    with open(path, "w", encoding="utf8") as output_file:
        json.dump(page, output_file, indent=4)
    print(f"Done writing page {idx}")


async def write_aio(data: Iterable[Dict], output_dir: Path):
    """
    Write data into JSON files.
    :param data: array of dictionaries
    :param output_dir: the directory where the files will be written
    :return: does its thing
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    await asyncio.gather(
        *[
            write(idx, page, timestamp, output_dir)
            for idx, page in enumerate(data, start=1)
        ]
    )
