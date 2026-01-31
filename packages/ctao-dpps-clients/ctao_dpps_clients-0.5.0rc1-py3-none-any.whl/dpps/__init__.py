"""
CTAO Data Processing and Preservation System python clients.

This is at the moment a pure meta-package pinning to specific
versions of the python client libraries of the DPPS subsystems.
"""

from bdms import __version__ as bdms_version
from rucio.version import version_string as get_rucio_version
from wms import __version__ as wms_version

from ._version import __version__

VERSION_INFO = {
    "dpps": __version__,
    "bdms": bdms_version,
    "wms": wms_version,
    "rucio": get_rucio_version(),
}

__all__ = [
    "__version__",
    "VERSION_INFO",
]
