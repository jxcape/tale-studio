"""BridgeMode value object for AVA Framework."""
from enum import Enum


class BridgeMode(Enum):
    """Translation strategy modes for Bridge layer."""

    INTUITIVE = "intuitive"  # Direct emotional mapping
    SYMBOLIC = "symbolic"    # Metaphorical translation (future)
    SENSORY = "sensory"      # Synesthetic translation (future)
