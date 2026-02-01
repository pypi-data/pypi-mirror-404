from soundgen.utils.generate_chirp import generate_chirp
from soundgen.utils.write_wav_file import write_wav_file

def sound_up(filename: str, start_freq: float | int, end_freq: float | int, duration: float | int) -> None:
    """
    Generates a sound with increasing frequency.
    """
    if start_freq >= end_freq:
        raise ValueError("start_freq must be less than end_freq for sound_up")
    
    signal = generate_chirp(start_freq, end_freq, duration)
    write_wav_file(filename, signal)