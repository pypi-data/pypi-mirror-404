# sboon_ai_tools/__init__.py
def _get_version():
    from importlib.metadata import version, PackageNotFoundError
    try:
        return version("sboon_ai_tools")
    except PackageNotFoundError:
        return "unknown [0.1.1]"

__version__ = _get_version()

del _get_version
#-------------------------------------------------------------------------------------
# การให้เรียกคลาสได้โดยตรง (Flatten)
from .h5_manager import H5VirtualDrive
from .audio_utils import processor
from .datasets import load_sample_data

# กำหนดสิ่งที่จะถูก export เมื่อใช้คำสั่ง: from sboon_studio import *
__all__ = [
    "H5VirtualDrive",
    "processor",
    "load_sample_data"
]