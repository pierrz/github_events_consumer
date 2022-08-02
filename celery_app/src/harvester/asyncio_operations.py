"""
Module dedicated to all Asyncio functions
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd
from config import harvester_config
from src.harvester.errors import EmptyResults, GenericError
from src.harvester.utils import get_session_data


def download(func):
    """
    Async loop to download a list of urls
    :param func: the function actually cleaning the parsed data
    :return: the retrieved data as an array
    """

    async def get(url, auth, **kwargs):
        try:
            if auth:
                data = await get_session_data(url, auth=auth)
            else:
                data = await get_session_data(url)
            return await func(data, **kwargs)

        except TypeError as e:
            EmptyResults(e)
        except Exception as e:
            GenericError(e)

    async def inner(
        urls: Iterable[str], auth: bool = True, **kwargs
    ) -> List[Tuple[str, bytes]]:
        try:
            return await asyncio.gather(*[get(url, auth, **kwargs) for url in urls])
        except TypeError as e:
            EmptyResults(e)
        except Exception as e:
            GenericError(e)

    return inner


@download
async def download_test(data, auth: bool = False) -> Iterable[Dict]:
    """
    For testing purpose (passthrough)
    :param data: the received data
    :return: the received data
    """

    return data


@download
async def download_github_events(
    data, filtered: bool = True, output: str = None
) -> Iterable[Dict]:
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
        df = raw_df[mask]
    else:
        df = raw_df

    if output == "df":
        return df
    return df.to_dict("records")


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
    Write data into JSON files with a trimmed timestamp (date-hour-minute only).
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
