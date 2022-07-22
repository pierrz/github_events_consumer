"""
Harvester tests
"""

import os
import shutil
from pathlib import Path

import pytest
from config import harvester_config
from src.harvester.asyncio_operations import (download_aio_test, download_test,
                                              write, write_aio)
from src.utils.json_utils import load_json  # pylint: disable=E0611


@pytest.mark.asyncio
async def test_download_sample(dog_sample_url):
    """
    Tests the download function onto a basic url
    :return: does its thing
    """

    response = await download_test(dog_sample_url)

    assert response["message"].startswith("https://images.dog.ceo/breeds")
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
async def test_asyncio_download_loop(dog_sample_url):
    """
    Tests the asyncio loop download function
    :return: does its thing
    :return:
    """

    size = 3
    test_urls = [dog_sample_url] * size
    results = await download_aio_test(test_urls)

    assert len(results) == size
