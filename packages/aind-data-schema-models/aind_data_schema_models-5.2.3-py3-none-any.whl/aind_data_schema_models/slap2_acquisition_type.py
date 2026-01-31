"""Stimulus modalities"""

from enum import Enum


class Slap2AcquisitionType(str, Enum):
    """Stimulus modalities"""

    INTEGRATION = "integration"
    RASTER = "raster"
