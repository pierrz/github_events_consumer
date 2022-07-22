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


def download(func):
    """
    Decorator function meant to download URLs
    :param func: the function used along this decorator
    :return: the downloaded data
    """

    async def inner(url):
        print(f"Start downloading {url}")
        async with aiohttp.ClientSession() as session:
            resp = await session.get(url)
            data = await resp.json()
        print(f"Done downloading {url}")
        return await func(data)

    return inner


@download
async def download_test(data):
    """
    For testing purpose (passthrough)
    :param data: the received data
    :return: the received data
    """
    return data


@download
async def download_github_events(data):
    """
    Handles downloads from the Marvel API
    :param data: the received data
    :return: the filtered data
    """

    df = pd.DataFrame(data)
    mask = df["type"].isin(["WatchEvent", "PullRequestEvent", "IssuesEvent"])
    required_data = df[mask].to_dict("records")
    return required_data


# TODO: create a decorator for the 2 following functions (same loop but different download 'def')
async def download_aio(urls: Iterable[str]) -> List[Tuple[str, bytes]]:
    """
    Async loop to download a list of urls
    :param urls: the list of urls to download
    :return: the retrieved data as an array
    """
    return await asyncio.gather(*[download_github_events(url) for url in urls])


async def download_aio_test(urls: Iterable[str]) -> List[Tuple[str, bytes]]:
    """
    Async loop to download a list of urls
    :param urls: the list of urls to download
    :return: the retrieved data as an array
    """
    return await asyncio.gather(*[download_test(url) for url in urls])


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
