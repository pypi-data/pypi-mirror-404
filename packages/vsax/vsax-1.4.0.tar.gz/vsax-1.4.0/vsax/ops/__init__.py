"""VSA operation sets."""

from vsax.ops.binary import BinaryOperations
from vsax.ops.fhrr import FHRROperations
from vsax.ops.map import MAPOperations
from vsax.ops.quaternion import QuaternionOperations

__all__ = [
    "FHRROperations",
    "MAPOperations",
    "BinaryOperations",
    "QuaternionOperations",
]
