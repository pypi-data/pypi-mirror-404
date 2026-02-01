"""
afflib - Arcaea chart file library

Package for handling aff files, the chart file format
used by the music game *Arcaea*.
"""

from .afflib import \
    Event, Note, Tap, Hold, Easing, ArcEasing, \
    Arc, Timing, Camera, SceneControl, \
    TimingGroup, Chart, set_precision, get_precision

__version__ = "0.0.1"
__author__ = "chitake"
__license__ = "CC0 1.0 Universal (CC0 1.0) Public Domain Dedication"

__all__ = [
    "Event", "Note", "Tap", "Hold", "Easing",
    "ArcEasing", "Arc", "Timing", "Camera",
    "SceneControl", "TimingGroup", "Chart",
    "set_precision", "get_precision"
]

set_precision(2)