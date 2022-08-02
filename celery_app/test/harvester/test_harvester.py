"""
Harvester tests
"""

import asyncio
import os
import shutil
from pathlib import Path

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

    response = await get_session_data(dog_sample_urls["test"])
    assert response["message"].startswith(dog_sample_urls["result-url-prefix"])
    assert response["status"] == "success"


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

    assert len(results) == size


@pytest.mark.asyncio
async def test_asyncio_download_github_events():
    """
    Tests the asyncio loop download function
    :return: does its thing
    :return:
    """

    urls = await get_events_urls()

    # json_data_raw = await asyncio.run(download_github_events(urls, filtered=False))
    # json_data_raw = await asyncio.run(download_github_events(urls))
    async with await asyncio.run(download_github_events(urls), debug=True) as json_data_raw:
        assert await len(json_data_raw) == urls * harvester_config.PER_PAGE

    # json_data_filtered = asyncio.run(download_github_events(urls, output="df"))
    # sums = json_data_filtered.groupby(["type"]).sum()
    # is_valid = sums[sums["type"] > 0].unique()
    #
    # print(sums)
    # print(is_valid)
    #
    # assert sorted(sums.index.to_list()) == harvester_config.EVENTS
    # assert is_valid

    shutil.rmtree(harvester_config.DATA_DIR)
