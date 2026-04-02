"""Shared rate limiter instance.

Defined here (not in main.py) to avoid circular imports: routes need to
import the limiter, and main.py imports routers from routes.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
