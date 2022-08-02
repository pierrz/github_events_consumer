"""Module gathering all error classes"""


class APILimitError(Exception):
    """Specific to the API call, should show the missing key from the received data"""
    def __init__(self, e):
        print(f"/!\\ The Github Events API limit is probably reached <- '{e.__doc__}'")


class EmptyResults(Exception):
    """Usually triggered by TypeError"""
    def __init__(self, e):
        print(f"/!\\ Empty results ('{e.__doc__}' <- NoneType) probably due to reaching the Github Events API limit.")
