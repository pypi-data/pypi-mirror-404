"""
LunchMoney App
"""

from lunchmoney.app import LunchMoneyApp

def test_init_app():
    """
    Very Simple Instantiation Test
    """
    app = LunchMoneyApp()
    assert app is not None