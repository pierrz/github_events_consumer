"""
Configuration module
"""

from pathlib import Path

from pydantic import BaseSettings

# TODO: move to shared module (update dockerfile and some imports)
diagrams_dir = Path("templates", "diagrams")


class Config(BaseSettings):
    """
    Config class.
    """

    LOCAL_DEV = True


app_config = Config()
