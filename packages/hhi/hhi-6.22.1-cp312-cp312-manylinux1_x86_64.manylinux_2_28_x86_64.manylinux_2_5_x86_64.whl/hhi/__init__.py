"""hhi - HHI photonics PDK"""

from gdsfactory.config import CONF

from hhi import cells, config
from hhi.pdk import PDK
from hhi.tech import (
    LAYER,
    LAYER_STACK,
    LAYER_VIEWS,
    constants,
    cross_sections,
)

CONF.max_cellname_length = 32
__all__ = (
    "cells",
    "config",
    "PDK",
    "LAYER",
    "LAYER_VIEWS",
    "LAYER_STACK",
    "cross_sections",
    "constants",
)
__version__ = "6.22.1"
