"""
LunchMoney App
"""

from lunchmoney.app import LunchMoneyApp

def test_init_app():
    """
    Very Simple Instantiation Test
    """
    app = LunchMoneyApp(access_token="xxxxxxxxx")
    assert app is not None
