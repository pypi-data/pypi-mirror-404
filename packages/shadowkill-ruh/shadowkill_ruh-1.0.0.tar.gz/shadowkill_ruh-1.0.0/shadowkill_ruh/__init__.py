"""
ShadowKill - Audio-triggered panic system for instant browser closing.

A discreet desktop guardian that listens for a double-knock on your desk
and instantly closes all browser tabs while opening a professional spreadsheet.
"""

__version__ = "1.0.0"
__author__ = "Rushan Ul Haque"
__email__ = "your.email@example.com"  # Update this

from .core import BossSensor

__all__ = ["BossSensor"]
