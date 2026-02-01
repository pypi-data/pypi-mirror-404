# Import the main core function for the first version
from .core.sound_up import sound_up
from .core.sound_down import sound_down

# Import utility functions for direct access and testing
from .utils.generate_chirp import generate_chirp
from .utils.write_wav_file import write_wav_file

# Official stable release version
__version__ = "1.0.0"

# Defining available exports
__all__ = [
    "sound_up",
    "sound_down",
    "generate_chirp",
    "write_wav_file",
]