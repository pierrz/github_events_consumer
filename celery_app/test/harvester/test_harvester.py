"""
Harvester tests
"""
import os
import shutil
from pathlib import Path

import pandas as pd
import pytest
from config import harvester_config
from src.harvester.asyncio_operations import (download_github_events,
                                              download_test, write, write_aio)
from src.harvester.utils import get_events_urls, get_session_data
from src.utils.json_utils import load_json  # pylint: disable=E0611


@pytest.mark.asyncio
async def test_download_sample(dog_sample_urls):
    """
    Tests the download function onto a basic url
    :return: does its thing
    """

    response = await get_session_data(
        dog_sample_urls["test"], auth=False, mode="response"
    )
    async with response:
        data = await response.json()
        assert response.status == 200
        assert data["message"].startswith(dog_sample_urls["result-url-prefix"])
        assert data["status"] == "success"


@pytest.mark.asyncio
async def test_write_data_to_file(json_sample_dict):
    """
    Tests the write function
    :return: does its thing
    """

    if not harvester_config.DATA_DIR.exists():
        os.mkdir(harvester_config.DATA_DIR)

    filepath = Path(harvester_config.DATA_DIR, "write-test.json")
    await write(11, json_sample_dict, "1984-12-31T07:59", path=filepath)

    assert filepath.exists()
    assert json_sample_dict == load_json(filepath)
    os.remove(filepath)


@pytest.mark.asyncio
async def test_asyncio_write_loop(json_array_dict):
    """
    Tests the asyncio loop write function
    :return: does its thing
    """

    test_output_dir = Path(harvester_config.DATA_DIR, "test")
    os.mkdir(test_output_dir)
    await write_aio(json_array_dict, test_output_dir)

    assert len(list(os.scandir(test_output_dir))) == len(json_array_dict)
    shutil.rmtree(test_output_dir)


@pytest.mark.asyncio
async def test_asyncio_download_loop(dog_sample_urls):
    """
    Tests the asyncio loop download function
    :return: does its thing
    :return:
    """

    size = 3
    test_urls = [dog_sample_urls["test"]] * size
    results = await download_test(test_urls)
    # results = await asyncio.run(download_test(test_urls))

    assert len(results) == size


@pytest.mark.asyncio
async def test_asyncio_download_github_events_unfiltered_records():
    """
    Tests the asyncio loop download function
    :return: does its thing
    :return:
    """

    event_urls = await get_events_urls()
    unfiltered_json_data = await download_github_events(event_urls, filtered=False)

    array = unfiltered_json_data.pop(0)
    for idx, part in enumerate(unfiltered_json_data):
        array += part

    assert len(array) == len(event_urls) * harvester_config.PER_PAGE


@pytest.mark.asyncio
async def test_asyncio_download_github_events_filtered_df():
    """
    Tests the asyncio loop download function
    :return: does its thing
    :return:
    """

    event_urls = await get_events_urls()
    df_list = await download_github_events(event_urls, output="df")
    grouped_df = (
        pd.concat(df_list).groupby(["type"]).sum().rename(columns={"public": "count"})
    )

    try:
        assert sorted(grouped_df.index.to_list()) == harvester_config.EVENTS

    # sometimes 1 event type is missing from the tested batch
    except AssertionError:
        for event in harvester_config.EVENTS:
            assert event in harvester_config.EVENTS

    # should always have at least 1 match from the required events
    is_valid = (grouped_df["count"] > 0).unique()[0]
    assert is_valid

    shutil.rmtree(harvester_config.DATA_DIR)
